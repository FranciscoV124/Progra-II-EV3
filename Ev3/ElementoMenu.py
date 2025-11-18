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
                # Comparar normalizando nombres y unidades a la forma del stock
                if stock._normalize_name(ingrediente_necesario.nombre) == stock._normalize_name(ingrediente_stock.nombre) and stock._normalize_unit(ingrediente_necesario.unidad) == stock._normalize_unit(ingrediente_stock.unidad):
                    if float(ingrediente_stock.cantidad) >= float(ingrediente_necesario.cantidad):
                        encontrado = True
                        break
            if not encontrado:
                return False
        return True

