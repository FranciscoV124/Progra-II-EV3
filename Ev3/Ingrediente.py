# Ingrediente.py
from dataclasses import dataclass
from typing import Optional

@dataclass(eq=True, frozen=False)
class Ingrediente:
    nombre: str
    unidad: Optional[float]  
    cantidad: float          

    def __post_init__(self):
        try:
            self.cantidad = float(self.cantidad)
        except (ValueError, TypeError):
            self.cantidad = 0.0

    def __str__(self):
        # Mostrar la cantidad con un decimal para conservar formatos como 15.0
        try:
            cantidad_formateada = f"{float(self.cantidad):.1f}"
        except (ValueError, TypeError):
            cantidad_formateada = str(self.cantidad)

        if self.unidad:
            return f"{self.nombre} ({self.unidad}) x {cantidad_formateada}"
        return f"{self.nombre} x {cantidad_formateada}"