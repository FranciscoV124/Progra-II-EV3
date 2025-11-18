# main.py
import importlib.util
import pathlib
import sys
import traceback

BASE_DIR = pathlib.Path(__file__).resolve().parent

# Cargar engine, get_session y Base (intento paquete -> relativo -> carga dinámica)
try:
    from ORM_clientes.database import engine, get_session, Base
except Exception:
    try:
        from database import engine, get_session, Base
    except Exception:
        try:
            spec = importlib.util.spec_from_file_location("database", str(BASE_DIR / "database.py"))
            db = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(db)  # type: ignore
            engine = db.engine
            get_session = db.get_session
            Base = db.Base
        except Exception:
            print("ERROR: no se pudo cargar ORM_clientes.database")
            traceback.print_exc()
            raise


def _load_models():
    """Intentar importar modelos desde paquete; si falla cargar desde archivo models.py."""
    try:
        # Caso: se usa el paquete ORM_clientes
        import ORM_clientes.models as m
        return m
    except Exception:
        try:
            # Caso: se ejecuta dentro de la carpeta ORM_clientes
            import models as m  # type: ignore
            return m
        except Exception:
            try:
                # Carga directa desde archivo models.py
                spec = importlib.util.spec_from_file_location("models", str(BASE_DIR / "models.py"))
                m = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(m)  # type: ignore
                return m
            except Exception:
                print("ERROR: no se pudo cargar ORM_clientes.models")
                traceback.print_exc()
                return None


def crear_tablas():
    print("Creando tablas en la base de datos...")
    # ⚠️ IMPORTANTE: cargar modelos antes de create_all
    models = _load_models()
    if models is None:
        print("Modelos no disponibles; no se pueden crear las tablas.")
        return

    # En este punto, Base.metadata ya conoce Cliente, Ingrediente, Menu, etc.
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas correctamente.")


def datos_iniciales():
    """Insertar datos de ejemplo (no usar campos que no existan en el modelo)."""
    models = _load_models()
    if models is None:
        print("Modelos no disponibles: se omiten datos iniciales.")
        return

    Cliente = getattr(models, "Cliente", None)
    Ingrediente = getattr(models, "Ingrediente", None)
    Menu = getattr(models, "Menu", None)

    if not (Cliente or Ingrediente or Menu):
        print("No se detectaron entidades válidas en models.py; omitiendo inserción de datos.")
        return

    session = get_session()
    try:
        # Asegurarse de que las tablas existen ANTES de consultar
        Base.metadata.create_all(bind=engine)

        if Cliente and session.query(Cliente).count() == 0:
            c1 = Cliente(nombre="Cliente Demo", email="demo@example.com", telefono=None)
            session.add(c1)

        if Ingrediente and session.query(Ingrediente).count() == 0:
            i1 = Ingrediente(
                nombre="Tomate",
                unidad="kg",
                stock_actual=10,
                stock_minimo=2,
                precio_unitario=800
            )
            i2 = Ingrediente(
                nombre="Pan",
                unidad="unid",
                stock_actual=50,
                stock_minimo=10,
                precio_unitario=200
            )
            session.add_all([i1, i2])

        if Menu and session.query(Menu).count() == 0:
            try:
                m1 = Menu(nombre="Completo", precio=3500)
            except TypeError:
                # por si el modelo Menu tiene otros parámetros obligatorios
                m1 = Menu(nombre="Completo")
            session.add(m1)

        session.commit()
        print("Datos iniciales insertados (si procedía).")
    except Exception as e:
        session.rollback()
        print("Error al insertar datos iniciales:", e)
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    crear_tablas()
    datos_iniciales()
