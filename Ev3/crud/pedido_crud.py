from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models import Pedido, ItemPedido, Cliente, Menu, Ingrediente
from typing import List, Optional, Dict

class PedidoCRUD:
    """Clase para operaciones CRUD de pedidos con gestión de items."""
    
    @staticmethod
    def crear_pedido(db: Session, cliente_id: int, items: List[Dict]) -> Optional[Pedido]:
        """Crea un pedido completo con validación de cliente, menús y disponibilidad,
        descontando stock de los ingredientes según las recetas de cada menú.
        """
        try:
            # 1) Validación de cliente
            if not cliente_id or cliente_id <= 0:
                raise ValueError("Debe seleccionar un cliente válido")
            
            cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
            if not cliente:
                raise ValueError(f"Cliente con ID {cliente_id} no existe")
            
            # 2) Validar items
            if not items or len(items) == 0:
                raise ValueError("Debe agregar al menos un producto al pedido")

            # ----------------------------------------------------
            # 3) Calcular consumo total de ingredientes
            #    según recetas y cantidades pedidas
            # ----------------------------------------------------
            consumo_ingredientes = {}  # {nombre_ingrediente: cantidad_total}

            for item_data in items:
                menu_id = item_data.get("menu_id")
                cantidad = item_data.get("cantidad", 1)
                
                if not menu_id:
                    raise ValueError("Falta el ID del menú en uno de los items")
                if cantidad <= 0:
                    raise ValueError("La cantidad debe ser mayor que cero")
                
                # Obtener menú y validar
                menu = db.query(Menu).filter(Menu.id == menu_id).first()
                if not menu:
                    raise ValueError(f"Menú con ID {menu_id} no existe")
                if not menu.disponible:
                    raise ValueError(f"El menú '{menu.nombre}' no está disponible")
                
                # Acumular uso de ingredientes según receta
                if menu.receta:
                    for ing_nombre, cant_por_menu in menu.receta.items():
                        try:
                            cant_por_menu = float(cant_por_menu)
                        except (TypeError, ValueError):
                            raise ValueError(
                                f"Cantidad inválida en la receta del ingrediente '{ing_nombre}' "
                                f"del menú '{menu.nombre}'"
                            )
                        if cant_por_menu <= 0:
                            raise ValueError(
                                f"La cantidad del ingrediente '{ing_nombre}' en el menú "
                                f"'{menu.nombre}' debe ser mayor que cero"
                            )
                        
                        consumo_total = cant_por_menu * cantidad
                        consumo_ingredientes[ing_nombre] = (
                            consumo_ingredientes.get(ing_nombre, 0.0) + consumo_total
                        )

            # ----------------------------------------------------
            # 4) Verificar stock suficiente para TODOS los ingredientes
            # ----------------------------------------------------
            for nombre_ing, consumo_total in consumo_ingredientes.items():
                ingrediente = db.query(Ingrediente).filter(
                    Ingrediente.nombre == nombre_ing
                ).first()
                if not ingrediente:
                    raise ValueError(
                        f"El ingrediente '{nombre_ing}' no existe en la base de datos"
                    )
                if ingrediente.stock < consumo_total:
                    raise ValueError(
                        f"Stock insuficiente para '{nombre_ing}'. "
                        f"Disponible: {ingrediente.stock} {ingrediente.unidad}, "
                        f"Requerido para este pedido: {consumo_total} {ingrediente.unidad}"
                    )

            # ----------------------------------------------------
            # 5) Crear pedido e items (ya sabemos que hay stock)
            # ----------------------------------------------------
            nuevo_pedido = Pedido(cliente_id=cliente_id)
            db.add(nuevo_pedido)
            db.flush()  # obtener ID del pedido
            
            for item_data in items:
                menu_id = item_data.get("menu_id")
                cantidad = item_data.get("cantidad", 1)

                item_pedido = ItemPedido(
                    pedido_id=nuevo_pedido.id,
                    menu_id=menu_id,
                    cantidad=cantidad
                )
                db.add(item_pedido)

            # ----------------------------------------------------
            # 6) Descontar stock de ingredientes
            # ----------------------------------------------------
            for nombre_ing, consumo_total in consumo_ingredientes.items():
                ingrediente = db.query(Ingrediente).filter(
                    Ingrediente.nombre == nombre_ing
                ).first()
                # Aquí ya sabemos que existe y tiene stock suficiente
                ingrediente.stock -= consumo_total

            # 7) Confirmar todo
            db.commit()
            db.refresh(nuevo_pedido)
            return nuevo_pedido

        except (SQLAlchemyError, ValueError) as e:
            db.rollback()
            raise Exception(f"Error al crear pedido: {str(e)}")
    
    @staticmethod
    def obtener_pedido_por_id(db: Session, pedido_id: int) -> Optional[Pedido]:
        """Obtiene un pedido con todos sus items"""
        try:
            return db.query(Pedido).filter(Pedido.id == pedido_id).first()
        except SQLAlchemyError as e:
            raise Exception(f"Error al obtener pedido: {str(e)}")
    
    @staticmethod
    def obtener_todos_pedidos(db: Session) -> List[Pedido]:
        """Obtiene todos los pedidos"""
        try:
            return db.query(Pedido).all()
        except SQLAlchemyError as e:
            raise Exception(f"Error al obtener pedidos: {str(e)}")
    
    @staticmethod
    def obtener_pedidos_por_cliente(db: Session, cliente_id: int) -> List[Pedido]:
        """Obtiene todos los pedidos de un cliente"""
        try:
            return db.query(Pedido).filter(Pedido.cliente_id == cliente_id).all()
        except SQLAlchemyError as e:
            raise Exception(f"Error al obtener pedidos del cliente: {str(e)}")
    
    @staticmethod
    def agregar_item(db: Session, pedido_id: int, menu_id: int, cantidad: int = 1) -> Optional[ItemPedido]:
        """Añade un elemento al pedido existente o actualiza cantidad si ya existe."""
        try:
            # Verificación de existencia del pedido
            pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
            if not pedido:
                raise ValueError(f"Pedido con ID {pedido_id} no existe")
            
            # Verificación de existencia y disponibilidad del menú
            menu = db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                raise ValueError(f"Menú con ID {menu_id} no existe")
            if not menu.disponible:
                raise ValueError(f"El menú '{menu.nombre}' no está disponible")
            
            # Verificar si ya existe este item en el pedido
            item_existente = db.query(ItemPedido).filter(
                ItemPedido.pedido_id == pedido_id,
                ItemPedido.menu_id == menu_id
            ).first()
            
            if item_existente:
                # Si existe, aumentar la cantidad
                item_existente.cantidad += cantidad
                db.commit()
                db.refresh(item_existente)
                return item_existente
            else:
                # Si no existe, crear nuevo item
                nuevo_item = ItemPedido(
                    pedido_id=pedido_id,
                    menu_id=menu_id,
                    cantidad=cantidad
                )
                db.add(nuevo_item)
                db.commit()
                db.refresh(nuevo_item)
                return nuevo_item
                
        except (SQLAlchemyError, ValueError) as e:
            db.rollback()
            raise Exception(f"Error al agregar item: {str(e)}")
    
    @staticmethod
    def actualizar_cantidad_item(db: Session, item_id: int, nueva_cantidad: int) -> Optional[ItemPedido]:
        """Actualiza la cantidad de un item específico"""
        try:
            item = db.query(ItemPedido).filter(ItemPedido.id == item_id).first()
            if not item:
                return None
            
            if nueva_cantidad <= 0:
                raise ValueError("La cantidad debe ser mayor a 0")
            
            item.cantidad = nueva_cantidad
            db.commit()
            db.refresh(item)
            return item
            
        except (SQLAlchemyError, ValueError) as e:
            db.rollback()
            raise Exception(f"Error al actualizar cantidad: {str(e)}")
    
    @staticmethod
    def eliminar_item(db: Session, item_id: int) -> bool:
        """Elimina un item específico de un pedido"""
        try:
            item = db.query(ItemPedido).filter(ItemPedido.id == item_id).first()
            if not item:
                return False
            
            db.delete(item)
            db.commit()
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            raise Exception(f"Error al eliminar item: {str(e)}")
    
    @staticmethod
    def eliminar_pedido(db: Session, pedido_id: int) -> bool:
        """Elimina un pedido completo con todos sus items"""
        try:
            pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
            if not pedido:
                return False
            
            # Los items se eliminan automáticamente por cascade
            db.delete(pedido)
            db.commit()
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            raise Exception(f"Error al eliminar pedido: {str(e)}")
    
    @staticmethod
    def calcular_total(db: Session, pedido_id: int) -> float:
        """Calcula el total de un pedido"""
        try:
            pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
            if not pedido:
                return 0.0
            
            return pedido.total  # Usa la propiedad del modelo
            
        except SQLAlchemyError as e:
            raise Exception(f"Error al calcular total: {str(e)}")