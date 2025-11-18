# crud/cliente_crud.py
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
# usar import absoluto (no fallback a 'models')
from ORM_clientes.models import Cliente, Pedido

def crear_cliente(session: Session, nombre: str, email: str, telefono: str = "", direccion: str = ""):
    nombre = (nombre or "").strip()
    email = (email or "").strip().lower()
    if not nombre:
        raise ValueError("El nombre es obligatorio.")
    if not email:
        raise ValueError("El email es obligatorio.")
    nuevo = Cliente(
        nombre=nombre,
        email=email,
        telefono=(telefono or "").strip(),
        direccion=(direccion or "").strip()
    )
    try:
        session.add(nuevo)
        session.commit()
        session.refresh(nuevo)
        return nuevo
    except IntegrityError:
        session.rollback()
        raise ValueError("El email ya existe. Debe ser único.")

def listar_clientes(session: Session, solo_activos: bool = True):
    query = session.query(Cliente)
    if solo_activos and hasattr(Cliente, "activo"):
        query = query.filter(Cliente.activo == True)
    return query.order_by(Cliente.nombre).all()

def actualizar_cliente(session: Session, cliente_id: int, **datos):
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise ValueError("Cliente no encontrado.")
    for campo, valor in datos.items():
        if hasattr(cliente, campo) and valor is not None:
            setattr(cliente, campo, valor)
    try:
        session.commit()
        session.refresh(cliente)
        return cliente
    except IntegrityError:
        session.rollback()
        raise ValueError("Error de integridad (posible email duplicado).")

def desactivar_cliente(session: Session, cliente_id: int):
    """
    Regla de negocio: no borrar cliente con pedidos.
    En vez de borrar, lo marcamos como inactivo.
    """
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise ValueError("Cliente no encontrado.")

    tiene_pedidos = session.query(Pedido).filter_by(cliente_id=cliente_id).count() > 0
    if tiene_pedidos:
        cliente.activo = False
        session.commit()
        return "Cliente desactivado (tiene pedidos asociados)."

    session.delete(cliente)
    session.commit()
    return "Cliente eliminado correctamente."
