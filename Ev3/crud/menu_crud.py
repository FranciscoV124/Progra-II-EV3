from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models import Menu, Ingrediente
from typing import Optional, List, Dict

class MenuCRUD:
    """Clase para operaciones CRUD de menús con validación de recetas."""
    
    @staticmethod
    def crear_menu(db: Session, nombre: str, descripcion: str, precio: float, 
                   categoria: str = None, disponible: bool = True, 
                   receta: Dict[str, float] = None) -> Optional[Menu]:
        """Crea un nuevo elemento de menú con validaciones de receta e ingredientes."""
        try:
            # Validación de nombre obligatorio
            if not nombre or not nombre.strip():
                raise ValueError("El nombre del menú no puede estar vacío")
            
            # Validación de precio válido
            if precio <= 0:
                raise ValueError("El precio debe ser mayor que cero")
            
            # Validación y verificación de receta
            if receta:
                # Control de ingredientes duplicados en la receta
                ingredientes_vistos = set()
                for ingrediente, cantidad in receta.items():
                    if not ingrediente or not ingrediente.strip():
                        raise ValueError("Nombre de ingrediente vacío en la receta")
                    
                    ingrediente_lower = ingrediente.lower()
                    if ingrediente_lower in ingredientes_vistos:
                        raise ValueError(f"El ingrediente '{ingrediente}' está duplicado en la receta")
                    ingredientes_vistos.add(ingrediente_lower)
                    
                    # Validar cantidades
                    if cantidad <= 0:
                        raise ValueError(f"La cantidad del ingrediente '{ingrediente}' debe ser mayor que cero")
                    
                    # Validar que el ingrediente exista en la base de datos
                    ingrediente_db = db.query(Ingrediente).filter(
                        Ingrediente.nombre == ingrediente
                    ).first()
                    if not ingrediente_db:
                        raise ValueError(f"El ingrediente '{ingrediente}' no existe en la base de datos")
                    
                    # Validar que tenga stock suficiente
                    if ingrediente_db.stock < cantidad:
                        raise ValueError(
                            f"Stock insuficiente para '{ingrediente}'. "
                            f"Disponible: {ingrediente_db.stock} {ingrediente_db.unidad}, "
                            f"Requerido: {cantidad} {ingrediente_db.unidad}"
                        )
            
            nuevo_menu = Menu(
                nombre=nombre.strip(),
                descripcion=descripcion.strip() if descripcion else None,
                precio=precio,
                categoria=categoria.strip() if categoria else None,
                disponible=1 if disponible else 0,
                receta=receta
            )
            db.add(nuevo_menu)
            db.commit()
            db.refresh(nuevo_menu)
            return nuevo_menu
        except (SQLAlchemyError, ValueError) as e:
            db.rollback()
            raise Exception(f"Error al crear menú: {str(e)}")
    
    @staticmethod
    def obtener_menu_por_id(db: Session, menu_id: int) -> Optional[Menu]:
        try:
            return db.query(Menu).filter(Menu.id == menu_id).first()
        except SQLAlchemyError as e:
            raise Exception(f"Error al obtener menú: {str(e)}")
    
    @staticmethod
    def obtener_todos_menus(db: Session) -> List[Menu]:
        try:
            return db.query(Menu).all()
        except SQLAlchemyError as e:
            raise Exception(f"Error al obtener menús: {str(e)}")
    
    @staticmethod
    def obtener_menus_disponibles(db: Session) -> List[Menu]:
        try:
            return db.query(Menu).filter(Menu.disponible == 1).all()
        except SQLAlchemyError as e:
            raise Exception(f"Error al obtener menús disponibles: {str(e)}")
    
    @staticmethod
    def obtener_menus_por_categoria(db: Session, categoria: str) -> List[Menu]:
        try:
            return db.query(Menu).filter(Menu.categoria == categoria).all()
        except SQLAlchemyError as e:
            raise Exception(f"Error al obtener menús por categoría: {str(e)}")
    
    @staticmethod
    def actualizar_menu(db: Session, menu_id: int, nombre: str = None, 
                       descripcion: str = None, precio: float = None,
                       categoria: str = None, disponible: bool = None,
                       receta: Dict[str, float] = None) -> Optional[Menu]:
        try:
            menu = db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                return None
            
            if nombre is not None:
                menu.nombre = nombre
            if descripcion is not None:
                menu.descripcion = descripcion
            if precio is not None:
                menu.precio = precio
            if categoria is not None:
                menu.categoria = categoria
            if disponible is not None:
                menu.disponible = 1 if disponible else 0
            if receta is not None:
                menu.receta = receta
            
            db.commit()
            db.refresh(menu)
            return menu
        except SQLAlchemyError as e:
            db.rollback()
            raise Exception(f"Error al actualizar menú: {str(e)}")
    
    @staticmethod
    def cambiar_disponibilidad(db: Session, menu_id: int, disponible: bool) -> Optional[Menu]:
        try:
            menu = db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                return None
            
            menu.disponible = 1 if disponible else 0
            db.commit()
            db.refresh(menu)
            return menu
        except SQLAlchemyError as e:
            db.rollback()
            raise Exception(f"Error al cambiar disponibilidad: {str(e)}")
    
    @staticmethod
    def eliminar_menu(db: Session, menu_id: int) -> bool:
        try:
            menu = db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                return False
            
            db.delete(menu)
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            raise Exception(f"Error al eliminar menú: {str(e)}")