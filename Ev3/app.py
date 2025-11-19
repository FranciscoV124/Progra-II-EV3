import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
import json
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from database import get_session, engine, Base
from crud.cliente_crud import ClienteCRUD
from crud.ingrediente_crud import IngredienteCRUD
from crud.menu_crud import MenuCRUD
from crud.pedido_crud import PedidoCRUD
from graficos import GraficosEstadisticos

# Configuración del tema y apariencia de la interfaz gráfica
ctk.set_appearance_mode("System")  # Adaptarse al tema del sistema
ctk.set_default_color_theme("blue")  # Esquema de colores azul

# Inicializar estructura de base de datos
Base.metadata.create_all(bind=engine)
class App(ctk.CTk):
    """Aplicación principal del sistema de gestión de restaurante."""
    
    def __init__(self):
        """Inicializa la ventana principal y todos los módulos de la aplicación."""
        super().__init__()

        # Configuración de ventana principal
        self.title("Sistema de Gestión - Restaurante")
        self.geometry("1024x768")

        # Crear contenedor de pestañas para organización modular
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(pady=20, padx=20, fill="both", expand=True)

        # Inicializar pestañas de funcionalidades
        self.tab_clientes = self.tabview.add("Clientes")
        self.crear_formulario_cliente(self.tab_clientes)

        self.tab_ingredientes = self.tabview.add("Ingredientes")
        self.crear_formulario_ingrediente(self.tab_ingredientes)

        self.tab_menus = self.tabview.add("Menús")
        self.crear_formulario_menu(self.tab_menus)

        self.tab_pedidos = self.tabview.add("Pedidos")
        self.crear_formulario_pedido(self.tab_pedidos)
        
        self.tab_graficos = self.tabview.add("Gráficos")
        self.crear_formulario_graficos(self.tab_graficos)
    # Módulo de gestión de clientes
    def crear_formulario_cliente(self, parent):
        """Crea interfaz completa para gestión de clientes."""
        # Frame superior con campos de entrada
        frame_superior = ctk.CTkFrame(parent)
        frame_superior.pack(pady=10, padx=10, fill="x")

        # Campos de entrada para datos del cliente
        ctk.CTkLabel(frame_superior, text="RUT").grid(row=0, column=0, pady=10, padx=10)
        self.entry_rut = ctk.CTkEntry(frame_superior, width=150)
        self.entry_rut.grid(row=0, column=1, pady=10, padx=10)

        ctk.CTkLabel(frame_superior, text="Nombre").grid(row=0, column=2, pady=10, padx=10)
        self.entry_nombre_cliente = ctk.CTkEntry(frame_superior, width=150)
        self.entry_nombre_cliente.grid(row=0, column=3, pady=10, padx=10)
        
        ctk.CTkLabel(frame_superior, text="Correo").grid(row=0, column=4, pady=10, padx=10)
        self.entry_correo_cliente = ctk.CTkEntry(frame_superior, width=150)
        self.entry_correo_cliente.grid(row=0, column=5, pady=10, padx=10)

        # Botones de operaciones CRUD
        ctk.CTkButton(frame_superior, text="Crear", command=self.crear_cliente).grid(row=1, column=0, pady=10, padx=5)
        ctk.CTkButton(frame_superior, text="Actualizar", command=self.actualizar_cliente).grid(row=1, column=1, pady=10, padx=5)
        ctk.CTkButton(frame_superior, text="Eliminar", command=self.eliminar_cliente).grid(row=1, column=2, pady=10, padx=5)
        ctk.CTkButton(frame_superior, text="Refrescar", command=self.cargar_clientes).grid(row=1, column=3, pady=10, padx=5)

        # Frame inferior para visualización de datos
        frame_inferior = ctk.CTkFrame(parent)
        frame_inferior.pack(pady=10, padx=10, fill="both", expand=True)

        # Tabla para mostrar clientes registrados
        self.treeview_clientes = ttk.Treeview(frame_inferior, columns=("ID", "RUT", "Nombre", "Correo"), show="headings")
        self.treeview_clientes.heading("ID", text="ID")
        self.treeview_clientes.heading("RUT", text="RUT")
        self.treeview_clientes.heading("Nombre", text="Nombre")
        self.treeview_clientes.heading("Correo", text="Correo")
        self.treeview_clientes.column("ID", width=50)
        self.treeview_clientes.column("Correo", width=200)
        self.treeview_clientes.pack(pady=10, padx=10, fill="both", expand=True)

        # Cargar datos iniciales
        self.cargar_clientes()

        self.cargar_clientes()

    def cargar_clientes(self):
        """Actualiza la tabla de clientes con datos de la base de datos."""
        db = next(get_session())
        # Limpiar tabla antes de cargar nuevos datos
        self.treeview_clientes.delete(*self.treeview_clientes.get_children())
        try:
            clientes = ClienteCRUD.obtener_todos_clientes(db)
            # Insertar cada cliente en la tabla
            for cliente in clientes:
                self.treeview_clientes.insert("", "end", values=(cliente.id, cliente.rut, cliente.nombre, cliente.correo or ""))
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar clientes: {e}")
        finally:
            db.close()

    def crear_cliente(self):
        """Procesa la creación de un nuevo cliente con validación de campos."""
        # Obtener datos de los campos de entrada
        rut = self.entry_rut.get().strip()
        nombre = self.entry_nombre_cliente.get().strip()
        correo = self.entry_correo_cliente.get().strip()
        
        if rut and nombre:
            db = next(get_session())
            try:
                ClienteCRUD.crear_cliente(db, rut, nombre, correo if correo else None)
                messagebox.showinfo("Éxito", "Cliente creado correctamente.")
                self.cargar_clientes()  # Actualizar tabla
                # Limpiar campos después de creación exitosa
                self.entry_rut.delete(0, 'end')
                self.entry_nombre_cliente.delete(0, 'end')
                self.entry_correo_cliente.delete(0, 'end')
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                db.close()
        else:
            messagebox.showwarning("Campos Vacíos", "Por favor, ingrese RUT y nombre.")

    def actualizar_cliente(self):
        selected = self.treeview_clientes.selection()
        if not selected:
            messagebox.showwarning("Selección", "Seleccione un cliente.")
            return
        cliente_id = self.treeview_clientes.item(selected)["values"][0]
        rut = self.entry_rut.get().strip()
        nombre = self.entry_nombre_cliente.get().strip()
        correo = self.entry_correo_cliente.get().strip()
        
        db = next(get_session())
        try:
            ClienteCRUD.actualizar_cliente(
                db, cliente_id, 
                rut if rut else None, 
                nombre if nombre else None,
                correo if correo else None
            )
            messagebox.showinfo("Éxito", "Cliente actualizado.")
            self.cargar_clientes()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            db.close()

    def eliminar_cliente(self):
        selected = self.treeview_clientes.selection()
        if not selected:
            messagebox.showwarning("Selección", "Seleccione un cliente.")
            return
        cliente_id = self.treeview_clientes.item(selected)["values"][0]
        db = next(get_session())
        try:
            ClienteCRUD.eliminar_cliente(db, cliente_id)
            messagebox.showinfo("Éxito", "Cliente eliminado.")
            self.cargar_clientes()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            db.close()
    # Módulo de gestión de ingredientes
    def crear_formulario_ingrediente(self, parent):
        """Crea interfaz para gestión de inventario de ingredientes."""
        # Frame para controles de ingredientes
        frame_superior = ctk.CTkFrame(parent)
        frame_superior.pack(pady=10, padx=10, fill="x")

        # Campos para datos de ingrediente
        ctk.CTkLabel(frame_superior, text="Nombre").grid(row=0, column=0, pady=10, padx=10)
        self.entry_nombre_ingrediente = ctk.CTkEntry(frame_superior, width=150)
        self.entry_nombre_ingrediente.grid(row=0, column=1, pady=10, padx=10)

        ctk.CTkLabel(frame_superior, text="Stock").grid(row=0, column=2, pady=10, padx=10)
        self.entry_stock = ctk.CTkEntry(frame_superior, width=100)
        self.entry_stock.grid(row=0, column=3, pady=10, padx=10)

        ctk.CTkLabel(frame_superior, text="Unidad").grid(row=0, column=4, pady=10, padx=10)

        self.combo_unidad = ctk.CTkComboBox(
            frame_superior,
            values=["gramos", "unidades"],
            width=100,
            state="readonly"   # esto bloquea que el usuario escriba
        )
        self.combo_unidad.grid(row=0, column=5, pady=10, padx=10)
        self.combo_unidad.set("gramos")



        ctk.CTkButton(frame_superior, text="Crear", command=self.crear_ingrediente).grid(row=1, column=0, pady=10, padx=5)
        ctk.CTkButton(frame_superior, text="Actualizar", command=self.actualizar_ingrediente).grid(row=1, column=1, pady=10, padx=5)
        ctk.CTkButton(frame_superior, text="Eliminar", command=self.eliminar_ingrediente).grid(row=1, column=2, pady=10, padx=5)
        ctk.CTkButton(frame_superior, text="Refrescar", command=self.cargar_ingredientes).grid(row=1, column=3, pady=10, padx=5)
        # Botón para importación masiva desde archivo CSV
        ctk.CTkButton(frame_superior, text="Cargar CSV", command=self.cargar_csv_ingredientes).grid(row=1, column=4, pady=10, padx=5)

        frame_inferior = ctk.CTkFrame(parent)
        frame_inferior.pack(pady=10, padx=10, fill="both", expand=True)

        self.treeview_ingredientes = ttk.Treeview(frame_inferior, columns=("ID", "Nombre", "Stock", "Unidad"), show="headings")
        self.treeview_ingredientes.heading("ID", text="ID")
        self.treeview_ingredientes.heading("Nombre", text="Nombre")
        self.treeview_ingredientes.heading("Stock", text="Stock")
        self.treeview_ingredientes.heading("Unidad", text="Unidad")
        self.treeview_ingredientes.column("ID", width=50)
        self.treeview_ingredientes.pack(pady=10, padx=10, fill="both", expand=True)

        self.cargar_ingredientes()

    def cargar_ingredientes(self):
        db = next(get_session())
        self.treeview_ingredientes.delete(*self.treeview_ingredientes.get_children())
        try:
            ingredientes = IngredienteCRUD.obtener_todos_ingredientes(db)
            for ing in ingredientes:
                self.treeview_ingredientes.insert("", "end", values=(ing.id, ing.nombre, ing.stock, ing.unidad))
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar ingredientes: {e}")
        finally:
            db.close()

    def crear_ingrediente(self):
        nombre = self.entry_nombre_ingrediente.get().strip()
        stock = self.entry_stock.get().strip()
        unidad = self.combo_unidad.get().strip()

        if nombre and stock and unidad:
            db = next(get_session())
            try:
                IngredienteCRUD.crear_ingrediente(db, nombre, float(stock), unidad)
                messagebox.showinfo("Éxito", "Ingrediente creado.")
                self.cargar_ingredientes()
                # Limpiar campos
                self.entry_nombre_ingrediente.delete(0, 'end')
                self.entry_stock.delete(0, 'end')
                self.combo_unidad.set("gramos")
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                db.close()
        else:
            messagebox.showwarning("Campos Vacíos", "Complete todos los campos.")


    def actualizar_ingrediente(self):
        selected = self.treeview_ingredientes.selection()
        if not selected:
            messagebox.showwarning("Selección", "Seleccione un ingrediente.")
            return

        ing_id = self.treeview_ingredientes.item(selected)["values"][0]
        nombre = self.entry_nombre_ingrediente.get().strip()
        stock = self.entry_stock.get().strip()
        unidad = self.combo_unidad.get().strip()

        db = next(get_session())
        try:
            IngredienteCRUD.actualizar_ingrediente(
                db, ing_id,
                nombre if nombre else None,
                float(stock) if stock else None,
                unidad if unidad else None
            )
            messagebox.showinfo("Éxito", "Ingrediente actualizado.")
            self.cargar_ingredientes()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            db.close()


    def eliminar_ingrediente(self):
        selected = self.treeview_ingredientes.selection()
        if not selected:
            messagebox.showwarning("Selección", "Seleccione un ingrediente.")
            return
        ing_id = self.treeview_ingredientes.item(selected)["values"][0]
        db = next(get_session())
        try:
            IngredienteCRUD.eliminar_ingrediente(db, ing_id)
            messagebox.showinfo("Éxito", "Ingrediente eliminado.")
            self.cargar_ingredientes()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            db.close()

    # Menús
    def crear_formulario_menu(self, parent):
        frame_superior = ctk.CTkFrame(parent)
        frame_superior.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(frame_superior, text="Nombre").grid(row=0, column=0, pady=5, padx=5)
        self.entry_nombre_menu = ctk.CTkEntry(frame_superior, width=150)
        self.entry_nombre_menu.grid(row=0, column=1, pady=5, padx=5)

        ctk.CTkLabel(frame_superior, text="Precio").grid(row=0, column=2, pady=5, padx=5)
        self.entry_precio = ctk.CTkEntry(frame_superior, width=100)
        self.entry_precio.grid(row=0, column=3, pady=5, padx=5)

        ctk.CTkLabel(frame_superior, text="Categoría").grid(row=1, column=0, pady=5, padx=5)
        self.entry_categoria = ctk.CTkEntry(frame_superior, width=150)
        self.entry_categoria.grid(row=1, column=1, pady=5, padx=5)

        ctk.CTkLabel(frame_superior, text="Receta (JSON)").grid(row=2, column=0, pady=5, padx=5)
        self.entry_receta = ctk.CTkEntry(frame_superior, width=400)
        self.entry_receta.grid(row=2, column=1, columnspan=3, pady=5, padx=5)

        ctk.CTkButton(frame_superior, text="Crear", command=self.crear_menu).grid(row=3, column=0, pady=10, padx=5)
        ctk.CTkButton(frame_superior, text="Eliminar", command=self.eliminar_menu).grid(row=3, column=1, pady=10, padx=5)
        ctk.CTkButton(frame_superior, text="Refrescar", command=self.cargar_menus).grid(row=3, column=2, pady=10, padx=5)

        frame_inferior = ctk.CTkFrame(parent)
        frame_inferior.pack(pady=10, padx=10, fill="both", expand=True)

        self.treeview_menus = ttk.Treeview(frame_inferior, columns=("ID", "Nombre", "Precio", "Categoría", "Disponible"), show="headings")
        self.treeview_menus.heading("ID", text="ID")
        self.treeview_menus.heading("Nombre", text="Nombre")
        self.treeview_menus.heading("Precio", text="Precio")
        self.treeview_menus.heading("Categoría", text="Categoría")
        self.treeview_menus.heading("Disponible", text="Disponible")
        self.treeview_menus.column("ID", width=50)
        self.treeview_menus.pack(pady=10, padx=10, fill="both", expand=True)

        self.cargar_menus()

    def cargar_menus(self):
        db = next(get_session())
        self.treeview_menus.delete(*self.treeview_menus.get_children())
        try:
            menus = MenuCRUD.obtener_todos_menus(db)
            for menu in menus:
                disp = "Sí" if menu.disponible else "No"
                self.treeview_menus.insert("", "end", values=(menu.id, menu.nombre, menu.precio, menu.categoria, disp))
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar menús: {e}")
        finally:
            db.close()

    def crear_menu(self):
        nombre = self.entry_nombre_menu.get().strip()
        precio = self.entry_precio.get().strip()
        categoria = self.entry_categoria.get().strip()
        receta_str = self.entry_receta.get().strip()
        
        if nombre and precio:
            db = next(get_session())
            try:
                receta = None
                if receta_str:
                    receta = json.loads(receta_str)  # Convierte string JSON a dict
                
                MenuCRUD.crear_menu(db, nombre, float(precio), categoria, True, receta)
                messagebox.showinfo("Éxito", "Menú creado.")
                self.cargar_menus()
                self.entry_nombre_menu.delete(0, 'end')
                self.entry_precio.delete(0, 'end')
                self.entry_categoria.delete(0, 'end')
                self.entry_descripcion_menu.delete(0, 'end')
                self.entry_receta.delete(0, 'end')
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Formato de receta inválido. Use JSON: {\"ingrediente\": cantidad}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                db.close()
        else:
            messagebox.showwarning("Campos Vacíos", "Ingrese nombre y precio.")

    def eliminar_menu(self):
        selected = self.treeview_menus.selection()
        if not selected:
            messagebox.showwarning("Selección", "Seleccione un menú.")
            return
        menu_id = self.treeview_menus.item(selected)["values"][0]
        db = next(get_session())
        try:
            MenuCRUD.eliminar_menu(db, menu_id)
            messagebox.showinfo("Éxito", "Menú eliminado.")
            self.cargar_menus()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            db.close()

    # Pedidos
        # Pedidos
    def crear_formulario_pedido(self, parent):
        # ---- Frame superior: selección de cliente, menú y cantidad ----
        frame_superior = ctk.CTkFrame(parent)
        frame_superior.pack(pady=10, padx=10, fill="x")

        # Selector de cliente
        ctk.CTkLabel(frame_superior, text="Cliente").grid(row=0, column=0, pady=5, padx=5, sticky="w")
        self.combo_clientes = ctk.CTkComboBox(frame_superior, width=220,state="readonly")
        self.combo_clientes.grid(row=0, column=1, pady=5, padx=5, sticky="w")

        # Selector de menú
        ctk.CTkLabel(frame_superior, text="Menú").grid(row=1, column=0, pady=5, padx=5, sticky="w")
        self.combo_menus = ctk.CTkComboBox(frame_superior, width=260,state="readonly")
        self.combo_menus.grid(row=1, column=1, pady=5, padx=5, sticky="w")

        # Cantidad
        ctk.CTkLabel(frame_superior, text="Cantidad").grid(row=0, column=2, pady=5, padx=5, sticky="w")
        self.entry_cantidad_item = ctk.CTkEntry(frame_superior, width=80)
        self.entry_cantidad_item.grid(row=0, column=3, pady=5, padx=5, sticky="w")
        self.entry_cantidad_item.insert(0, "1")

        # Botones de carrito / listas / pedido
        ctk.CTkButton(
            frame_superior, text="Agregar al carrito",
            command=self.agregar_item_carrito
        ).grid(row=1, column=3, pady=5, padx=5)

        ctk.CTkButton(
            frame_superior, text="Vaciar carrito",
            command=self.vaciar_carrito
        ).grid(row=1, column=4, pady=5, padx=5)

        ctk.CTkButton(
            frame_superior, text="Refrescar listas",
            command=self.cargar_listas_pedido
        ).grid(row=0, column=4, pady=5, padx=5)

        ctk.CTkButton(
            frame_superior, text="Crear Pedido",
            command=self.crear_pedido
        ).grid(row=0, column=5, pady=5, padx=5)

        # ---- Frame medio: carrito de items del pedido ----
        frame_carrito = ctk.CTkFrame(parent)
        frame_carrito.pack(pady=10, padx=10, fill="both", expand=False)

        ctk.CTkLabel(frame_carrito, text="Carrito de productos").pack(anchor="w", padx=10, pady=(5, 0))

        self.treeview_carrito = ttk.Treeview(
            frame_carrito,
            columns=("MenuID", "Nombre", "Cantidad"),
            show="headings",
            height=5
        )
        self.treeview_carrito.heading("MenuID", text="ID Menú")
        self.treeview_carrito.heading("Nombre", text="Nombre")
        self.treeview_carrito.heading("Cantidad", text="Cantidad")

        self.treeview_carrito.column("MenuID", width=80)
        self.treeview_carrito.column("Nombre", width=250)
        self.treeview_carrito.column("Cantidad", width=80)

        self.treeview_carrito.pack(pady=5, padx=10, fill="x")

        # ---- Frame inferior: tabla de pedidos existentes ----
        frame_inferior = ctk.CTkFrame(parent)
        frame_inferior.pack(pady=10, padx=10, fill="both", expand=True)

        self.treeview_pedidos = ttk.Treeview(
            frame_inferior,
            columns=("ID", "Cliente", "Fecha", "Total", "Items"),
            show="headings"
        )
        self.treeview_pedidos.heading("ID", text="ID")
        self.treeview_pedidos.heading("Cliente", text="Cliente")
        self.treeview_pedidos.heading("Fecha", text="Fecha")
        self.treeview_pedidos.heading("Total", text="Total")
        self.treeview_pedidos.heading("Items", text="Items")

        self.treeview_pedidos.column("ID", width=50)
        self.treeview_pedidos.column("Cliente", width=150)
        self.treeview_pedidos.column("Fecha", width=150)
        self.treeview_pedidos.column("Total", width=80)
        self.treeview_pedidos.column("Items", width=100)

        self.treeview_pedidos.pack(pady=10, padx=10, fill="both", expand=True)

        # Carrito en memoria: lista de dicts {menu_id, nombre, cantidad}
        self.carrito_items = []

        # Cargar combos con clientes y menús disponibles
        self.cargar_listas_pedido()
        # Cargar pedidos existentes
        self.cargar_pedidos()

    def cargar_listas_pedido(self):
            """Carga clientes y menús disponibles en los ComboBox."""
            db = next(get_session())
            try:
                # Cargar clientes
                clientes = ClienteCRUD.obtener_todos_clientes(db)
                if clientes:
                    valores_clientes = [f"{c.id} - {c.nombre}" for c in clientes]
                    self.combo_clientes.configure(values=valores_clientes)
                    self.combo_clientes.set(valores_clientes[0])
                else:
                    self.combo_clientes.configure(values=["No hay clientes"])
                    self.combo_clientes.set("No hay clientes")

                # Cargar menús disponibles
                menus = MenuCRUD.obtener_menus_disponibles(db)
                if menus:
                    valores_menus = [f"{m.id} - {m.nombre} (${m.precio})" for m in menus]
                    self.combo_menus.configure(values=valores_menus)
                    self.combo_menus.set(valores_menus[0])
                else:
                    self.combo_menus.configure(values=["No hay menús disponibles"])
                    self.combo_menus.set("No hay menús disponibles")
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar listas: {e}")
            finally:
                db.close()

    def actualizar_treeview_carrito(self):
        """Refresca la tabla visual del carrito con los items actuales."""
        self.treeview_carrito.delete(*self.treeview_carrito.get_children())
        for item in self.carrito_items:
            self.treeview_carrito.insert(
                "", "end",
                values=(item["menu_id"], item["nombre"], item["cantidad"])
            )

    def agregar_item_carrito(self):
        """Agrega el menú seleccionado con la cantidad indicada al carrito."""
        cliente_texto = self.combo_clientes.get()
        menu_texto = self.combo_menus.get()
        cantidad_texto = self.entry_cantidad_item.get().strip()

        # Validar selección de cliente y menú
        if not cliente_texto or "No hay clientes" in cliente_texto:
            messagebox.showwarning("Cliente", "Debe seleccionar un cliente válido.")
            return

        if not menu_texto or "No hay menús" in menu_texto:
            messagebox.showwarning("Menú", "Debe seleccionar un menú válido.")
            return

        # Validar cantidad
        try:
            cantidad = int(cantidad_texto)
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Cantidad", "La cantidad debe ser un número entero mayor que 0.")
            return

        # Obtener ID y nombre de menú desde el texto del ComboBox
        try:
            partes_menu = menu_texto.split("-", 1)
            menu_id = int(partes_menu[0].strip())
            nombre_menu = partes_menu[1].strip()
        except Exception:
            messagebox.showerror("Error", "No se pudo interpretar el menú seleccionado.")
            return

        # Ver si el menú ya está en el carrito -> acumular cantidad
        for item in self.carrito_items:
            if item["menu_id"] == menu_id:
                item["cantidad"] += cantidad
                break
        else:
            # Si no está, lo agregamos nuevo
            self.carrito_items.append({
                "menu_id": menu_id,
                "nombre": nombre_menu,
                "cantidad": cantidad
            })

        # Refrescar tabla visual del carrito
        self.actualizar_treeview_carrito()
        # Resetear cantidad a 1 por comodidad
        self.entry_cantidad_item.delete(0, "end")
        self.entry_cantidad_item.insert(0, "1")

    def vaciar_carrito(self):
        """Elimina todos los items del carrito."""
        self.carrito_items = []
        self.actualizar_treeview_carrito()


    def cargar_pedidos(self):
        """Carga todos los pedidos en la tabla, mostrando la cantidad total de menús."""
        db = next(get_session())
        # Limpiar la tabla
        self.treeview_pedidos.delete(*self.treeview_pedidos.get_children())
        try:
            pedidos = PedidoCRUD.obtener_todos_pedidos(db)
            for pedido in pedidos:
                # Sumar todas las cantidades de los items del pedido
                total_cantidades = sum(item.cantidad for item in pedido.items)
                items_text = f"{total_cantidades} menú(s)"

                self.treeview_pedidos.insert(
                    "", "end",
                    values=(
                        pedido.id,
                        pedido.cliente.nombre,
                        pedido.fecha.strftime("%Y-%m-%d %H:%M"),
                        f"${pedido.total}",
                        items_text
                    )
                )
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar pedidos: {e}")
        finally:
            db.close()


    def crear_pedido(self):
        """Crea un pedido usando el cliente seleccionado y los items del carrito."""
        cliente_texto = self.combo_clientes.get()

        # Validar cliente
        if not cliente_texto or "No hay clientes" in cliente_texto:
            messagebox.showwarning("Cliente", "Debe seleccionar un cliente válido.")
            return

        # Validar que el carrito tenga productos
        if not self.carrito_items:
            messagebox.showwarning("Carrito vacío", "Debe agregar al menos un producto al carrito.")
            return

        # Obtener ID de cliente desde el texto "id - nombre"
        try:
            partes_cliente = cliente_texto.split("-", 1)
            cliente_id = int(partes_cliente[0].strip())
        except Exception:
            messagebox.showerror("Error", "No se pudo interpretar el cliente seleccionado.")
            return

        db = next(get_session())
        try:
            # Adaptar carrito al formato esperado por PedidoCRUD
            items_payload = [
                {"menu_id": item["menu_id"], "cantidad": item["cantidad"]}
                for item in self.carrito_items
            ]

            PedidoCRUD.crear_pedido(db, cliente_id, items_payload)
            messagebox.showinfo("Éxito", "Pedido creado correctamente.")

            # Limpiar carrito y refrescar pedidos
            self.vaciar_carrito()
            self.cargar_pedidos()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            db.close()


    def eliminar_pedido(self):
        selected = self.treeview_pedidos.selection()
        if not selected:
            messagebox.showwarning("Selección", "Seleccione un pedido.")
            return
        pedido_id = self.treeview_pedidos.item(selected)["values"][0]
        db = next(get_session())
        try:
            PedidoCRUD.eliminar_pedido(db, pedido_id)
            messagebox.showinfo("Éxito", "Pedido eliminado.")
            self.cargar_pedidos()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            db.close()
    
    def cargar_csv_ingredientes(self):
        """Permite importar ingredientes masivamente desde archivo CSV."""
        # Diálogo para selección de archivo
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not archivo:
            return
        
        db = next(get_session())
        try:
            # Procesar archivo CSV
            resultados = IngredienteCRUD.cargar_desde_csv(db, archivo)
            
            # Generar mensaje informativo con estadísticas
            mensaje = f"Carga completada:\n"
            mensaje += f" Exitosos: {resultados['exitosos']}\n"
            mensaje += f"  Errores: {resultados['errores']}\n\n"
            
            if resultados['mensajes']:
                mensaje += "Detalles:\n"
                # Mostrar solo los primeros 10 mensajes
                for msg in resultados['mensajes'][:10]:
                    mensaje += f"• {msg}\n"
                if len(resultados['mensajes']) > 10:
                    mensaje += f"... y {len(resultados['mensajes']) - 10} más"
            
            messagebox.showinfo("Carga CSV", mensaje)
            self.cargar_ingredientes()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            db.close()

    def crear_formulario_graficos(self, parent):
        """Crea módulo de visualización de estadísticas y gráficos."""
        # Frame para controles de selección de gráficos
        frame_controles = ctk.CTkFrame(parent)
        frame_controles.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(frame_controles, text="Seleccionar Gráfico:", font=("Arial", 14, "bold")).grid(row=0, column=0, pady=10, padx=10)
        
        # ComboBox con tipos de gráficos disponibles
        self.combo_graficos = ctk.CTkComboBox(
            frame_controles,
            values=["Ventas por Fecha", "Menús Más Vendidos", "Uso de Ingredientes"],
            width=200,
            state="readonly"   # esto bloquea que el usuario escriba
        )
        self.combo_graficos.set("Ventas por Fecha")
        self.combo_graficos.grid(row=0, column=1, pady=10, padx=10)
        
        # Control para selección de periodo temporal
        ctk.CTkLabel(frame_controles, text="Periodo:").grid(row=0, column=2, pady=10, padx=10)
        self.combo_periodo = ctk.CTkComboBox(
            frame_controles,
            values=["diario", "semanal", "mensual", "anual"],
            width=120,
            state="readonly"   
        )
        self.combo_periodo.set("diario")
        self.combo_periodo.grid(row=0, column=3, pady=10, padx=10)
        
        # Botón para ejecutar generación de gráfico
        ctk.CTkButton(
            frame_controles,
            text="Generar Gráfico",
            command=self.generar_grafico
        ).grid(row=0, column=4, pady=10, padx=10)
        
        # Área de visualización de gráficos
        self.frame_grafico = ctk.CTkFrame(parent)
        self.frame_grafico.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Label de información
        self.label_info_grafico = ctk.CTkLabel(
            self.frame_grafico,
            text="Seleccione un tipo de gráfico y presione 'Generar Gráfico'",
            font=("Arial", 12)
        )
        self.label_info_grafico.pack(pady=50)
    
    def generar_grafico(self):
        """Procesa la solicitud de generación y muestra el gráfico correspondiente."""
        # Limpiar área de visualización anterior
        for widget in self.frame_grafico.winfo_children():
            widget.destroy()
        
        tipo_grafico = self.combo_graficos.get()
        db = next(get_session())
        
        try:
            fig = None
            error = None
            
            # Generar gráfico según tipo seleccionado
            if tipo_grafico == "Ventas por Fecha":
                periodo = self.combo_periodo.get()
                fig, error = GraficosEstadisticos.graficar_ventas_por_fecha(db, periodo)
            elif tipo_grafico == "Menús Más Vendidos":
                fig, error = GraficosEstadisticos.graficar_distribucion_menus(db)
            elif tipo_grafico == "Uso de Ingredientes":
                fig, error = GraficosEstadisticos.graficar_uso_ingredientes(db)
            
            # Manejar resultado de generación de gráfico
            if error:
                # Mostrar mensaje de error o falta de datos
                label_error = ctk.CTkLabel(
                    self.frame_grafico,
                    text=error,
                    font=("Arial", 12),
                    text_color="red"
                )
                label_error.pack(pady=50)
            elif fig:
                # Integrar gráfico de matplotlib en la interfaz
                canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)
            else:
                # Mostrar mensaje genérico de error
                label_error = ctk.CTkLabel(
                    self.frame_grafico,
                    text="No se pudo generar el gráfico",
                    font=("Arial", 12)
                )
                label_error.pack(pady=50)
                
        except Exception as e:
            messagebox.showerror("Erreor", f"Error al generar gráfico: {str(e)}")
        finally:
            db.close()

# Punto de entrada de la aplicación
if __name__ == "__main__":
    # Crear e iniciar la aplicación gráfica
    app = App()
    app.mainloop()