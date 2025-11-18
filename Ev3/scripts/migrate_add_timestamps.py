import sqlite3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "restaurante.db"

if not DB.exists():
    print(f"No se encontró {DB}. Ejecuta desde la raíz del proyecto.")
    sys.exit(1)

# backup
bak = ROOT / "restaurante.db.bak"
print(f"Haciendo backup: {bak}")
with open(DB, "rb") as r, open(bak, "wb") as w:
    w.write(r.read())

conn = sqlite3.connect(str(DB))
cur = conn.cursor()

def has_col(table, col):
    cur.execute(f"PRAGMA table_info('{table}')")
    return col in [r[1] for r in cur.fetchall()]

changed = False
# Añadir columnas sin DEFAULT (nullable)
if not has_col("ingredientes", "created_at"):
    print("Agregando columna created_at (nullable)...")
    cur.execute("ALTER TABLE ingredientes ADD COLUMN created_at DATETIME")
    changed = True

if not has_col("ingredientes", "updated_at"):
    print("Agregando columna updated_at (nullable)...")
    cur.execute("ALTER TABLE ingredientes ADD COLUMN updated_at DATETIME")
    changed = True

if changed:
    # Rellenar con timestamp actual donde estén NULL
    print("Actualizando valores NULL a la fecha actual...")
    cur.execute("UPDATE ingredientes SET created_at = datetime('now') WHERE created_at IS NULL")
    cur.execute("UPDATE ingredientes SET updated_at = datetime('now') WHERE updated_at IS NULL")
    conn.commit()
    print("Migración completada.")
else:
    print("No se requirió migración (columnas ya presentes).")

cur.close()
conn.close()