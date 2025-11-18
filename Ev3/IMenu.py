# IMenu.py
from typing import Protocol, List, Optional
from Ingrediente import Ingrediente 
from Stock import Stock 

class IMenu(Protocol):

    # Atributos/Propiedades Requeridas
    nombre: str
    precio: float
    
    @property
    def cantidad(self) -> int:
        """Cantidad de este elemento en el pedido."""
        ...
        
    @cantidad.setter
    def cantidad(self, value: int) -> None:
        """Permite modificar la cantidad."""
        ...

    def esta_disponible(self, stock: 'Stock') -> bool:
        """
        Verifica si los ingredientes requeridos para este menú están
        disponibles en el stock.
        """
        ...