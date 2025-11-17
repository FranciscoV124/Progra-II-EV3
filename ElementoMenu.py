from dataclasses import dataclass, field
from typing import List, Optional
from Ingrediente import Ingrediente
from Stock import Stock
from IMenu import IMenu

@dataclass
class CrearMenu(IMenu):
    nombre: str
    ingredientes: List[Ingrediente]
    precio: float = 0.0
    icono_path: Optional[str] = None
    cantidad: int = 1

    def esta_disponible(self, stock: 'Stock') -> bool:
        for ingrediente_necesario in self.ingredientes:
            encontrado = False
            for ingrediente_stock in stock.lista_ingredientes:
                if ingrediente_necesario.nombre == ingrediente_stock.nombre and ingrediente_necesario.unidad == ingrediente_stock.unidad:
                    if float(ingrediente_stock.cantidad) >= float(ingrediente_necesario.cantidad):
                        encontrado = True
                        break
            if not encontrado:
                return False
        return True

