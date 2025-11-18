# graficos.py
from sqlalchemy.orm import Session
try:
    from ORM_clientes.models import Pedido, PedidoDetalle, Menu
except Exception:
    from models import Pedido, PedidoDetalle, Menu
from collections import defaultdict
import matplotlib.pyplot as plt
from datetime import datetime

def grafico_ventas_por_fecha(session: Session):
    pedidos = session.query(Pedido).all()
    ventas_por_fecha = defaultdict(float)
    for p in pedidos:
        if not p.fecha or p.total is None:
            continue
        fecha_key = p.fecha.date().isoformat()
        ventas_por_fecha[fecha_key] += float(p.total)

    if not ventas_por_fecha:
        print("No hay datos disponibles para Ventas por fecha.")
        return

    fechas = list(ventas_por_fecha.keys())
    totales = list(ventas_por_fecha.values())

    plt.figure()
    plt.bar(fechas, totales)
    plt.title("Ventas por fecha")
    plt.xlabel("Fecha")
    plt.ylabel("Total vendido")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def grafico_menus_mas_pedidos(session: Session):
    detalles = session.query(PedidoDetalle).all()
    conteo_menus = defaultdict(float)

    for d in detalles:
        if not d.menu_id or d.cantidad is None:
            continue
        conteo_menus[d.menu_id] += float(d.cantidad)

    if not conteo_menus:
        print("No hay datos disponibles para Menús más pedidos.")
        return

    menu_ids = list(conteo_menus.keys())
    cantidades = list(conteo_menus.values())

    # Obtener nombres
    nombres = []
    for mid in menu_ids:
        menu = session.get(Menu, mid)
        nombres.append(menu.nombre if menu else f"ID {mid}")

    plt.figure()
    plt.bar(nombres, cantidades)
    plt.title("Menús más pedidos")
    plt.xlabel("Menú")
    plt.ylabel("Cantidad")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
