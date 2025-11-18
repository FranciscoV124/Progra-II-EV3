from Ingrediente import Ingrediente

class Stock:
    def __init__(self):
        self.lista_ingredientes = []

    @staticmethod
    def _normalize_name(nombre: str) -> str:
        if nombre is None:
            return ""
        return str(nombre).strip().casefold()

    @staticmethod
    def _normalize_unit(unidad: str) -> str:
        if unidad is None:
            return ""
        u = str(unidad).strip().casefold()
        # Map common variants to canonical units
        if u.startswith("kg") or u.startswith("kil"):
            return "kg"
        if u in ("unid", "unidad", "u", "pcs", "p"):
            return "unid"
        return u

    def agregar_ingrediente(self, ingrediente):
        # Si el ingrediente ya existe, suma la cantidad
        # Normalizar nombre y unidad del ingrediente entrante
        nombre_norm = self._normalize_name(ingrediente.nombre)
        unidad_norm = self._normalize_unit(ingrediente.unidad)
        # Actualizar los atributos del objeto para consistencia
        try:
            ingrediente.nombre = nombre_norm
        except Exception:
            ingrediente.nombre = nombre_norm
        try:
            ingrediente.unidad = unidad_norm
        except Exception:
            ingrediente.unidad = unidad_norm

        for ing in self.lista_ingredientes:
            if self._normalize_name(ing.nombre) == nombre_norm and self._normalize_unit(ing.unidad) == unidad_norm:
                ing.cantidad = float(ing.cantidad) + float(ingrediente.cantidad)
                return
        # Si no existe, lo agrega
        self.lista_ingredientes.append(ingrediente)

    def mostrar_stock(self):
        # Devuelve la lista de objetos Ingrediente actuales
        return self.lista_ingredientes

    def eliminar_ingrediente(self, nombre_ingrediente):
        nombre_norm = self._normalize_name(nombre_ingrediente)
        self.lista_ingredientes = [
            ing for ing in self.lista_ingredientes if self._normalize_name(ing.nombre) != nombre_norm
        ]

    def verificar_stock(self):
        return len(self.lista_ingredientes) > 0

    def actualizar_stock(self, nombre_ingrediente, nueva_cantidad):
        nombre_norm = self._normalize_name(nombre_ingrediente)
        for ing in self.lista_ingredientes:
            if self._normalize_name(ing.nombre) == nombre_norm:
                ing.cantidad = nueva_cantidad
                return True
        return False

    def obtener_elementos_menu(self):
        return self.lista_ingredientes

    def restar_ingredientes(self, ingredientes_requeridos):
        # Comprobar disponibilidad
        for req in ingredientes_requeridos:
            encontrado = False
            for ing in self.lista_ingredientes:
                # Comparar nombres y unidades normalizados
                if self._normalize_name(ing.nombre) == self._normalize_name(req.nombre) and self._normalize_unit(ing.unidad) == self._normalize_unit(req.unidad):
                    try:
                        if float(ing.cantidad) >= float(req.cantidad):
                            encontrado = True
                            break
                    except (ValueError, TypeError):
                        # si no se puede convertir a float, consideramos no disponible
                        return False
            if not encontrado:
                return False

        # Descontar los ingredientes (ya que todo está disponible)
        for req in ingredientes_requeridos:
            for ing in self.lista_ingredientes:
                if self._normalize_name(ing.nombre) == self._normalize_name(req.nombre) and self._normalize_unit(ing.unidad) == self._normalize_unit(req.unidad):
                    ing.cantidad = float(ing.cantidad) - float(req.cantidad)
                    # evitar cantidades negativas
                    if ing.cantidad < 0:
                        ing.cantidad = 0.0
                    break

        return True

