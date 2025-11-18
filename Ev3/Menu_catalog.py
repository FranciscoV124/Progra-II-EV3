# menu_catalog.py
from typing import List
from ElementoMenu import CrearMenu
from Ingrediente import Ingrediente
from IMenu import IMenu

def get_default_menus() -> List[IMenu]:
    return [
        CrearMenu(
            "Completo",
            [
                Ingrediente("Vienesa","unid", 1),
                Ingrediente("Pan de completo","unid", 1),
                Ingrediente("Palta","kg",0.3),
                Ingrediente("Tomate","kg",0.2),
            ],
            precio=1800,
            icono_path="IMG/icono_hotdog_sin_texto_64x64.png",
        ),
        CrearMenu(
            "Chorrillana",
            [
                Ingrediente("Papas", "kg", 0.7),
                Ingrediente("Carne", "kg", 0.4),
                Ingrediente("Carne de vacuno", "kg", 0.3),
                Ingrediente("Cebolla", "kg", 0.1),
                Ingrediente("Huevos", "unid", 2),
            ],
            precio=6000,
            icono_path="IMG/icono_chorrillana_64x64.png",
        ),
        CrearMenu(
            "Pepsi",
            [
                Ingrediente("Pepsi", "unid", 1),
            ],
            precio=1000,
            icono_path="IMG/icono_cola_64x64.png",
        ),
        CrearMenu(
            "Coca Cola",
            [
                Ingrediente("Coca cola", "unid", 1),
            ],
            precio=900,
            icono_path="IMG/icono_cola_lata_64x64.png",
        ),
        CrearMenu(
            "Empanada queso",
            [
                Ingrediente("Masa de empanada", "unid", 1),
                Ingrediente("Queso", "kg", 0.2),
            ],
            precio=1500,
            icono_path="IMG/icono_empanada_queso_64x64.png",
        ),
        CrearMenu(
            "Hamburguesa",
            [
                Ingrediente("Pan de hamburguesa", "unid", 1),
                Ingrediente("Churrasco de carne", "kg", 0.4),
                Ingrediente("Lamina de queso", "unid", 1),
                Ingrediente("Tomate", "kg", 0.2),
            ],
            precio=2500,
            icono_path="IMG/icono_hamburguesa_negra_64x64.png",
        ),
        CrearMenu(
            "Papas fritas",
            [
                Ingrediente("Papas", "kg", 0.3),
            ],
            precio=1800,
            icono_path="IMG/icono_papas_fritas_64x64.png",
        ),
    ]