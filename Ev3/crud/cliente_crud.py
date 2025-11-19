from sqlalchemy.orm import Session 
from sqlalchemy.exc import SQLAlchemyError
from models import Cliente
from typing import Optional, List
import re

class ClienteCRUD:
    """Clase para operaciones CRUD relacionadas con la gestión de clientes."""
    
    @staticmethod
    def validar_correo(correo: str) -> bool:
        """Valida el formato del correo electrónico usando expresión regular."""
        if not correo:
            return True  # Correo es opcional
        # Patrón estándar para validación de email
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(patron, correo) is not None
    
    @staticmethod
    def crear_cliente(db: Session, rut: str, nombre: str, correo: str = None) -> Optional[Cliente]:
        """Crea un nuevo cliente con validaciones de integridad de datos."""
        try:
            # Validación de campos obligatorios
            if not rut or not rut.strip():
                raise ValueError("El RUT no puede estar vacío")
            if not nombre or not nombre.strip():
                raise ValueError("El nombre no puede estar vacío")
            
            # Validación de formato de correo electrónico
            if correo and not ClienteCRUD.validar_correo(correo):
                raise ValueError("Formato de correo electrónico inválido")
            
            # Verificación de unicidad del RUT
            cliente_existente = db.query(Cliente).filter(Cliente.rut == rut).first()
            if cliente_existente:
                raise ValueError(f"El cliente con RUT '{rut}' ya existe")
            
            # Verificación de unicidad del correo
            if correo:
                correo_existente = db.query(Cliente).filter(Cliente.correo == correo).first()
                if correo_existente:
                    raise ValueError(f"El correo '{correo}' ya está registrado")
            
            nuevo_cliente = Cliente(rut=rut.strip(), nombre=nombre.strip(), correo=correo.strip() if correo else None)
            db.add(nuevo_cliente)
            db.commit()
            db.refresh(nuevo_cliente)
            return nuevo_cliente
        except (SQLAlchemyError, ValueError) as e:
            db.rollback()
            raise Exception(f"Error al crear cliente: {str(e)}")
    
    @staticmethod
    def obtener_cliente_por_id(db: Session, cliente_id: int) -> Optional[Cliente]:
        """Busca y retorna un cliente por su identificador único."""
        try:
            return db.query(Cliente).filter(Cliente.id == cliente_id).first()
        except SQLAlchemyError as e:
            raise Exception(f"Error al obtener cliente: {str(e)}")
    
    @staticmethod
    def obtener_cliente_por_rut(db: Session, rut: str) -> Optional[Cliente]:
        """Busca y retorna un cliente por su RUT."""
        try:
            return db.query(Cliente).filter(Cliente.rut == rut).first()
        except SQLAlchemyError as e:
            raise Exception(f"Error al buscar cliente: {str(e)}")
    
    @staticmethod
    def obtener_todos_clientes(db: Session) -> List[Cliente]:
        """Retorna la lista completa de clientes registrados."""
        try:
            return db.query(Cliente).all()
        except SQLAlchemyError as e:
            raise Exception(f"Error al obtener clientes: {str(e)}")
    
    @staticmethod
    def actualizar_cliente(db: Session, cliente_id: int, rut: str = None, 
                          nombre: str = None, correo: str = None) -> Optional[Cliente]:
        """Actualiza los datos de un cliente"""
        try:
            cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
            if not cliente:
                return None
            
            if rut is not None:
                if not rut.strip():
                    raise ValueError("El RUT no puede estar vacío")
                # Verificar que el nuevo RUT no esté en uso
                rut_existente = db.query(Cliente).filter(
                    Cliente.rut == rut,
                    Cliente.id != cliente_id
                ).first()
                if rut_existente:
                    raise ValueError(f"El RUT '{rut}' ya está en uso")
                cliente.rut = rut.strip()
            
            if nombre is not None:
                if not nombre.strip():
                    raise ValueError("El nombre no puede estar vacío")
                cliente.nombre = nombre.strip()
            
            if correo is not None:
                if correo.strip() and not ClienteCRUD.validar_correo(correo):
                    raise ValueError("Formato de correo electrónico inválido")
                # Verificar que el correo no esté en uso
                if correo.strip():
                    correo_existente = db.query(Cliente).filter(
                        Cliente.correo == correo,
                        Cliente.id != cliente_id
                    ).first()
                    if correo_existente:
                        raise ValueError(f"El correo '{correo}' ya está en uso")
                cliente.correo = correo.strip() if correo.strip() else None
            
            db.commit()
            db.refresh(cliente)
            return cliente
        except (SQLAlchemyError, ValueError) as e:
            db.rollback()
            raise Exception(f"Error al actualizar cliente: {str(e)}")
    
    @staticmethod
    def eliminar_cliente(db: Session, cliente_id: int) -> bool:
        """Elimina un cliente por su ID"""
        try:
            cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
            if not cliente:
                return False
            
            db.delete(cliente)
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            raise Exception(f"Error al eliminar cliente: {str(e)}")
