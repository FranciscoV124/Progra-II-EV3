from sqlalchemy import Column, String, Float, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Cliente(Base):
    """Modelo para representar clientes del restaurante."""
    __tablename__ = "Clientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rut = Column(String, unique=True, index=True, nullable=False)  # Identificador único del cliente
    nombre = Column(String, nullable=False)
    correo = Column(String, nullable=True)  # Campo opcional
    
    # Relación uno a muchos: un cliente puede tener múltiples pedidos
    pedidos = relationship("Pedido", back_populates="cliente", cascade="all, delete-orphan")


class Ingrediente(Base):
    """Modelo para gestionar ingredientes disponibles en el inventario."""
    __tablename__ = "Ingredientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False, unique=True)  # Nombre único del ingrediente
    stock = Column(Float, default=0.0)  # Cantidad disponible en inventario
    unidad = Column(String, nullable=False)  # Unidad de medida: kg, litros, unidades, etc.


class Menu(Base):
    """Modelo para representar elementos del menú del restaurante."""
    __tablename__ = "Menus"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    precio = Column(Float, nullable=False)
    categoria = Column(String, nullable=True)  # Clasificación: Churrascos, Bebidas, Postres, etc.
    disponible = Column(Integer, default=1)  # Control de disponibilidad: 1=disponible, 0=no disponible
    receta = Column(JSON, nullable=True)  # Ingredientes necesarios en formato JSON
    
    # Relación uno a muchos: un menú puede aparecer en múltiples pedidos
    items = relationship("ItemPedido", back_populates="menu", cascade="all, delete-orphan")


class Pedido(Base):
    """Modelo para gestionar pedidos realizados por clientes."""
    __tablename__ = "Pedidos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(DateTime, default=datetime.now)  # Timestamp automático de creación
    estado = Column(String, default="Pendiente")  # Estados: Pendiente, En preparación, Completado
    
    # Referencia al cliente que realizó el pedido
    cliente_id = Column(Integer, ForeignKey("Clientes.id"), nullable=False)
    
    # Relaciones bidireccionales
    cliente = relationship("Cliente", back_populates="pedidos")
    items = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")
    
    @property
    def total(self) -> float:
        """Calcula el total del pedido sumando todos los subtotales de los items."""
        return sum(item.subtotal for item in self.items)


class ItemPedido(Base):
    """Modelo para representar elementos individuales dentro de un pedido."""
    __tablename__ = "ItemPedidos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cantidad = Column(Integer, nullable=False)  # Cantidad solicitada del elemento del menú

    # Referencias a pedido y menú
    pedido_id = Column(Integer, ForeignKey("Pedidos.id"), nullable=False)
    menu_id = Column(Integer, ForeignKey("Menus.id"), nullable=False)
    
    # Relaciones bidireccionales
    pedido = relationship("Pedido", back_populates="items")
    menu = relationship("Menu", back_populates="items")

    @property
    def subtotal(self) -> float:
        """Calcula el subtotal multiplicando precio por cantidad."""
        if self.menu:
            return self.menu.precio * self.cantidad
        return 0.0
