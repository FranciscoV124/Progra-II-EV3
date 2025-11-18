# models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

# Importar Base desde database
try:
    from ORM_clientes.database import Base
except Exception:
    from database import Base  # type: ignore

class Ingrediente(Base):
    __tablename__ = "ingredientes"
    __table_args__ = (UniqueConstraint("nombre", name="uix_ingrediente_nombre"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(128), nullable=False, index=True)
    unidad = Column(String(32), nullable=False, default="unid")
    stock_actual = Column(Float, nullable=False, default=0.0)
    stock_minimo = Column(Float, nullable=False, default=0.0)
    precio_unitario = Column(Float, nullable=False, default=0.0)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(128), nullable=False)
    email = Column(String(128), nullable=True)
    telefono = Column(String(32), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    total = Column(Float, default=0.0)
    estado = Column(String(32), default="pendiente")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cliente = relationship("Cliente", backref="pedidos", lazy="joined")

class Menu(Base):
    __tablename__ = "menus"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(128), nullable=False, unique=True)
    precio = Column(Float, default=0.0)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MenuIngrediente(Base):
    __tablename__ = "menu_ingredientes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)
    ingrediente_id = Column(Integer, ForeignKey("ingredientes.id"), nullable=False)
    cantidad = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class PedidoDetalle(Base):
    __tablename__ = "pedido_detalles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    subtotal = Column(Float, nullable=False, default=0.0)

    pedido = relationship("Pedido", backref="detalles")
    menu = relationship("Menu", backref="detalles_pedido")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
