# Pedido.py,
from typing import List
from IMenu import IMenu # Se mantiene el import del protocolo
from Stock import Stock
from Ingrediente import Ingrediente # Necesario para la resta de stock

class Pedido:

    def __init__(self):
        # La lista 'menus' contiene objetos IMenu (CrearMenu) con su atributo 'cantidad' actualizado
        self.menus: List[IMenu] = [] 

    def agregar_menu(self, menu: IMenu, cantidad: int = 1):
        """Agrega un menú al pedido o aumenta su cantidad."""
        for item in self.menus:
            if item.nombre == menu.nombre:
                item.cantidad += cantidad
                return
        
        # Si no existe, se crea una copia del menú y se le asigna la cantidad
        menu_copia = menu.__class__(menu.nombre, menu.ingredientes, menu.precio, menu.icono_path, cantidad)
        self.menus.append(menu_copia)

    def quitar_menu(self, nombre_menu: str, cantidad: int = 1) -> bool:
        # Quita una cantidad específica de un menú del pedido
        for item in self.menus:
            if item.nombre == nombre_menu:
                if item.cantidad > cantidad:
                    item.cantidad -= cantidad
                else:
                    self.menus.remove(item)
                return True
        return False

    def calcular_total(self) -> float:
        # Calcula el total del pedido sin IVA
        total = sum(menu.precio * menu.cantidad for menu in self.menus)
        return total

    def finalizar_pedido(self, stock: Stock) -> bool:
        # Intenta restar los ingredientes del stock. Si tiene éxito, vacía el pedido.
        
        # Calcular ingredientes totales requeridos
        ingredientes_requeridos: List[Ingrediente] = []
        
        for menu_item in self.menus:
            for req_ing in menu_item.ingredientes:
                cantidad_total_requerida = req_ing.cantidad * menu_item.cantidad
                
                # Buscar si el ingrediente ya fue agregado a la lista de requeridos
                encontrado = False
                for total_req in ingredientes_requeridos:
                    if total_req.nombre == req_ing.nombre and total_req.unidad == req_ing.unidad:
                        total_req.cantidad += cantidad_total_requerida
                        encontrado = True
                        break
                
                if not encontrado:
                    ingredientes_requeridos.append(Ingrediente(
                        nombre=req_ing.nombre, 
                        unidad=req_ing.unidad, 
                        cantidad=cantidad_total_requerida
                    ))

        # Intentar restar los ingredientes del stock (operación atómica)
        if stock.restar_ingredientes(ingredientes_requeridos):
            # Si la resta fue exitosa, vaciar el pedido
            self.menus = []
            return True

        return False