from django.db import connection

cols = [
    ("masters_companymaster", "city", "VARCHAR(100) DEFAULT '' NOT NULL"),
    ("masters_companymaster", "state", "VARCHAR(100) DEFAULT '' NOT NULL"),
    ("masters_companymaster", "pan", "VARCHAR(10) DEFAULT '' NOT NULL"),
    ("masters_companymaster", "phone", "VARCHAR(20) DEFAULT '' NOT NULL"),
    ("masters_companymaster", "email", "VARCHAR(254) DEFAULT '' NOT NULL"),
    ("masters_companymaster", "gstin", "VARCHAR(15) DEFAULT '' NOT NULL"),
    ("masters_companymaster", "code", "VARCHAR(10) DEFAULT '' NOT NULL"),
    ("masters_companymaster", "is_active", "INTEGER DEFAULT 1 NOT NULL"),
    ("masters_companymaster", "created_at", "DATETIME DEFAULT '2024-01-01 00:00:00' NOT NULL"),
    ("masters_salesmanmaster", "code", "VARCHAR(10) DEFAULT '' NOT NULL"),
    ("masters_salesmanmaster", "phone", "VARCHAR(15) DEFAULT '' NOT NULL"),
    ("masters_salesmanmaster", "email", "VARCHAR(254) DEFAULT '' NOT NULL"),
    ("masters_salesmanmaster", "area", "VARCHAR(100) DEFAULT '' NOT NULL"),
    ("masters_salesmanmaster", "is_active", "INTEGER DEFAULT 1 NOT NULL"),
    ("masters_salesmanmaster", "created_at", "DATETIME DEFAULT '2024-01-01 00:00:00' NOT NULL"),
    ("masters_areamaster", "code", "VARCHAR(10) DEFAULT '' NOT NULL"),
    ("masters_areamaster", "is_active", "INTEGER DEFAULT 1 NOT NULL"),
    ("masters_areamaster", "created_at", "DATETIME DEFAULT '2024-01-01 00:00:00' NOT NULL"),
    ("masters_userprofile", "phone", "VARCHAR(15) DEFAULT '' NOT NULL"),
    ("masters_userprofile", "is_active", "INTEGER DEFAULT 1 NOT NULL"),
]

with connection.cursor() as cursor:
    for table, col, defn in cols:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")
            print(f"OK: {table}.{col}")
        except Exception as e:
            print(f"SKIP: {table}.{col} - {e}")

print("All done!")
