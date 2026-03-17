import pandas as pd
import numpy as np
import sqlite3
import os
from datetime import datetime
from pathlib import Path

# Configuración de rutas
BASE_DIR = Path(__file__).parent.parent
DATA_RAW_PATH = BASE_DIR / 'data_raw' / 'laptop_prices.csv'
DB_PATH = BASE_DIR / 'src' / 'db' / 'ingestion.db'
OUTPUT_XLSX = BASE_DIR / 'src' / 'static' / 'xlsx' / 'cleaned_data.xlsx'
AUDIT_PATH = BASE_DIR / 'src' / 'static' / 'auditoria' / 'cleaning_report.txt'

# Crear directorios si no existen
OUTPUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)

class DataCleaner:
    def __init__(self):
        self.df = None
        self.df_clean = None
        self.audit_log = []
        self.stats_before = {}
        self.stats_after = {}
        
    def log_audit(self, message):
        """Registra eventos en el log de auditoría"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.audit_log.append(f"[{timestamp}] {message}")
        print(f"✓ {message}")
    
    def load_data(self):
        """Carga datos desde CSV"""
        try:
            self.df = pd.read_csv(DATA_RAW_PATH)
            self.log_audit(f"Datos cargados desde {DATA_RAW_PATH}")
            self.log_audit(f"Registros iniciales: {len(self.df)}")
            return True
        except Exception as e:
            self.log_audit(f"ERROR al cargar datos: {str(e)}")
            return False
    
    def exploratory_analysis(self, df, label="INICIAL"):
        """Realiza análisis exploratorio"""
        stats = {
            'label': label,
            'total_records': len(df),
            'total_columns': len(df.columns),
            'duplicates': df.duplicated().sum(),
            'null_values': df.isnull().sum().to_dict(),
            'data_types': df.dtypes.astype(str).to_dict(),
            'memory_usage': df.memory_usage(deep=True).sum() / 1024**2  # MB
        }
        return stats
    
    def clean_duplicates(self):
        """Elimina registros duplicados"""
        initial_count = len(self.df_clean)
        self.df_clean = self.df_clean.drop_duplicates()
        removed = initial_count - len(self.df_clean)
        self.log_audit(f"Duplicados eliminados: {removed}")
    
    def handle_missing_values(self):
        """Maneja valores nulos"""
        # Identifica columnas con valores nulos
        null_counts = self.df_clean.isnull().sum()
        null_cols = null_counts[null_counts > 0]
        
        if len(null_cols) > 0:
            self.log_audit(f"Columnas con valores nulos: {null_cols.to_dict()}")
            
            # Para columnas numéricas, usar mediana
            numeric_cols = self.df_clean.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if self.df_clean[col].isnull().sum() > 0:
                    median_val = self.df_clean[col].median()
                    self.df_clean[col].fillna(median_val, inplace=True)
                    self.log_audit(f"Nulos en '{col}' imputados con mediana: {median_val}")
            
            # Para columnas categóricas, usar moda
            categorical_cols = self.df_clean.select_dtypes(include=['object']).columns
            for col in categorical_cols:
                if self.df_clean[col].isnull().sum() > 0:
                    mode_val = self.df_clean[col].mode()[0] if len(self.df_clean[col].mode()) > 0 else 'Unknown'
                    self.df_clean[col].fillna(mode_val, inplace=True)
                    self.log_audit(f"Nulos en '{col}' imputados con moda: {mode_val}")
            
            # Elimina filas con demasiados nulos (>50% de columnas)
            threshold = len(self.df_clean.columns) * 0.5
            initial = len(self.df_clean)
            self.df_clean = self.df_clean.dropna(thresh=threshold)
            removed = initial - len(self.df_clean)
            if removed > 0:
                self.log_audit(f"Filas con >50% nulos eliminadas: {removed}")
    
    def fix_data_types(self):
        """Corrige tipos de datos"""
        try:
            # Conversión de columnas numéricas
            numeric_mappings = {
                'Ram': int,
                'Inches': float,
                'Weight': float,
                'Price_euros': float,
                'ScreenW': int,
                'ScreenH': int,
                'CPU_freq': float
            }
            
            for col, dtype in numeric_mappings.items():
                if col in self.df_clean.columns:
                    try:
                        self.df_clean[col] = pd.to_numeric(self.df_clean[col], errors='coerce')
                        self.df_clean[col] = self.df_clean[col].astype(dtype)
                    except Exception as e:
                        self.log_audit(f"Advertencia: No se pudo convertir '{col}' a {dtype}: {e}")
            
            self.log_audit("Tipos de datos corregidos correctamente")
        except Exception as e:
            self.log_audit(f"ERROR en corrección de tipos: {str(e)}")
    
    def remove_outliers(self):
        """Elimina outliers usando IQR"""
        numeric_cols = self.df_clean.select_dtypes(include=[np.number]).columns
        initial = len(self.df_clean)
        
        for col in numeric_cols:
            Q1 = self.df_clean[col].quantile(0.25)
            Q3 = self.df_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = len(self.df_clean[(self.df_clean[col] < lower_bound) | (self.df_clean[col] > upper_bound)])
            if outliers > 0:
                self.df_clean = self.df_clean[(self.df_clean[col] >= lower_bound) & (self.df_clean[col] <= upper_bound)]
                self.log_audit(f"Outliers eliminados en '{col}': {outliers}")
        
        removed = initial - len(self.df_clean)
        if removed > 0:
            self.log_audit(f"Total outliers eliminados: {removed}")
    
    def normalize_columns(self):
        """Normaliza columnas numéricas seleccionadas"""
        try:
            numeric_cols = ['Weight', 'Price_euros', 'Ram']
            for col in numeric_cols:
                if col in self.df_clean.columns:
                    min_val = self.df_clean[col].min()
                    max_val = self.df_clean[col].max()
                    if max_val > min_val:
                        self.df_clean[f'{col}_normalized'] = (self.df_clean[col] - min_val) / (max_val - min_val)
            
            self.log_audit("Normalización de columnas completada")
        except Exception as e:
            self.log_audit(f"Advertencia en normalización: {str(e)}")
    
    def clean(self):
        """Ejecuta pipeline completo de limpieza"""
        if not self.load_data():
            return False
        
        self.df_clean = self.df.copy()
        self.stats_before = self.exploratory_analysis(self.df, "ANTES")
        
        self.log_audit("=" * 50)
        self.log_audit("INICIANDO LIMPIEZA DE DATOS")
        self.log_audit("=" * 50)
        
        self.clean_duplicates()
        self.handle_missing_values()
        self.fix_data_types()
        self.remove_outliers()
        self.normalize_columns()
        
        self.stats_after = self.exploratory_analysis(self.df_clean, "DESPUÉS")
        
        self.log_audit("=" * 50)
        self.log_audit("LIMPIEZA COMPLETADA")
        self.log_audit("=" * 50)
        
        return True
    
    def save_cleaned_data(self):
        """Guarda datos limpios en Excel"""
        try:
            # Guarda muestra de 50 registros
            sample = self.df_clean.sample(min(50, len(self.df_clean)), random_state=42)
            sample.to_excel(OUTPUT_XLSX, index=False, sheet_name='Datos_Limpios')
            self.log_audit(f"Datos limpios guardados en {OUTPUT_XLSX}")
            return True
        except Exception as e:
            self.log_audit(f"ERROR al guardar Excel: {str(e)}")
            return False
    
    def save_audit_report(self):
        """Genera reporte de auditoría"""
        try:
            with open(AUDIT_PATH, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("REPORTE DE AUDITORÍA - LIMPIEZA DE DATOS\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Estadísticas antes
                f.write("ESTADÍSTICAS ANTES DE LIMPIEZA:\n")
                f.write("-" * 80 + "\n")
                f.write(f"Registros totales: {self.stats_before['total_records']}\n")
                f.write(f"Columnas: {self.stats_before['total_columns']}\n")
                f.write(f"Duplicados: {self.stats_before['duplicates']}\n")
                f.write(f"Uso de memoria: {self.stats_before['memory_usage']:.2f} MB\n\n")
                
                f.write("Valores nulos por columna:\n")
                for col, count in self.stats_before['null_values'].items():
                    if count > 0:
                        f.write(f"  - {col}: {count}\n")
                f.write("\n")
                
                # Estadísticas después
                f.write("ESTADÍSTICAS DESPUÉS DE LIMPIEZA:\n")
                f.write("-" * 80 + "\n")
                f.write(f"Registros totales: {self.stats_after['total_records']}\n")
                f.write(f"Columnas: {self.stats_after['total_columns']}\n")
                f.write(f"Duplicados: {self.stats_after['duplicates']}\n")
                f.write(f"Uso de memoria: {self.stats_after['memory_usage']:.2f} MB\n\n")
                
                # Comparativa
                f.write("COMPARATIVA:\n")
                f.write("-" * 80 + "\n")
                records_removed = self.stats_before['total_records'] - self.stats_after['total_records']
                f.write(f"Registros eliminados: {records_removed}\n")
                f.write(f"Tasa de retención: {(self.stats_after['total_records'] / self.stats_before['total_records'] * 100):.2f}%\n\n")
                
                # Log de operaciones
                f.write("LOG DE OPERACIONES:\n")
                f.write("-" * 80 + "\n")
                for log_entry in self.audit_log:
                    f.write(log_entry + "\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("FIN DEL REPORTE\n")
                f.write("=" * 80 + "\n")
            
            self.log_audit(f"Reporte de auditoría guardado en {AUDIT_PATH}")
            return True
        except Exception as e:
            self.log_audit(f"ERROR al guardar reporte: {str(e)}")
            return False
    
    def run(self):
        """Ejecuta el proceso completo"""
        if self.clean():
            self.save_cleaned_data()
            self.save_audit_report()
            print("\n✅ Proceso de limpieza completado exitosamente")
            return True
        else:
            print("\n❌ Error durante el proceso de limpieza")
            return False


if __name__ == '__main__':
    cleaner = DataCleaner()
    cleaner.run()

            
        