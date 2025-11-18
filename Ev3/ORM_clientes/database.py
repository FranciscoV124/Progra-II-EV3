# database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path

# Carpeta raíz del proyecto: Ev3 (un nivel arriba de ORM_clientes)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "restaurante.db"

# Ahora TODOS (ORM y Restaurante.py) usan el mismo archivo
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base = declarative_base()

# ... (deja el resto del archivo igual)



def test_connection(timeout: float = 2.0) -> bool:
    """Intenta una consulta simple al motor. Devuelve True si OK."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


@contextmanager
def session_scope():
    """Context manager: commit si OK, rollback y re-raise si falla."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()


def get_session():
    """Obtener sesión simple (recuerda cerrarla)."""
    return SessionLocal()


def init_db():
    """Crear tablas si no existen."""
    from sqlalchemy import inspect
    if not inspect(engine).has_table("ingredientes"):
        Base.metadata.create_all(bind=engine)


# inicializar esquema al importar el paquete
try:
    init_db()
except Exception:
    # no interrumpir imports si algo falla en creación de tablas (depuración posterior)
    pass
