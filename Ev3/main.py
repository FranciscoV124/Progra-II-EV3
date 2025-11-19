from database import get_session, engine, Base
from crud.cliente_crud import ClienteCRUD
from crud.ingrediente_crud import IngredienteCRUD
from crud.menu_crud import MenuCRUD
from crud.pedido_crud import PedidoCRUD

# Inicialización de la estructura de base de datos
Base.metadata.create_all(bind=engine)

def main():
    """Función principal que demuestra el uso completo del sistema CRUD."""
    # Establecer sesión de base de datos
    db = next(get_session())

    try:
        # Demostración de creación de clientes
        print("=== CREANDO CLIENTES ===")
        cliente1 = ClienteCRUD.crear_cliente(db, rut="12345678-9", nombre="Jose Mardones")
        print(f"Cliente creado: {cliente1.nombre} - RUT: {cliente1.rut}")
        
        # Demostración de gestión de ingredientes
        print("\n=== CREANDO INGREDIENTES PARA CHURRASCOS ===")
        pan = IngredienteCRUD.crear_ingrediente(db, nombre="Pan", stock=100.0, unidad="unidades")
        carne = IngredienteCRUD.crear_ingrediente(db, nombre="Carne", stock=5000.0, unidad="gramos")
        tomate = IngredienteCRUD.crear_ingrediente(db, nombre="Tomate", stock=1500.0, unidad="gramos")
        palta = IngredienteCRUD.crear_ingrediente(db, nombre="Palta", stock=1200.0, unidad="gramos")
        mayonesa = IngredienteCRUD.crear_ingrediente(db, nombre="Mayonesa", stock=800.0, unidad="gramos")
        print(f"Ingredientes creados: {pan.nombre}, {carne.nombre}, {tomate.nombre}, {palta.nombre}, {mayonesa.nombre}")
        
        # Demostración de creación de menús con recetas
        print("\n=== CREANDO MENÚS DE CHURRASCOS ===")
        # Definición de receta con cantidades por porción
        receta_churrasco_italiano = {
            "Pan": 1,
            "Carne": 150.0,
            "Tomate": 30.0,
            "Palta": 40.0,
            "Mayonesa": 20.0
        }
        churrasco_italiano = MenuCRUD.crear_menu(
            db, 
            nombre="Churrasco Italiano",
            descripcion="Churrasco con tomate, palta y mayonesa",
            precio=5500.0,
            categoria="Churrascos",
            disponible=True,
            receta=receta_churrasco_italiano
        )
        print(f"Menú creado: {churrasco_italiano.nombre} - ${churrasco_italiano.precio}")
        
        bebida = MenuCRUD.crear_menu(
            db,
            nombre="Bebida en lata",
            descripcion="350 ml surtida",
            precio=1500.0,
            categoria="Bebidas",
            disponible=True,
            receta=None
        )
        print(f"Menú creado: {bebida.nombre} - ${bebida.precio}")
        
        # Demostración de sistema de pedidos
        print("\n=== CREANDO PEDIDO DE CHURRASCOS ===")
        # Creación de pedido con múltiples elementos del menú
        pedido = PedidoCRUD.crear_pedido(
            db, 
            cliente_id=cliente1.id,
            items=[
                {"menu_id": churrasco_italiano.id, "cantidad": 2},
                {"menu_id": bebida.id, "cantidad": 1}
            ]
        )
        print(f"Pedido creado: ID {pedido.id}")
        print(f"Items en el pedido:")
        # Mostrar desglose del pedido
        for item in pedido.items:
            print(f"  - {item.cantidad}x {item.menu.nombre} (${item.subtotal})")
        print(f"Total del pedido: ${pedido.total}")
        
        # Demostración de consultas y listados
        print("\n=== TODOS LOS CLIENTES ===")
        clientes = ClienteCRUD.obtener_todos_clientes(db)
        for c in clientes:
            print(f"- {c.nombre} (RUT: {c.rut})")
        
        # Listado de menús activos
        print("\n=== MENÚS DISPONIBLES ===")
        menus = MenuCRUD.obtener_menus_disponibles(db)
        for m in menus:
            print(f"- {m.nombre} - ${m.precio} ({m.categoria})")
        
        print("\n¡Operaciones de churrasquería completadas exitosamente!")
        
    except Exception as e:
        # Manejo centralizado de errores del sistema
        print(f"\nError: {e}")
    finally:
        # Garantizar cierre de sesión de base de datos
        db.close()

if __name__ == "__main__":
    main()
