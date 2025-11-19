from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Configuración de la base de datos SQLite local
DATABASE_URL = 'sqlite:///./proyecto.db'

# Crear el motor de base de datos con configuración para SQLite
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Configurar fábrica de sesiones de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para todos los modelos ORM
Base = declarative_base()


def get_session():
    """Generador que proporciona sesiones de base de datos con manejo automático de cierre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()