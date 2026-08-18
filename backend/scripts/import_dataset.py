import os
import sys
import time
import pandas as pd
import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DB = os.getenv("MYSQL_DB", "medical_device_prediction")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))

def get_connection(include_db=True):
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB if include_db else None,
        charset="utf8mb4",
        autocommit=False
    )

def create_database():
    print(f"Ensuring database '{MYSQL_DB}' exists...")
    conn = get_connection(include_db=False)
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    conn.commit()
    conn.close()
    print("Database verified.")

def create_dataset_tables():
    print("Creating dataset tables (manufacturers, devices, events) if not exist...")
    conn = get_connection(include_db=True)
    with conn.cursor() as cur:
        # 1. manufacturers
        cur.execute("""
        CREATE TABLE IF NOT EXISTS `manufacturers` (
            `id` VARCHAR(64) NOT NULL PRIMARY KEY,
            `name` VARCHAR(500) NULL,
            `parent_company` VARCHAR(500) NULL,
            `address` TEXT NULL,
            `representative` VARCHAR(500) NULL,
            `comment` TEXT NULL,
            `source` VARCHAR(255) NULL,
            `slug` VARCHAR(500) NULL,
            `created_at` VARCHAR(100) NULL,
            `updated_at` VARCHAR(100) NULL,
            INDEX `idx_mfr_name` (`name`(255))
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 2. devices
        cur.execute("""
        CREATE TABLE IF NOT EXISTS `devices` (
            `id` VARCHAR(64) NOT NULL PRIMARY KEY,
            `manufacturer_id` VARCHAR(64) NULL,
            `name` VARCHAR(500) NULL,
            `classification` VARCHAR(255) NULL,
            `code` VARCHAR(255) NULL,
            `description` TEXT NULL,
            `distributed_to` TEXT NULL,
            `implanted` VARCHAR(50) NULL,
            `number` VARCHAR(255) NULL,
            `quantity_in_commerce` DOUBLE NULL,
            `risk_class` VARCHAR(50) NULL,
            `slug` VARCHAR(500) NULL,
            `country` VARCHAR(50) NULL,
            `created_at` VARCHAR(100) NULL,
            `updated_at` VARCHAR(100) NULL,
            INDEX `idx_dev_mfr_id` (`manufacturer_id`),
            INDEX `idx_dev_classification` (`classification`(191)),
            INDEX `idx_dev_risk_class` (`risk_class`),
            INDEX `idx_dev_country` (`country`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 3. events
        cur.execute("""
        CREATE TABLE IF NOT EXISTS `events` (
            `id` VARCHAR(64) NOT NULL PRIMARY KEY,
            `device_id` VARCHAR(64) NULL,
            `type` VARCHAR(100) NULL,
            `status` VARCHAR(100) NULL,
            `country` VARCHAR(50) NULL,
            `action` TEXT NULL,
            `action_classification` VARCHAR(100) NULL,
            `action_level` VARCHAR(100) NULL,
            `action_summary` TEXT NULL,
            `determined_cause` TEXT NULL,
            `reason` TEXT NULL,
            `date` VARCHAR(100) NULL,
            `event_year` INT NULL,
            `event_month` INT NULL,
            `date_initiated_by_firm` VARCHAR(100) NULL,
            `date_posted` VARCHAR(100) NULL,
            `date_terminated` VARCHAR(100) NULL,
            `date_updated` VARCHAR(100) NULL,
            `created_at` VARCHAR(100) NULL,
            `updated_at` VARCHAR(100) NULL,
            INDEX `idx_evt_device_id` (`device_id`),
            INDEX `idx_evt_type` (`type`),
            INDEX `idx_evt_status` (`status`),
            INDEX `idx_evt_country` (`country`),
            INDEX `idx_evt_year` (`event_year`),
            INDEX `idx_evt_month` (`event_month`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
    conn.commit()
    conn.close()
    print("Dataset tables verified.")

def import_manufacturers():
    fpath = os.path.join(DATA_DIR, "manufacturers-1681209657.csv")
    if not os.path.exists(fpath):
        print(f"Manufacturers file not found at: {fpath}")
        return
    print(f"\nImporting manufacturers from {os.path.basename(fpath)}...")
    df = pd.read_csv(fpath, low_memory=False)
    df = df.drop_duplicates(subset=["id"], keep="first")
    df = df.where(pd.notnull(df), None)

    conn = get_connection()
    cur = conn.cursor()
    
    # Check existing count
    cur.execute("SELECT COUNT(*) FROM `manufacturers`")
    cnt = cur.fetchone()[0]
    if cnt >= len(df):
        print(f"Manufacturers already imported ({cnt:,} records). Skipping.")
        conn.close()
        return

    sql = """
    INSERT INTO `manufacturers` (
        `id`, `name`, `parent_company`, `address`, `representative`,
        `comment`, `source`, `slug`, `created_at`, `updated_at`
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);
    """

    records = []
    for _, row in df.iterrows():
        records.append((
            str(row.get("id", "")).strip()[:64],
            str(row.get("name", ""))[:500] if row.get("name") is not None else None,
            str(row.get("parent_company", ""))[:500] if row.get("parent_company") is not None else None,
            str(row.get("address", "")) if row.get("address") is not None else None,
            str(row.get("representative", ""))[:500] if row.get("representative") is not None else None,
            str(row.get("comment", "")) if row.get("comment") is not None else None,
            str(row.get("source", ""))[:255] if row.get("source") is not None else None,
            str(row.get("slug", ""))[:500] if row.get("slug") is not None else None,
            str(row.get("created_at", ""))[:100] if row.get("created_at") is not None else None,
            str(row.get("updated_at", ""))[:100] if row.get("updated_at") is not None else None,
        ))

    batch_size = 5000
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        cur.executemany(sql, batch)
        conn.commit()
        print(f" - Inserted {min(i + batch_size, len(records)):,} / {len(records):,} manufacturers")

    conn.close()
    print("Manufacturers import completed.")

def import_devices():
    fpath = os.path.join(DATA_DIR, "devices-1681209661.csv")
    if not os.path.exists(fpath):
        print(f"Devices file not found at: {fpath}")
        return
    print(f"\nImporting devices from {os.path.basename(fpath)}...")
    df = pd.read_csv(fpath, low_memory=False)
    df = df.drop_duplicates(subset=["id"], keep="first")
    df = df.where(pd.notnull(df), None)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM `devices`")
    cnt = cur.fetchone()[0]
    if cnt >= len(df):
        print(f"Devices already imported ({cnt:,} records). Skipping.")
        conn.close()
        return

    sql = """
    INSERT INTO `devices` (
        `id`, `manufacturer_id`, `name`, `classification`, `code`,
        `description`, `distributed_to`, `implanted`, `number`,
        `quantity_in_commerce`, `risk_class`, `slug`, `country`,
        `created_at`, `updated_at`
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);
    """

    records = []
    for _, row in df.iterrows():
        qty = row.get("quantity_in_commerce")
        try:
            qty_val = float(qty) if qty is not None else None
        except Exception:
            qty_val = None

        records.append((
            str(row.get("id", "")).strip()[:64],
            str(row.get("manufacturer_id", "")).strip()[:64] if row.get("manufacturer_id") is not None else None,
            str(row.get("name", ""))[:500] if row.get("name") is not None else None,
            str(row.get("classification", ""))[:255] if row.get("classification") is not None else None,
            str(row.get("code", ""))[:255] if row.get("code") is not None else None,
            str(row.get("description", "")) if row.get("description") is not None else None,
            str(row.get("distributed_to", "")) if row.get("distributed_to") is not None else None,
            str(row.get("implanted", ""))[:50] if row.get("implanted") is not None else None,
            str(row.get("number", ""))[:255] if row.get("number") is not None else None,
            qty_val,
            str(row.get("risk_class", ""))[:50] if row.get("risk_class") is not None else None,
            str(row.get("slug", ""))[:500] if row.get("slug") is not None else None,
            str(row.get("country", ""))[:50] if row.get("country") is not None else None,
            str(row.get("created_at", ""))[:100] if row.get("created_at") is not None else None,
            str(row.get("updated_at", ""))[:100] if row.get("updated_at") is not None else None,
        ))

    batch_size = 5000
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        cur.executemany(sql, batch)
        conn.commit()
        print(f" - Inserted {min(i + batch_size, len(records)):,} / {len(records):,} devices")

    conn.close()
    print("Devices import completed.")

def import_events():
    fpath = os.path.join(DATA_DIR, "events-1681209680.csv")
    if not os.path.exists(fpath):
        print(f"Events file not found at: {fpath}")
        return
    print(f"\nImporting events from {os.path.basename(fpath)}...")
    df = pd.read_csv(fpath, low_memory=False)
    df = df.drop_duplicates(subset=["id"], keep="first")
    df = df.where(pd.notnull(df), None)

    # Precalculate event_year and event_month from date
    df["dt_parsed"] = pd.to_datetime(df["date"], errors="coerce")
    df["event_year"] = df["dt_parsed"].dt.year
    df["event_month"] = df["dt_parsed"].dt.month

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM `events`")
    cnt = cur.fetchone()[0]
    if cnt >= len(df):
        print(f"Events already imported ({cnt:,} records). Skipping.")
        conn.close()
        return

    sql = """
    INSERT INTO `events` (
        `id`, `device_id`, `type`, `status`, `country`,
        `action`, `action_classification`, `action_level`, `action_summary`,
        `determined_cause`, `reason`, `date`, `event_year`, `event_month`,
        `date_initiated_by_firm`, `date_posted`, `date_terminated`,
        `date_updated`, `created_at`, `updated_at`
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE `type` = VALUES(`type`);
    """

    records = []
    for _, row in df.iterrows():
        eyear = int(row["event_year"]) if pd.notnull(row["event_year"]) else None
        emonth = int(row["event_month"]) if pd.notnull(row["event_month"]) else None

        records.append((
            str(row.get("id", "")).strip()[:64],
            str(row.get("device_id", "")).strip()[:64] if row.get("device_id") is not None else None,
            str(row.get("type", ""))[:100] if row.get("type") is not None else None,
            str(row.get("status", ""))[:100] if row.get("status") is not None else None,
            str(row.get("country", ""))[:50] if row.get("country") is not None else None,
            str(row.get("action", "")) if row.get("action") is not None else None,
            str(row.get("action_classification", ""))[:100] if row.get("action_classification") is not None else None,
            str(row.get("action_level", ""))[:100] if row.get("action_level") is not None else None,
            str(row.get("action_summary", "")) if row.get("action_summary") is not None else None,
            str(row.get("determined_cause", "")) if row.get("determined_cause") is not None else None,
            str(row.get("reason", "")) if row.get("reason") is not None else None,
            str(row.get("date", ""))[:100] if row.get("date") is not None else None,
            eyear,
            emonth,
            str(row.get("date_initiated_by_firm", ""))[:100] if row.get("date_initiated_by_firm") is not None else None,
            str(row.get("date_posted", ""))[:100] if row.get("date_posted") is not None else None,
            str(row.get("date_terminated", ""))[:100] if row.get("date_terminated") is not None else None,
            str(row.get("date_updated", ""))[:100] if row.get("date_updated") is not None else None,
            str(row.get("created_at", ""))[:100] if row.get("created_at") is not None else None,
            str(row.get("updated_at", ""))[:100] if row.get("updated_at") is not None else None,
        ))

    batch_size = 5000
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        cur.executemany(sql, batch)
        conn.commit()
        print(f" - Inserted {min(i + batch_size, len(records)):,} / {len(records):,} events")

    conn.close()
    print("Events import completed.")

def verify_import():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM `manufacturers`")
        m_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM `devices`")
        d_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM `events`")
        e_count = cur.fetchone()[0]
        
        print("\n" + "="*50)
        print("MYSQL DATABASE INGESTION VERIFICATION")
        print("="*50)
        print(f"Database: {MYSQL_DB}")
        print(f"Manufacturers Count: {m_count:,}")
        print(f"Devices Count:       {d_count:,}")
        print(f"Events Count:        {e_count:,}")
        print("="*50 + "\n")
    conn.close()

def main():
    t0 = time.time()
    create_database()
    create_dataset_tables()
    import_manufacturers()
    import_devices()
    import_events()
    verify_import()
    print(f"Total import time: {time.time() - t0:.2f} seconds")

if __name__ == "__main__":
    main()
