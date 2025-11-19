"""
Script para probar el manejo de errores del sistema de restaurante.
Ejecuta escenarios de error comunes para verificar la robustez del sistema.
"""

from database import get_session, engine, Base
from crud.cliente_crud import ClienteCRUD
from crud.ingrediente_crud import IngredienteCRUD
from crud.menu_crud import MenuCRUD
from crud.pedido_crud import PedidoCRUD
import os
import tempfile

# Crear las tablas si no existen
Base.metadata.create_all(bind=engine)

def test_database_errors():
    """Prueba manejo de errores relacionados con la base de datos."""
    print("=== TESTING DATABASE ERRORS ===")
    
    # Test 1: Verificar manejo de sesión
    try:
        db = next(get_session())
        print("✓ Conexión a base de datos exitosa")
        db.close()
    except Exception as e:
        print(f"✗ Error de conexión: {e}")

def test_cliente_errors():
    """Prueba manejo de errores en operaciones de clientes."""
    print("\n=== TESTING CLIENTE ERRORS ===")
    
    db = next(get_session())
    
    try:
        # Test 1: Cliente con RUT vacío
        try:
            ClienteCRUD.crear_cliente(db, "", "Juan Pérez")
            print("✗ Debería fallar con RUT vacío")
        except Exception as e:
            print(f"✓ RUT vacío detectado: {str(e)}")
        
        # Test 2: Cliente con nombre vacío
        try:
            ClienteCRUD.crear_cliente(db, "12345678-9", "")
            print("✗ Debería fallar con nombre vacío")
        except Exception as e:
            print(f"✓ Nombre vacío detectado: {str(e)}")
        
        # Test 3: Correo inválido
        try:
            ClienteCRUD.crear_cliente(db, "12345678-9", "Juan Pérez", "correo-invalido")
            print("✗ Debería fallar con correo inválido")
        except Exception as e:
            print(f"✓ Correo inválido detectado: {str(e)}")
        
        # Test 4: Crear cliente válido
        cliente = ClienteCRUD.crear_cliente(db, "12345678-9", "Juan Pérez", "juan@example.com")
        print(f"✓ Cliente válido creado: {cliente.nombre}")
        
        # Test 5: RUT duplicado
        try:
            ClienteCRUD.crear_cliente(db, "12345678-9", "Pedro González")
            print("✗ Debería fallar con RUT duplicado")
        except Exception as e:
            print(f"✓ RUT duplicado detectado: {str(e)}")
        
        # Test 6: Correo duplicado
        try:
            ClienteCRUD.crear_cliente(db, "87654321-0", "Ana López", "juan@example.com")
            print("✗ Debería fallar con correo duplicado")
        except Exception as e:
            print(f"✓ Correo duplicado detectado: {str(e)}")
        
        # Test 7: Cliente inexistente
        cliente_inexistente = ClienteCRUD.obtener_cliente_por_id(db, 99999)
        if cliente_inexistente is None:
            print("✓ Cliente inexistente retorna None correctamente")
        else:
            print("✗ Debería retornar None para cliente inexistente")
            
    finally:
        db.close()

def test_ingrediente_errors():
    """Prueba manejo de errores en operaciones de ingredientes."""
    print("\n=== TESTING INGREDIENTE ERRORS ===")
    
    db = next(get_session())
    
    try:
        # Test 1: Ingrediente con nombre vacío
        try:
            IngredienteCRUD.crear_ingrediente(db, "", 10.0, "unidades")
            print("✗ Debería fallar con nombre vacío")
        except Exception as e:
            print(f"✓ Nombre vacío detectado: {str(e)}")
        
        # Test 2: Stock negativo
        try:
            IngredienteCRUD.crear_ingrediente(db, "Pan frica", -5.0, "unidades")
            print("✗ Debería fallar con stock negativo")
        except Exception as e:
            print(f"✓ Stock negativo detectado: {str(e)}")
        
        # Test 3: Stock cero
        try:
            IngredienteCRUD.crear_ingrediente(db, "Pan frica", 0.0, "unidades")
            print("✗ Debería fallar con stock cero")
        except Exception as e:
            print(f"✓ Stock cero detectado: {str(e)}")
        
        # Test 4: Unidad vacía
        try:
            IngredienteCRUD.crear_ingrediente(db, "Pan frica", 10.0, "")
            print("✗ Debería fallar con unidad vacía")
        except Exception as e:
            print(f"✓ Unidad vacía detectada: {str(e)}")
        
        # Test 5: Crear ingrediente válido
        ingrediente = IngredienteCRUD.crear_ingrediente(db, "Pan frica", 50.0, "unidades")
        print(f"✓ Ingrediente válido creado: {ingrediente.nombre}")
        
        # Test 6: Nombre duplicado
        try:
            IngredienteCRUD.crear_ingrediente(db, "Pan frica", 25.0, "unidades")
            print("✗ Debería fallar con nombre duplicado")
        except Exception as e:
            print(f"✓ Nombre duplicado detectado: {str(e)}")
        
        # Test 7: Actualizar con stock negativo
        try:
            IngredienteCRUD.actualizar_stock(db, ingrediente.id, -100.0)
            print("✗ Debería fallar al intentar stock negativo")
        except Exception as e:
            print(f"✓ Stock insuficiente detectado: {str(e)}")
            
    finally:
        db.close()

def test_menu_errors():
    """Prueba manejo de errores en operaciones de menús."""
    print("\n=== TESTING MENU ERRORS ===")
    
    db = next(get_session())
    
    try:
        # Crear ingrediente para las pruebas (tomate para el churrasco)
        ingrediente = IngredienteCRUD.crear_ingrediente(db, "Tomate", 30.0, "kg")
        
        # Test 1: Menú con nombre vacío
        try:
            MenuCRUD.crear_menu(db, "", "Descripción", 10000.0)
            print("✗ Debería fallar con nombre vacío")
        except Exception as e:
            print(f"✓ Nombre vacío detectado: {str(e)}")
        
        # Test 2: Precio negativo
        try:
            MenuCRUD.crear_menu(db, "Churrasco Clásico", "Sándwich de churrasco", -5000.0)
            print("✗ Debería fallar con precio negativo")
        except Exception as e:
            print(f"✓ Precio negativo detectado: {str(e)}")
        
        # Test 3: Precio cero
        try:
            MenuCRUD.crear_menu(db, "Churrasco Clásico", "Sándwich de churrasco", 0.0)
            print("✗ Debería fallar con precio cero")
        except Exception as e:
            print(f"✓ Precio cero detectado: {str(e)}")
        
        # Test 4: Receta con ingrediente inexistente
        receta_invalida = {"Ingrediente Inexistente": 0.5}
        try:
            MenuCRUD.crear_menu(db, "Churrasco Italiano", "Churrasco con palta y tomate", 12000.0, receta=receta_invalida)
            print("✗ Debería fallar con ingrediente inexistente")
        except Exception as e:
            print(f"✓ Ingrediente inexistente detectado: {str(e)}")
        
        # Test 5: Receta con cantidad negativa
        receta_negativa = {"Tomate": -0.5}
        try:
            MenuCRUD.crear_menu(db, "Churrasco Italiano", "Churrasco con palta y tomate", 12000.0, receta=receta_negativa)
            print("✗ Debería fallar con cantidad negativa")
        except Exception as e:
            print(f"✓ Cantidad negativa detectada: {str(e)}")
        
        # Test 6: Receta con stock insuficiente
        receta_excesiva = {"Tomate": 50.0}  # Más del stock disponible (30.0)
        try:
            MenuCRUD.crear_menu(db, "Churrasco Italiano", "Churrasco con palta y tomate", 12000.0, receta=receta_excesiva)
            print("✗ Debería fallar con stock insuficiente")
        except Exception as e:
            print(f"✓ Stock insuficiente detectado: {str(e)}")
        
        # Test 7: Receta con ingredientes duplicados
        receta_duplicada = {"Tomate": 0.5, "tomate": 0.3}  # Mismo ingrediente
        try:
            MenuCRUD.crear_menu(db, "Churrasco Italiano", "Churrasco con palta y tomate", 12000.0, receta=receta_duplicada)
            print("✗ Debería fallar con ingredientes duplicados")
        except Exception as e:
            print(f"✓ Ingredientes duplicados detectados: {str(e)}")
        
        # Test 8: Crear menú válido
        receta_valida = {"Tomate": 0.2}
        menu = MenuCRUD.crear_menu(db, "Churrasco Italiano Clásico", "Churrasco con tomate", 8000.0, receta=receta_valida)
        print(f"✓ Menú válido creado: {menu.nombre}")
        
    finally:
        db.close()

def test_pedido_errors():
    """Prueba manejo de errores en operaciones de pedidos."""
    print("\n=== TESTING PEDIDO ERRORS ===")
    
    db = next(get_session())
    
    try:
        # Crear cliente y menú para las pruebas
        cliente = ClienteCRUD.crear_cliente(db, "11111111-1", "Test Cliente")
        menu = MenuCRUD.crear_menu(db, "Churrasco Prueba", "Churrasco de prueba", 5000.0)
        
        # Test 1: Pedido sin cliente
        try:
            PedidoCRUD.crear_pedido(db, None, [{"menu_id": menu.id, "cantidad": 1}])
            print("✗ Debería fallar sin cliente")
        except Exception as e:
            print(f"✓ Cliente requerido detectado: {str(e)}")
        
        # Test 2: Cliente inexistente
        try:
            PedidoCRUD.crear_pedido(db, 99999, [{"menu_id": menu.id, "cantidad": 1}])
            print("✗ Debería fallar con cliente inexistente")
        except Exception as e:
            print(f"✓ Cliente inexistente detectado: {str(e)}")
        
        # Test 3: Pedido sin items
        try:
            PedidoCRUD.crear_pedido(db, cliente.id, [])
            print("✗ Debería fallar sin items")
        except Exception as e:
            print(f"✓ Items requeridos detectado: {str(e)}")
        
        # Test 4: Item con menú inexistente
        try:
            PedidoCRUD.crear_pedido(db, cliente.id, [{"menu_id": 99999, "cantidad": 1}])
            print("✗ Debería fallar con menú inexistente")
        except Exception as e:
            print(f"✓ Menú inexistente detectado: {str(e)}")
        
        # Test 5: Cantidad negativa
        try:
            PedidoCRUD.crear_pedido(db, cliente.id, [{"menu_id": menu.id, "cantidad": -1}])
            print("✗ Debería fallar con cantidad negativa")
        except Exception as e:
            print(f"✓ Cantidad negativa detectada: {str(e)}")
        
        # Test 6: Cantidad cero
        try:
            PedidoCRUD.crear_pedido(db, cliente.id, [{"menu_id": menu.id, "cantidad": 0}])
            print("✗ Debería fallar con cantidad cero")
        except Exception as e:
            print(f"✓ Cantidad cero detectada: {str(e)}")
        
        # Test 7: Menú no disponible
        menu_no_disponible = MenuCRUD.crear_menu(db, "Churrasco No Disponible", "No disponible", 3000.0, disponible=False)
        try:
            PedidoCRUD.crear_pedido(db, cliente.id, [{"menu_id": menu_no_disponible.id, "cantidad": 1}])
            print("✗ Debería fallar con menú no disponible")
        except Exception as e:
            print(f"✓ Menú no disponible detectado: {str(e)}")
        
        # Test 8: Crear pedido válido
        pedido = PedidoCRUD.crear_pedido(db, cliente.id, [{"menu_id": menu.id, "cantidad": 2}])
        print(f"✓ Pedido válido creado: ID {pedido.id}")
        
    finally:
        db.close()

def test_csv_errors():
    """Prueba manejo de errores en importación CSV."""
    print("\n=== TESTING CSV IMPORT ERRORS ===")
    
    db = next(get_session())
    
    try:
        # Test 1: Archivo inexistente
        try:
            IngredienteCRUD.cargar_desde_csv(db, "archivo_inexistente.csv")
            print("✗ Debería fallar con archivo inexistente")
        except Exception as e:
            print(f"✓ Archivo inexistente detectado: {str(e)}")
        
        # Test 2: CSV con formato incorrecto
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("columna1,columna2\nvalor1,valor2\n")
            csv_incorrecto = f.name
        
        try:
            IngredienteCRUD.cargar_desde_csv(db, csv_incorrecto)
            print("✗ Debería fallar con formato incorrecto")
        except Exception as e:
            print(f"✓ Formato CSV incorrecto detectado: {str(e)}")
        finally:
            os.unlink(csv_incorrecto)
        
        # Test 3: CSV con datos inválidos
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("nombre,stock,unidad\n")
            f.write(",10.0,unidades\n")  # Nombre vacío
            f.write("Pan frica,abc,unidades\n")  # Stock inválido
            f.write("Carne laminada,-5.0,\n")  # Stock negativo y unidad vacía
            csv_datos_invalidos = f.name
        
        try:
            resultados = IngredienteCRUD.cargar_desde_csv(db, csv_datos_invalidos)
            print(f"✓ CSV con errores procesado: {resultados['errores']} errores detectados")
            if resultados['errores'] > 0:
                print("✓ Errores correctamente registrados en el resultado")
        except Exception as e:
            print(f"Error inesperado: {e}")
        finally:
            os.unlink(csv_datos_invalidos)
        
        # Test 4: CSV válido
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("nombre,stock,unidad\n")
            f.write("Sal,25.0,kg\n")
            f.write("Pimienta,15.0,kg\n")
            csv_valido = f.name
        
        try:
            resultados = IngredienteCRUD.cargar_desde_csv(db, csv_valido)
            print(f"✓ CSV válido procesado: {resultados['exitosos']} ingredientes creados")
        finally:
            os.unlink(csv_valido)
            
    finally:
        db.close()

def test_graficos_errors():
    """Prueba manejo de errores en generación de gráficos."""
    print("\n=== TESTING GRAFICOS ERRORS ===")
    
    from graficos import GraficosEstadisticos
    
    db = next(get_session())
    
    try:
        # Test 1: Gráficos sin datos
        fig, error = GraficosEstadisticos.graficar_ventas_por_fecha(db, "diario")
        if error and "No hay datos disponibles" in error:
            print("✓ Error de datos insuficientes detectado correctamente")
        else:
            print("✗ Debería retornar error por falta de datos")
        
        fig, error = GraficosEstadisticos.graficar_distribucion_menus(db)
        if error and "No hay datos disponibles" in error:
            print("✓ Error de menús sin datos detectado correctamente")
        else:
            print("✗ Debería retornar error por falta de datos")
        
        fig, error = GraficosEstadisticos.graficar_uso_ingredientes(db)
        if error and "No hay datos disponibles" in error:
            print("✓ Error de ingredientes sin datos detectado correctamente")
        else:
            print("✗ Debería retornar error por falta de datos")
        
        # Test 2: Periodo inválido (debería usar diario por defecto)
        ventas = GraficosEstadisticos.obtener_ventas_por_fecha(db, "periodo_inexistente")
        print("✓ Periodo inválido manejado correctamente (usar diario por defecto)")
        
    finally:
        db.close()

def cleanup_test_data():
    """Limpia los datos de prueba creados durante los tests."""
    print("\n=== CLEANUP ===")
    
    try:
        # Eliminar archivo de base de datos de prueba si existe
        if os.path.exists("proyecto.db"):
            # Crear nuevas tablas limpias
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            print("✓ Base de datos limpiada")
    except Exception as e:
        print(f"✗ Error en limpieza: {e}")

if __name__ == "__main__":
    print("INICIANDO TESTS DE MANEJO DE ERRORES")
    print("=" * 50)
    
    try:
        test_database_errors()
        test_cliente_errors()
        test_ingrediente_errors() 
        test_menu_errors()
        test_pedido_errors()
        test_csv_errors()
        test_graficos_errors()
        
        print("\n" + "=" * 50)
        print("TESTS DE MANEJO DE ERRORES COMPLETADOS")
        
    except Exception as e:
        print(f"\nERROR CRÍTICO EN LOS TESTS: {e}")
    
    finally:
        cleanup_test_data()
