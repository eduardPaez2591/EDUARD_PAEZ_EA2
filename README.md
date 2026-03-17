# 📊 EA2. Proyecto Integrador — Preprocesamiento de Datos en Big Data

## Descripción

Este proyecto implementa un pipeline completo de **preprocesamiento y limpieza de datos** utilizando un dataset de precios de laptops. Simula un entorno de Big Data en la nube mediante PySpark/Pandas y automatiza el proceso con GitHub Actions.

## 🎯 Objetivo

- ✅ Validar y transformar datos crudos
- ✅ Eliminar duplicados y valores nulos
- ✅ Corregir tipos de datos
- ✅ Remover outliers
- ✅ Normalizar columnas
- ✅ Generar reportes de auditoría
- ✅ Automatizar con GitHub Actions

## 📁 Estructura del Proyecto

EDUARD_PAEZ_EA2/
├── .github/
│ └── workflows/
│ └── bigdata.yml
├── data_raw/
│ └── laptop_prices.csv
├── src/
│ ├── db/
│ │ └── ingestion.db
│ ├── static/
│ │ ├── auditoria/
│ │ │ └── cleaning_report.txt
│ │ └── xlsx/
│ │ └── cleaned_data.xlsx
│ ├── cleaning.py
│ ├── ingestion.py
│ └── utils.py
├── README.md
├── requirements.txt
└── setup.py

## ⚙️ Automatización con GitHub Actions

El workflow .github/workflows/bigdata.yml se ejecuta automáticamente cuando:
📤 Haces push a main o master
⏰ Diariamente a las 00:00 UTC
🖱️ Manualmente desde la pestaña "Actions"

Lo que hace el Workflow:
✅ Clona el repositorio
✅ Configura Python 3.10
✅ Instala dependencias
✅ Crea la base de datos
✅ Ejecuta el script de limpieza
✅ Genera archivos de salida
✅ Carga artefactos
✅ Muestra el reporte de auditoría

## 📊 Operaciones de Limpieza Realizadas

Operación Descripción
Eliminación de Duplicados Remove duplicate records based on all columns
Manejo de Valores Nulos Imputation using median (numeric) and mode (categorical)
Corrección de Tipos Convert columns to appropriate data types
Remoción de Outliers Remove values outside IQR bounds
Normalización Min-Max scaling for numeric columns

## 📋 Archivos de Salida

cleaned_data.xlsx
Contiene una muestra de 50 registros después de la limpieza
Incluye columnas normalizadas adicionales
Listo para análisis posteriores
cleaning_report.txt
Reporte detallado que incluye:
Timestamp de ejecución
Estadísticas antes y después
Número de registros eliminados
Operaciones realizadas
Valores nulos por columna
Tasa de retención
