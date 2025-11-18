# crud/pedido_crud.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
try:
    from ORM_clientes.models import Pedido, PedidoDetalle, Cliente, Menu
except Exception:
    from models import Pedido, PedidoDetalle, Cliente, Menu
from datetime import datetime

def crear_pedido(session: Session, cliente_id: int, items: list[dict]):
    """
    items = [
        {"menu_id": 1, "cantidad": 2},
        {"menu_id": 3, "cantidad": 1},
    ]
    """
    cliente = session.get(Cliente, cliente_id)
    if not cliente or not cliente.activo:
        raise ValueError("Cliente no existe o está inactivo.")

    if not items:
        raise ValueError("No hay items en el pedido.")

    total = 0.0
    detalles = []

    for item in items:
        menu = session.get(Menu, item.get("menu_id"))
        cantidad = float(item.get("cantidad", 0))
        if not menu:
            raise ValueError(f"Menu id {item.get('menu_id')} no encontrado.")
        if cantidad <= 0:
            raise ValueError("Cantidad debe ser mayor que 0.")
        precio = float(menu.precio) * cantidad
        total += precio
        detalles.append({"menu": menu, "cantidad": cantidad, "precio_unitario": float(menu.precio)})

    try:
        pedido = Pedido(cliente_id=cliente_id, fecha=datetime.utcnow(), total=total, estado="CREADO")
        session.add(pedido)
        session.flush()  # para obtener id del pedido
        for d in detalles:
            pd = PedidoDetalle(pedido_id=pedido.id, menu_id=d["menu"].id, cantidad=d["cantidad"], precio_unitario=d["precio_unitario"])
            session.add(pd)
        session.commit()
        session.refresh(pedido)
        return pedido
    except SQLAlchemyError:
        session.rollback()
        raise

def listar_pedidos(session: Session, cliente_id: int | None = None):
    query = session.query(Pedido)
    if cliente_id is not None:
        query = query.filter(Pedido.cliente_id == cliente_id)
    return query.order_by(Pedido.fecha.desc()).all()
