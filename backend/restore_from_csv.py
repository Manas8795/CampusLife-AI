import csv
import json
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "campuslife.db"
BACKUP_DIR = ROOT_DIR / "backend" / "database_backup_csv"
JSON_BACKUP = BACKUP_DIR / "campuslife_database_backup.json"

def restore_database():
    print(f"[Restore] Connecting to SQLite database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if JSON_BACKUP.exists():
        print(f"[Restore] Reading high-fidelity backup from {JSON_BACKUP}...")
        with open(JSON_BACKUP, "r", encoding="utf-8") as f:
            data = json.load(f)

        for table, rows in data.items():
            if not rows:
                continue
            cursor.execute(f"DELETE FROM {table};")
            cols = list(rows[0].keys())
            placeholders = ", ".join(["?"] * len(cols))
            col_names = ", ".join([f'"{c}"' for c in cols])
            sql = f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})"

            values = [tuple(r.get(c) for c in cols) for r in rows]
            cursor.executemany(sql, values)
            print(f"  -> Restored {table}: {len(rows)} records")

    else:
        print(f"[Restore] Reading from CSV files in {BACKUP_DIR}...")
        csv_files = list(BACKUP_DIR.glob("*.csv"))
        for csv_file in csv_files:
            table = csv_file.stem
            if table == "campuslife_database_backup":
                continue
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if not rows:
                    continue
                cursor.execute(f"DELETE FROM {table};")
                cols = list(rows[0].keys())
                placeholders = ", ".join(["?"] * len(cols))
                col_names = ", ".join([f'"{c}"' for c in cols])
                sql = f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})"
                values = [tuple(r.get(c) for c in cols) for r in rows]
                cursor.executemany(sql, values)
                print(f"  -> Restored {table}: {len(rows)} records from {csv_file.name}")

    conn.commit()
    conn.close()
    print("[Restore] All database records successfully restored from CSV backup!")

if __name__ == "__main__":
    restore_database()
