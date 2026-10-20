import csv
import json
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "campuslife.db"
BACKUP_DIR = ROOT_DIR / "backend" / "database_backup_csv"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
CONSOLIDATED_CSV = ROOT_DIR / "campuslife_database_backup.csv"
JSON_BACKUP = BACKUP_DIR / "campuslife_database_backup.json"

def export_database():
    print(f"[Backup] Connecting to SQLite database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row["name"] for row in cursor.fetchall()]
    print(f"[Backup] Found {len(tables)} tables: {', '.join(tables)}")

    full_export_data = {}
    master_rows = []

    for table in tables:
        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]

        # 1. Export individual CSV
        table_csv_path = BACKUP_DIR / f"{table}.csv"
        with open(table_csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(column_names)
            for row in rows:
                writer.writerow(list(row))

        # Store for JSON and consolidated CSV
        dict_rows = [dict(row) for row in rows]
        full_export_data[table] = dict_rows

        for row in dict_rows:
            row_id = row.get("id", "")
            created_at = row.get("created_at") or row.get("timestamp") or row.get("date") or ""
            master_rows.append({
                "table_name": table,
                "record_id": row_id,
                "data_json": json.dumps(row, default=str),
                "timestamp": str(created_at)
            })

        print(f"  -> Exported {table}: {len(rows)} rows to {table_csv_path.name}")

    # 2. Export Consolidated Master CSV
    with open(CONSOLIDATED_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["table_name", "record_id", "timestamp", "data_json"])
        writer.writeheader()
        writer.writerows(master_rows)
    print(f"[Backup] Successfully generated Consolidated Master CSV at: {CONSOLIDATED_CSV}")

    # Also place a copy inside BACKUP_DIR
    with open(BACKUP_DIR / "campuslife_database_backup.csv", mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["table_name", "record_id", "timestamp", "data_json"])
        writer.writeheader()
        writer.writerows(master_rows)

    # 3. Export Complete High-Fidelity JSON Backup
    with open(JSON_BACKUP, mode="w", encoding="utf-8") as f:
        json.dump(full_export_data, f, indent=2, default=str)
    print(f"[Backup] Successfully generated JSON Backup at: {JSON_BACKUP}")

    conn.close()
    return len(master_rows)

def clear_database_tables():
    print("\n[Clear] Clearing all user data records from database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tables to clear completely
    data_tables = [
        "tasks",
        "trips",
        "trip_activities",
        "expenses",
        "receipts",
        "budgets",
        "health_records",
        "wellness_recommendations",
        "study_plans",
        "study_materials",
        "voice_messages",
        "voice_conversations",
        "voice_calls",
        "productivity_records",
        "intelligence_insights",
        "intelligence_risks",
        "notifications"
    ]

    for table in data_tables:
        try:
            cursor.execute(f"DELETE FROM {table};")
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}';")
            print(f"  -> Cleared table: {table}")
        except sqlite3.OperationalError:
            pass

    # Reset student_states to clean baseline
    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_academic = json.dumps({
        "total_tasks": 0,
        "pending_tasks": 0,
        "overdue_tasks": 0,
        "productivity_risk": "LOW",
        "completion_rate": 1.0
    })
    clean_wellness = json.dumps({
        "avg_sleep_7d": 8.0,
        "avg_study_7d": 0.0,
        "stress_level": "LOW"
    })
    clean_financial = json.dumps({
        "budget_spent": 0.0,
        "budget_limit": 10000.0,
        "utilization_pct": 0.0,
        "days_runway": 30
    })
    clean_travel = json.dumps({
        "upcoming_trips_count": 0,
        "conflicts_count": 0
    })

    cursor.execute("""
        UPDATE student_states
        SET academic_summary = ?,
            wellness_summary = ?,
            financial_summary = ?,
            travel_summary = ?,
            compound_risk_level = 'LOW',
            compound_risk_score = 0.1,
            updated_at = ?
        WHERE user_id = 1;
    """, (clean_academic, clean_wellness, clean_financial, clean_travel, now_iso))

    conn.commit()
    conn.execute("VACUUM;")
    conn.close()
    print("[Clear] Database successfully cleared & vacuumed. Clean baseline established!\n")

if __name__ == "__main__":
    count = export_database()
    clear_database_tables()
    print(f"[Done] Total {count} records preserved in CSV backup. Database is completely clear and ready.")
