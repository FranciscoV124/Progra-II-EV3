import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sqlalchemy.orm import Session
from models import Pedido, ItemPedido, Menu, Ingrediente
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from functools import reduce

class GraficosEstadisticos:
    """Clase para generar gráficos estadísticos del sistema de restaurante."""
    
    @staticmethod
    def validar_datos_disponibles(datos: list, mensaje_tipo: str = "datos") -> bool:
        """Verifica si existe información suficiente para generar visualizaciones."""
        if not datos or len(datos) == 0:
            return False
        return True
    
    @staticmethod
    def obtener_ventas_por_fecha(db: Session, periodo: str = "diario") -> Dict[str, float]:
        """Agrupa y suma las ventas por periodos de tiempo especificados.
        
        Soporta agrupación diaria, semanal, mensual y anual de las transacciones.
        """
        try:
            # Obtener todos los pedidos de la base de datos
            pedidos = db.query(Pedido).all()
            
            if not GraficosEstadisticos.validar_datos_disponibles(pedidos):
                return {}
            
            ventas = {}
            
            # Procesar cada pedido para agrupar por periodo
            for pedido in pedidos:
                if not pedido.fecha:
                    continue
                    
                try:
                    fecha = pedido.fecha
                    total = pedido.total
                    
                    # Determinar formato de agrupación según el periodo
                    if periodo == "diario":
                        clave = fecha.strftime("%Y-%m-%d")
                    elif periodo == "semanal":
                        # Calcular número de semana ISO
                        clave = f"{fecha.year}-S{fecha.isocalendar()[1]}"
                    elif periodo == "mensual":
                        clave = fecha.strftime("%Y-%m")
                    elif periodo == "anual":
                        clave = str(fecha.year)
                    else:
                        clave = fecha.strftime("%Y-%m-%d")
                    
                    ventas[clave] = ventas.get(clave, 0.0) + total
                    
                except (ValueError, AttributeError) as e:
                    # Manejar errores de formato en fechas
                    continue
            
            return dict(sorted(ventas.items()))
            
        except Exception as e:
            raise Exception(f"Error al obtener ventas por fecha: {str(e)}")
    
    @staticmethod
    def obtener_distribucion_menus(db: Session) -> Dict[str, int]:
        """Calcula las estadísticas de popularidad de cada elemento del menú."""
        try:
            # Obtener todos los items de pedidos realizados
            items = db.query(ItemPedido).all()
            
            if not GraficosEstadisticos.validar_datos_disponibles(items):
                return {}
            
            # Acumular cantidades por nombre de menú
            distribucion = {}
            for item in items:
                if item.menu and item.menu.nombre:
                    nombre = item.menu.nombre
                    distribucion[nombre] = distribucion.get(nombre, 0) + item.cantidad
            
            # Retornar ordenado por popularidad descendente
            return dict(sorted(distribucion.items(), key=lambda x: x[1], reverse=True))
            
        except Exception as e:
            raise Exception(f"Error al obtener distribución de menús: {str(e)}")
    
    @staticmethod
    def obtener_uso_ingredientes(db: Session) -> Dict[str, float]:
        """Calcula el consumo total de ingredientes en base a las recetas y pedidos."""
        try:
            # Obtener todos los pedidos para calcular consumo
            pedidos = db.query(Pedido).all()
            
            if not GraficosEstadisticos.validar_datos_disponibles(pedidos):
                return {}
            
            uso_ingredientes = {}
            
            # Procesar cada pedido y sus items
            for pedido in pedidos:
                for item in pedido.items:
                    menu = item.menu
                    cantidad_menu = item.cantidad
                    
                    # Calcular ingredientes usados si el menú tiene receta
                    if menu and menu.receta:
                        for ingrediente, cantidad_por_menu in menu.receta.items():
                            try:
                                # Multiplicar receta por cantidad pedida
                                cantidad_total = cantidad_por_menu * cantidad_menu
                                uso_ingredientes[ingrediente] = uso_ingredientes.get(ingrediente, 0.0) + cantidad_total
                            except (ValueError, TypeError):
                                # Omitir ingredientes con formato inválido
                                continue
            
            return dict(sorted(uso_ingredientes.items(), key=lambda x: x[1], reverse=True))
            
        except Exception as e:
            raise Exception(f"Error al calcular uso de ingredientes: {str(e)}")
    
    @staticmethod
    def graficar_ventas_por_fecha(db: Session, periodo: str = "diario", frame=None):
        """Crea visualización de barras para tendencias de ventas temporales."""
        try:
            # Obtener datos de ventas agrupados por periodo
            ventas = GraficosEstadisticos.obtener_ventas_por_fecha(db, periodo)
            
            if not ventas:
                return None, "No hay datos disponibles para mostrar ventas por fecha"
            
            # Configurar figura y ejes del gráfico
            fig, ax = plt.subplots(figsize=(10, 6))
            
            fechas = list(ventas.keys())
            valores = list(ventas.values())
            
            # Crear gráfico de barras con configuración estética
            ax.bar(fechas, valores, color='steelblue')
            ax.set_xlabel('Fecha')
            ax.set_ylabel('Ventas ($)')
            ax.set_title(f'Ventas por {periodo.capitalize()}')
            plt.xticks(rotation=45, ha='right')  # Rotar etiquetas para mejor legibilidad
            plt.tight_layout()
            
            return fig, None
            
        except Exception as e:
            return None, f"Error al generar gráfico: {str(e)}"
    
    @staticmethod
    def graficar_distribucion_menus(db: Session):
        """Genera visualización horizontal de los menús más populares."""
        try:
            # Obtener datos de popularidad de menús
            distribucion = GraficosEstadisticos.obtener_distribucion_menus(db)
            
            if not distribucion:
                return None, "No hay datos disponibles para mostrar distribución de menús"
            
            # Filtrar a los 10 elementos más vendidos para mejor visualización
            top_10 = dict(list(distribucion.items())[:10])
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            menus = list(top_10.keys())
            cantidades = list(top_10.values())
            
            # Crear gráfico de barras horizontales
            ax.barh(menus, cantidades, color='coral')
            ax.set_xlabel('Cantidad Vendida')
            ax.set_ylabel('Menú')
            ax.set_title('Top 10 Menús Más Vendidos')
            plt.tight_layout()
            
            return fig, None
            
        except Exception as e:
            return None, f"Error al generar gráfico: {str(e)}"
    
    @staticmethod
    def graficar_uso_ingredientes(db: Session):
        """Crea gráfico circular mostrando proporción de uso de ingredientes."""
        try:
            # Obtener estadísticas de consumo de ingredientes
            uso = GraficosEstadisticos.obtener_uso_ingredientes(db)
            
            if not uso:
                return None, "No hay datos disponibles para mostrar uso de ingredientes"
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            ingredientes = list(uso.keys())
            cantidades = list(uso.values())
            
            # Optimizar visualización agrupando ingredientes menores
            if len(ingredientes) > 8:
                top_ingredientes = ingredientes[:7]
                top_cantidades = cantidades[:7]
                otros = sum(cantidades[7:])  # Agrupar ingredientes menos usados
                
                top_ingredientes.append('Otros')
                top_cantidades.append(otros)
                
                ingredientes = top_ingredientes
                cantidades = top_cantidades
            
            # Crear gráfico circular con porcentajes
            ax.pie(cantidades, labels=ingredientes, autopct='%1.1f%%', startangle=90)
            ax.set_title('Distribución de Uso de Ingredientes')
            plt.tight_layout()
            
            return fig, None
            
        except Exception as e:
            return None, f"Error al generar gráfico: {str(e)}"
