# crud/menu_crud.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
try:
    from ORM_clientes.models import Menu, MenuIngrediente, Ingrediente
except Exception:
    from models import Menu, MenuIngrediente, Ingrediente

def crear_menu(session: Session, nombre: str, descripcion: str, precio: float):
    if precio < 0:
        raise ValueError("El precio no puede ser negativo.")

    nuevo = Menu(
        nombre=nombre.strip(),
        descripcion=descripcion.strip(),
        precio=precio
    )
    try:
        session.add(nuevo)
        session.commit()
        session.refresh(nuevo)
        return nuevo
    except IntegrityError:
        session.rollback()
        raise ValueError("Ya existe un menú con ese nombre.")


def listar_menus(session: Session, solo_activos: bool = True):
    query = session.query(Menu)
    if solo_activos and hasattr(Menu, "activo"):
        query = query.filter(Menu.activo == True)
    return query.order_by(Menu.nombre).all()


def asignar_ingrediente_a_menu(session: Session, menu_id: int, ingrediente_id: int, cantidad: float):
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")

    menu = session.get(Menu, menu_id)
    ing = session.get(Ingrediente, ingrediente_id)
    if not menu or not ing:
        raise ValueError("Menu o ingrediente no encontrado.")

    # Verificar si ya existe la relación
    rel = session.query(MenuIngrediente).filter_by(menu_id=menu_id, ingrediente_id=ingrediente_id).first()
    if rel:
        rel.cantidad = cantidad
    else:
        rel = MenuIngrediente(menu_id=menu_id, ingrediente_id=ingrediente_id, cantidad=cantidad)
        session.add(rel)
    session.commit()
    return rel


def eliminar_ingrediente_de_menu(session: Session, menu_id: int, ingrediente_id: int):
    rel = session.query(MenuIngrediente).filter_by(menu_id=menu_id, ingrediente_id=ingrediente_id).first()
    if not rel:
        raise ValueError("Relación no encontrada.")
    session.delete(rel)
    session.commit()
    return True
