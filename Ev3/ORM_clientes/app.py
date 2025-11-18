# app.py
import customtkinter as ctk
import importlib
import importlib.util
import pathlib
import sys

# Asegurar que la carpeta padre esté en sys.path cuando se ejecuta el script
current_dir = pathlib.Path(__file__).resolve().parent
if current_dir.name == "ORM_clientes":
    parent_dir = str(current_dir.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# Import robusto: intentamos varias formas para soportar ejecución como script
try:
    # Caso habitual cuando el script se ejecuta desde el paquete (misma carpeta)
    from database import get_session, test_connection
except Exception:
    try:
        # Intentar como paquete (si la carpeta se convirtió en paquete)
        from ORM_clientes.database import get_session, test_connection
    except Exception:
        # Fallback: cargar dinámicamente desde el archivo en la misma carpeta
        db_path = pathlib.Path(__file__).resolve().parent / "database.py"
        spec = importlib.util.spec_from_file_location("ORM_clientes.database", str(db_path))
        db = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(db)
        # Registrar el módulo para que "from database import ..." funcione y para import por paquete
        sys.modules["ORM_clientes.database"] = db
        sys.modules["database"] = db
        get_session = getattr(db, "get_session")
        test_connection = getattr(db, "test_connection", lambda: True)

from database import test_connection  # o ORM_clientes.database según import
if not test_connection():
    print("ERROR: No se pudo conectar a la base de datos. Revisa DATABASE_URL y permisos.")
    sys.exit(1)

# CRUD imports — intentar import relativo dentro de la carpeta `crud`,
# y si falla, intentar como `ORM_clientes.crud`.
try:
    from crud.clientes_crud import listar_clientes
    from crud.ingredientes_crud import listar_ingredientes
    from crud.menu_crud import listar_menus
    from crud.pedido_crud import listar_pedidos
except Exception:
    from ORM_clientes.crud.clientes_crud import listar_clientes
    from ORM_clientes.crud.ingredientes_crud import listar_ingredientes
    from ORM_clientes.crud.menu_crud import listar_menus
    from ORM_clientes.crud.pedido_crud import listar_pedidos

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sistema de Gestión Restaurante - EV3")
        self.geometry("1000x600")

        self.session = get_session()

        # Tabview principal
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_clientes = self.tabview.add("Clientes")
        self.tab_ingredientes = self.tabview.add("Ingredientes")
        self.tab_menus = self.tabview.add("Menús")
        self.tab_pedidos = self.tabview.add("Pedidos")
        self.tab_graficos = self.tabview.add("Gráficos")

        self._build_tab_clientes()
        self._build_tab_ingredientes()
        self._build_tab_menus()
        self._build_tab_pedidos()
        self._build_tab_graficos()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- CLIENTES ----------
    def _build_tab_clientes(self):
        label = ctk.CTkLabel(self.tab_clientes, text="Gestión de clientes", font=("Arial", 18, "bold"))
        label.pack(pady=10)

        self.btn_refrescar_clientes = ctk.CTkButton(
            self.tab_clientes, text="Refrescar lista", command=self.refrescar_clientes
        )
        self.btn_refrescar_clientes.pack(pady=5)

        self.text_clientes = ctk.CTkTextbox(self.tab_clientes, width=800, height=400)
        self.text_clientes.pack(pady=10)

    def refrescar_clientes(self):
        self.text_clientes.delete("1.0", "end")
        clientes = listar_clientes(self.session, solo_activos=False)
        for c in clientes:
            self.text_clientes.insert("end", f"{c.id} - {c.nombre} - {c.email} - Activo: {c.activo}\n")

    # ---------- INGREDIENTES ----------
    def _build_tab_ingredientes(self):
        label = ctk.CTkLabel(self.tab_ingredientes, text="Gestión de ingredientes", font=("Arial", 18, "bold"))
        label.pack(pady=10)

        self.btn_refrescar_ing = ctk.CTkButton(
            self.tab_ingredientes, text="Refrescar lista", command=self.refrescar_ingredientes
        )
        self.btn_refrescar_ing.pack(pady=5)

        self.text_ing = ctk.CTkTextbox(self.tab_ingredientes, width=800, height=400)
        self.text_ing.pack(pady=10)

    def refrescar_ingredientes(self):
        self.text_ing.delete("1.0", "end")
        ings = listar_ingredientes(self.session, solo_activos=False)
        for i in ings:
            self.text_ing.insert(
                "end",
                f"{i.id} - {i.nombre} | stock: {i.stock_actual} {i.unidad} | precio: {i.precio_unitario}\n"
            )

    # ---------- MENÚS ----------
    def _build_tab_menus(self):
        label = ctk.CTkLabel(self.tab_menus, text="Gestión de menús", font=("Arial", 18, "bold"))
        label.pack(pady=10)

        self.btn_refrescar_menu = ctk.CTkButton(
            self.tab_menus, text="Refrescar lista", command=self.refrescar_menus
        )
        self.btn_refrescar_menu.pack(pady=5)

        self.text_menu = ctk.CTkTextbox(self.tab_menus, width=800, height=400)
        self.text_menu.pack(pady=10)

    def refrescar_menus(self):
        self.text_menu.delete("1.0", "end")
        menus = listar_menus(self.session, solo_activos=False)
        for m in menus:
            self.text_menu.insert(
                "end",
                f"{m.id} - {m.nombre} | ${m.precio} | Activo: {m.activo}\n"
            )

    # ---------- PEDIDOS ----------
    def _build_tab_pedidos(self):
        label = ctk.CTkLabel(self.tab_pedidos, text="Gestión de pedidos", font=("Arial", 18, "bold"))
        label.pack(pady=10)

        self.btn_refrescar_ped = ctk.CTkButton(
            self.tab_pedidos, text="Refrescar lista", command=self.refrescar_pedidos
        )
        self.btn_refrescar_ped.pack(pady=5)

        self.text_ped = ctk.CTkTextbox(self.tab_pedidos, width=800, height=400)
        self.text_ped.pack(pady=10)

    def refrescar_pedidos(self):
        self.text_ped.delete("1.0", "end")
        pedidos = listar_pedidos(self.session)
        for p in pedidos:
            self.text_ped.insert(
                "end",
                f"{p.id} - Cliente: {p.cliente_id} | Fecha: {p.fecha} | Total: ${p.total} | Estado: {p.estado}\n"
            )

    # ---------- GRÁFICOS ----------
    def _build_tab_graficos(self):
        label = ctk.CTkLabel(self.tab_graficos, text="Gráficos y estadísticas", font=("Arial", 18, "bold"))
        label.pack(pady=10)

        aviso = ctk.CTkLabel(
            self.tab_graficos,
            text="Aquí luego conectaremos los botones para mostrar los gráficos de matplotlib.",
            wraplength=700
        )
        aviso.pack(pady=20)

    def on_close(self):
        # Cerrar sesión de BD
        if self.session:
            self.session.close()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
