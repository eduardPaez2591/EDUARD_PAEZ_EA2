import pandas as pd 
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / 'data_raw' / 'laptop_prices.csv'
DB_PATH = BASE_DIR / 'src' / 'db' / 'laptop_prices.db'

def create_database():
    # Create the SQLite database and the laptop_prices table
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists

    try:
        df = pd.read_csv(CSV_PATH)
        conn = sqlite3.connect(DB_PATH)
        df.to_sql('laptops', conn, if_exists='replace', index=False)
        conn.close()
        print(f"✓ Base de datos creada en {DB_PATH}")
        print(f"✓ {len(df)} registros importados")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    create_database()