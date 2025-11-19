from ElementoMenu import CrearMenu
import customtkinter as ctk
from tkinter import ttk, Toplevel
from Ingrediente import Ingrediente
from Stock import Stock
import re
from PIL import Image
from CTkMessagebox import CTkMessagebox
from Pedido import Pedido
from BoletaFacade import BoletaFacade
from tkinter import filedialog
from Menu_catalog import get_default_menus
from menu_pdf import create_menu_pdf
from ctk_pdf_viewer import CTkPDFViewer
import os
from tkinter.font import nametofont
import sys
import pathlib
import traceback
import sqlite3
from datetime import datetime
from sqlalchemy import func

# -------------------------------------------------------------------
# ORM / CRUD + modelos
# -------------------------------------------------------------------
try:
    from ORM_clientes.database import get_session, test_connection
    from ORM_clientes.crud.ingredientes_crud import (
        cargar_ingredientes_desde_csv,
        crear_ingrediente,
        listar_ingredientes,
    )
    from ORM_clientes.crud.clientes_crud import listar_clientes
    from ORM_clientes.crud.menu_crud import listar_menus
    from ORM_clientes.crud.pedido_crud import listar_pedidos
except Exception as e:
    print("ERROR: no se pudieron importar los módulos ORM desde 'ORM_clientes'.")
    traceback.print_exc()
    raise

try:
    from ORM_clientes.models import Ingrediente as IngredienteModel
    from ORM_clientes.models import Menu as MenuModel
    from ORM_clientes.models import Pedido as PedidoModel
    from ORM_clientes.models import PedidoDetalle as PedidoDetalleModel
except Exception:
    IngredienteModel = None
    MenuModel = None
    PedidoModel = None
    PedidoDetalleModel = None

# Graficos (pestaña Gráficos)
try:
    from ORM_clientes import graficos as graficos_mod
except Exception:
    graficos_mod = None

# -------------------------------------------------------------------
# Preparar rutas / DB / migración
# -------------------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB = ROOT / "restaurante.db"

if not DB.exists():
    print(f"No se encontró {DB}. Ejecuta desde la raíz del proyecto.")
    sys.exit(1)

bak = ROOT / "restaurante.db.bak"
print(f"Haciendo backup: {bak}")
with open(DB, "rb") as r, open(bak, "wb") as w:
    w.write(r.read())

conn = sqlite3.connect(str(DB))
cur = conn.cursor()


def has_col(table, col):
    cur.execute(f"PRAGMA table_info('{table}')")
    return col in [r[1] for r in cur.fetchall()]


changed = False
if not has_col("ingredientes", "created_at"):
    print("Agregando columna created_at ...")
    cur.execute(
        "ALTER TABLE ingredientes "
        "ADD COLUMN created_at DATETIME DEFAULT (CURRENT_TIMESTAMP)"
    )
    changed = True
if not has_col("ingredientes", "updated_at"):
    print("Agregando columna updated_at ...")
    cur.execute(
        "ALTER TABLE ingredientes "
        "ADD COLUMN updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP)"
    )
    changed = True

if changed:
    conn.commit()
    print("Migración completada.")
else:
    print("No se requirió migración (columnas ya presentes).")

cur.close()
conn.close()

# -------------------------------------------------------------------
# Aplicación
# -------------------------------------------------------------------
class AplicacionConPestanas(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gestión de ingredientes y pedidos")
        self.geometry("870x700")
        nametofont("TkHeadingFont").configure(size=14)
        nametofont("TkDefaultFont").configure(size=11)

        self.stock = Stock()
        self.menus_creados = set()
        self.pedido = Pedido()
        self.menus = get_default_menus()

        # Cliente seleccionado para el pedido actual
        self.cliente_seleccionado = None
        self._clientes_cache = []

        self.tabview = ctk.CTkTabview(self, command=self.on_tab_change)
        self.tabview.pack(expand=True, fill="both", padx=10, pady=10)

        # Sesión compartida para operaciones CRUD (cerrar en on_close)
        try:
            self.session = get_session()
        except Exception:
            self.session = None

        self.crear_pestanas()

        # Cargar stock inicial desde la BD (para que persista entre ejecuciones)
        self._cargar_stock_desde_bd()
        self.actualizar_treeview()

        # Cerrar sesión al salir
        try:
            self.protocol("WM_DELETE_WINDOW", self.on_close)
        except Exception:
            pass

    # ---------- CLIENTES (desde app.py) ----------
    def _build_tab_clientes(self):
        frame = ctk.CTkFrame(self.tab_clientes)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        label = ctk.CTkLabel(frame, text="Gestión de Clientes (ORM)")
        label.pack(pady=10)

        self.txt_clientes = ctk.CTkTextbox(frame, width=700, height=350)
        self.txt_clientes.pack(expand=True, fill="both", padx=10, pady=10)

        btn_refrescar = ctk.CTkButton(
            frame,
            text="Listar clientes",
            command=self.refrescar_clientes_tab,
        )
        btn_refrescar.pack(pady=5)

    def refrescar_clientes_tab(self):
        """Usa listar_clientes y muestra en la pestaña Clientes."""
        try:
            sess = self.session or get_session()
            clientes = listar_clientes(sess, solo_activos=False)
            self.txt_clientes.delete("1.0", "end")
            for c in clientes:
                self.txt_clientes.insert(
                    "end",
                    f"{c.id} - {c.nombre} - {getattr(c, 'email', '')} - Activo: {c.activo}\n",
                )
        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"No se pudo obtener lista de clientes:\n{e}",
                icon="warning",
            )

    # ---------- INGREDIENTES (ORM) ----------
    def _build_tab_ingredientes_orm(self):
        frame = ctk.CTkFrame(self.tab_ing_orm)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        label = ctk.CTkLabel(frame, text="Ingredientes en BD (ORM)")
        label.pack(pady=10)

        self.txt_ing_orm = ctk.CTkTextbox(frame, width=700, height=350)
        self.txt_ing_orm.pack(expand=True, fill="both", padx=10, pady=10)

        btn_refrescar = ctk.CTkButton(
            frame, text="Listar ingredientes", command=self.refrescar_ingredientes_tab
        )
        btn_refrescar.pack(pady=5)

    def refrescar_ingredientes_tab(self):
        try:
            sess = self.session or get_session()
            ings = listar_ingredientes(sess, solo_activos=False)
            self.txt_ing_orm.delete("1.0", "end")
            for i in ings:
                self.txt_ing_orm.insert(
                    "end",
                    f"{i.id} - {i.nombre} | stock: {i.stock_actual} {i.unidad} | precio: {i.precio_unitario}\n",
                )
        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"No se pudo obtener lista de ingredientes:\n{e}",
                icon="warning",
            )

    # ---------- MENÚS (ORM) ----------
    def _build_tab_menus_orm(self):
        frame = ctk.CTkFrame(self.tab_menus_orm)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        label = ctk.CTkLabel(frame, text="Menús en BD (ORM)")
        label.pack(pady=10)

        self.txt_menus_orm = ctk.CTkTextbox(frame, width=700, height=350)
        self.txt_menus_orm.pack(expand=True, fill="both", padx=10, pady=10)

        btn_refrescar = ctk.CTkButton(
            frame, text="Listar menús", command=self.refrescar_menus_tab
        )
        btn_refrescar.pack(pady=5)

    def refrescar_menus_tab(self):
        try:
            sess = self.session or get_session()
            menus = listar_menus(sess, solo_activos=False)
            self.txt_menus_orm.delete("1.0", "end")
            for m in menus:
                self.txt_menus_orm.insert(
                    "end",
                    f"{m.id} - {m.nombre} | ${m.precio} | Activo: {m.activo}\n",
                )
        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"No se pudo obtener lista de menús:\n{e}",
                icon="warning",
            )

    # ---------- PEDIDOS (ORM) ----------
    def _build_tab_pedidos_orm(self):
        frame = ctk.CTkFrame(self.tab_pedidos_orm)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        label = ctk.CTkLabel(frame, text="Pedidos en BD (ORM)")
        label.pack(pady=10)

        self.txt_pedidos_orm = ctk.CTkTextbox(frame, width=700, height=350)
        self.txt_pedidos_orm.pack(expand=True, fill="both", padx=10, pady=10)

        btn_refrescar = ctk.CTkButton(
            frame, text="Listar pedidos", command=self.refrescar_pedidos_tab
        )
        btn_refrescar.pack(pady=5)

    def refrescar_pedidos_tab(self):
        try:
            sess = self.session or get_session()
            pedidos = listar_pedidos(sess)
            self.txt_pedidos_orm.delete("1.0", "end")
            for p in pedidos:
                self.txt_pedidos_orm.insert(
                    "end",
                    f"{p.id} - Cliente: {p.cliente_id} | Fecha: {p.fecha} "
                    f"| Total: ${p.total} | Estado: {p.estado}\n",
                )
        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"No se pudo obtener lista de pedidos:\n{e}",
                icon="warning",
            )

    # ---------- GRÁFICOS ----------
    def _build_tab_graficos(self):
        frame = ctk.CTkFrame(self.tab_graficos)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        label = ctk.CTkLabel(frame, text="Gráficos de Ventas / Pedidos")
        label.pack(pady=10)

        if graficos_mod is None:
            msg = "Módulo 'graficos' no disponible. Revisa imports."
            ctk.CTkLabel(frame, text=msg, text_color="red").pack(pady=10)
            return

        btn_ventas_fecha = ctk.CTkButton(
            frame, text="Ventas por fecha", command=self._grafico_ventas_por_fecha
        )
        btn_ventas_fecha.pack(pady=5)

        btn_mas_pedidos = ctk.CTkButton(
            frame, text="Menús más pedidos", command=self._grafico_menus_mas_pedidos
        )
        btn_mas_pedidos.pack(pady=5)

        # Ejemplo visible de map / filter / reduce + lambda sobre el stock
        btn_resumen_stock = ctk.CTkButton(
            frame,
            text="Resumen de stock (map/filter/reduce)",
            command=self._resumen_stock_funcional,
        )
        btn_resumen_stock.pack(pady=15)

    def _grafico_ventas_por_fecha(self):
        try:
            sess = self.session or get_session()
            graficos_mod.grafico_ventas_por_fecha(sess)
        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"No se pudo generar gráfico de ventas:\n{e}",
                icon="warning",
            )

    def _grafico_menus_mas_pedidos(self):
        try:
            sess = self.session or get_session()
            graficos_mod.grafico_menus_mas_pedidos(sess)
        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"No se pudo generar gráfico de menús:\n{e}",
                icon="warning",
            )

    def _resumen_stock_funcional(self):
        """Ejemplo explícito de map / filter / reduce + lambda sobre el stock."""
        from functools import reduce

        cantidades = list(
            map(
                lambda ing: float(getattr(ing, "cantidad", 0.0) or 0.0),
                self.stock.lista_ingredientes,
            )
        )
        total_stock = reduce(lambda acc, x: acc + x, cantidades, 0.0)

        bajos = list(
            filter(
                lambda ing: float(getattr(ing, "cantidad", 0.0) or 0.0) < 1.0,
                self.stock.lista_ingredientes,
            )
        )
        nombres_bajos = ", ".join(ing.nombre for ing in bajos) if bajos else "Ninguno"

        CTkMessagebox(
            title="Resumen de Stock",
            message=(
                f"Total de unidades (map+reduce): {total_stock:.2f}\n"
                f"Ingredientes con stock < 1 (filter+lambda): {nombres_bajos}"
            ),
            icon="info",
        )

    # ------------------------------------------------------------------
    # Gestión de cierre
    # ------------------------------------------------------------------
    def on_close(self):
        """Cerrar sesión de BD y destruir ventana."""
        try:
            if getattr(self, "session", None):
                try:
                    self.session.close()
                except Exception:
                    pass
        finally:
            try:
                self.destroy()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Carga inicial de stock desde BD
    # ------------------------------------------------------------------
    def _cargar_stock_desde_bd(self):
        """Cargar ingredientes desde la BD al objeto Stock al iniciar la app."""
        if IngredienteModel is None:
            return
        session = None
        try:
            session = get_session()
            db_ings = listar_ingredientes(session, solo_activos=True)
            nueva_lista = []
            for ing in db_ings:
                try:
                    cant = float(getattr(ing, "stock_actual", 0.0) or 0.0)
                except Exception:
                    cant = 0.0
                nueva_lista.append(
                    Ingrediente(
                        nombre=ing.nombre,
                        unidad=getattr(ing, "unidad", "unid"),
                        cantidad=cant,
                    )
                )
            self.stock.lista_ingredientes = nueva_lista
        except Exception as e:
            print("Advertencia: no se pudo cargar stock inicial desde BD:", e)
        finally:
            if session:
                session.close()

    # ------------------------------------------------------------------
    # Ventanas auxiliares de listados (emergentes)
    # ------------------------------------------------------------------
    def refrescar_clientes(self):
        try:
            sess = self.session or get_session()
            clientes = listar_clientes(sess, solo_activos=False)
            win = Toplevel(self)
            win.title("Clientes")
            text = ctk.CTkTextbox(win, width=700, height=400)
            text.pack(expand=True, fill="both", padx=10, pady=10)
            for c in clientes:
                text.insert(
                    "end",
                    f"{c.id} - {c.nombre} - {getattr(c,'email', '')} - Activo: {c.activo}\n",
                )
        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"No se pudo obtener lista de clientes:\n{e}",
                icon="warning",
            )

    def refrescar_ingredientes(self):
        try:
            sess = self.session or get_session()
            ings = listar_ingredientes(sess, solo_activos=False)
            win = Toplevel(self)
            win.title("Ingredientes")
            text = ctk.CTkTextbox(win, width=700, height=400)
            text.pack(expand=True, fill="both", padx=10, pady=10)
            for i in ings:
                text.insert(
                    "end",
                    f"{i.id} - {i.nombre} | stock: {i.stock_actual} {i.unidad} "
                    f"| precio: {i.precio_unitario}\n",
                )
        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"No se pudo obtener lista de ingredientes:\n{e}",
                icon="warning",
            )

    def refrescar_menus(self):
        try:
            sess = self.session or get_session()
            menus = listar_menus(sess, solo_activos=False)
            win = Toplevel(self)
            win.title("Menús")
            text = ctk.CTkTextbox(win, width=700, height=400)
            text.pack(expand=True, fill="both", padx=10, pady=10)
            for m in menus:
                text.insert(
                    "end",
                    f"{m.id} - {m.nombre} | ${m.precio} | Activo: {m.activo}\n",
                )
        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"No se pudo obtener lista de menús:\n{e}",
                icon="warning",
            )

    def refrescar_pedidos(self):
        try:
            sess = self.session or get_session()
            pedidos = listar_pedidos(sess)
            win = Toplevel(self)
            win.title("Pedidos")
            text = ctk.CTkTextbox(win, width=700, height=400)
            text.pack(expand=True, fill="both", padx=10, pady=10)
            for p in pedidos:
                text.insert(
                    "end",
                    f"{p.id} - Cliente: {p.cliente_id} | Fecha: {p.fecha} "
                    f"| Total: ${p.total} | Estado: {p.estado}\n",
                )
        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"No se pudo obtener lista de pedidos:\n{e}",
                icon="warning",
            )

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------
    def on_tab_change(self):
        selected_tab = self.tabview.get()
        if selected_tab in ("Stock", "Pedido", "Carta restorante", "Boleta"):
            self.actualizar_treeview()

    def crear_pestanas(self):
        # Pestañas originales
        self.tab3 = self.tabview.add("Carga de CSV")
        self.tab1 = self.tabview.add("Stock")
        self.tab4 = self.tabview.add("Carta restorante")
        self.tab2 = self.tabview.add("Pedido")
        self.tab5 = self.tabview.add("Boleta")

        self.configurar_pestana1()
        self.configurar_pestana2()
        self.configurar_pestana3()
        self._configurar_pestana_crear_menu()
        self._configurar_pestana_ver_boleta()

        # Nuevas pestañas ORM / Gráficos
        self.tab_clientes = self.tabview.add("Clientes")
        self.tab_ing_orm = self.tabview.add("Ingredientes")
        self.tab_menus_orm = self.tabview.add("Menús")
        self.tab_pedidos_orm = self.tabview.add("Pedidos")
        self.tab_graficos = self.tabview.add("Gráficos")

        self._build_tab_clientes()
        self._build_tab_ingredientes_orm()
        self._build_tab_menus_orm()
        self._build_tab_pedidos_orm()
        self._build_tab_graficos()

    # ------------------------------------------------------------------
    # Pestaña 3: carga CSV + ORM
    # ------------------------------------------------------------------
    def configurar_pestana3(self):
        label = ctk.CTkLabel(self.tab3, text="Carga de archivo CSV")
        label.pack(pady=20)

        boton_cargar_csv = ctk.CTkButton(
            self.tab3,
            text="Cargar CSV",
            fg_color="#1976D2",
            text_color="white",
            command=self.cargar_csv,
        )
        boton_cargar_csv.pack(pady=10)

        self.frame_tabla_csv = ctk.CTkFrame(self.tab3)
        self.frame_tabla_csv.pack(fill="both", expand=True, padx=10, pady=10)

        self.df_csv = None
        self.tabla_csv = None
        self.csv_path = None  # ruta del CSV

        self.boton_agregar_stock = ctk.CTkButton(
            self.frame_tabla_csv,
            text="Agregar al Stock",
            command=self.agregar_csv_al_stock,
        )
        self.boton_agregar_stock.pack(side="bottom", pady=10)

    def agregar_csv_al_stock(self):
        """Cargar stock desde CSV usando el ORM y actualizar stock + tabla."""
        if self.df_csv is None:
            CTkMessagebox(
                title="Error",
                message="Primero debes cargar un archivo CSV.",
                icon="warning",
            )
            return

        cols = {str(c).strip() for c in self.df_csv.columns}
        try:
            session = get_session()
        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"No se pudo obtener sesión de BD: {e}",
                icon="warning",
            )
            return

        try:
            required_full = {
                "nombre",
                "unidad",
                "stock_actual",
                "stock_minimo",
                "precio_unitario",
            }

            # 1) CSV completo -> usar helper masivo
            if self.csv_path and required_full.issubset(cols) and os.path.exists(
                self.csv_path
            ):
                resumen = cargar_ingredientes_desde_csv(session, self.csv_path)
                CTkMessagebox(
                    title="Carga completada",
                    message=(
                        f"Importados: {resumen.get('importados', 0)}, "
                        f"Actualizados: {resumen.get('actualizados', 0)}"
                    ),
                    icon="info",
                )

            # 2) CSV simple: nombre + cantidad (+ unidad opcional)
            elif {"nombre", "cantidad"}.issubset(cols):
                import_count = 0
                upd_count = 0
                errores = []

                for idx, row in self.df_csv.iterrows():
                    try:
                        nombre = str(row.get("nombre") or "").strip()
                        if not nombre:
                            errores.append(f"Fila {idx+1}: nombre vacío.")
                            continue

                        cantidad_raw = row.get("cantidad")
                        unidad = (
                            str(row.get("unidad") or "unid").strip()
                            if "unidad" in cols
                            else "unid"
                        )

                        cantidad = float(cantidad_raw)
                        if cantidad <= 0:
                            errores.append(
                                f"Fila {idx+1} ({nombre}): cantidad debe ser > 0"
                            )
                            continue

                        if IngredienteModel is None:
                            errores.append(
                                f"Fila {idx+1} ({nombre}): modelo Ingrediente no disponible."
                            )
                            continue

                        existente = (
                            session.query(IngredienteModel)
                            .filter(
                                func.lower(IngredienteModel.nombre)
                                == nombre.casefold()
                            )
                            .one_or_none()
                        )

                        if existente:
                            existente.stock_actual = float(
                                (existente.stock_actual or 0.0) + cantidad
                            )
                            existente.unidad = unidad
                            upd_count += 1
                        else:
                            nuevo = IngredienteModel(
                                nombre=nombre,
                                unidad=unidad,
                                stock_actual=cantidad,
                                stock_minimo=0.0,
                                precio_unitario=0.0,
                                activo=True,
                            )
                            session.add(nuevo)
                            import_count += 1

                    except Exception as e:
                        errores.append(f"Fila {idx+1}: {e}")

                session.commit()
                msg = f"Importados: {import_count}, Actualizados: {upd_count}"
                if errores:
                    msg += f"\nErrores: {len(errores)} (ver consola)"
                    print("Errores al importar CSV:")
                    for er in errores:
                        print(er)
                CTkMessagebox(title="Carga CSV", message=msg, icon="info")

            else:
                CTkMessagebox(
                    title="Error",
                    message=(
                        "CSV inválido. Debe contener al menos 'nombre' y 'cantidad' "
                        "o las columnas completas requeridas."
                    ),
                    icon="warning",
                )
                return

            # Sincronizar stock en memoria desde la BD
            try:
                db_ings = listar_ingredientes(session, solo_activos=True)
                nueva_lista = []
                for dbi in db_ings:
                    try:
                        cantidad_val = float(getattr(dbi, "stock_actual", 0.0))
                    except Exception:
                        cantidad_val = 0.0
                    nueva_lista.append(
                        Ingrediente(
                            nombre=dbi.nombre,
                            unidad=getattr(dbi, "unidad", "unid"),
                            cantidad=cantidad_val,
                        )
                    )
                self.stock.lista_ingredientes = nueva_lista
                self.actualizar_treeview()
            except Exception as e:
                print("Advertencia: no se pudo sincronizar stock desde BD:", e)

        except Exception as e:
            session.rollback()
            CTkMessagebox(
                title="Error",
                message=f"Error al agregar CSV al stock:\n{e}",
                icon="warning",
            )
        finally:
            try:
                session.close()
            except Exception:
                pass

    def cargar_csv(self):
        """Seleccionar archivo CSV y mostrarlo en la tabla de la pestaña 3."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo CSV", filetypes=[("Archivos CSV", "*.csv")]
        )
        if not file_path:
            CTkMessagebox(
                title="Error",
                message="No se seleccionó ningún archivo.",
                icon="warning",
            )
            return

        try:
            import pandas as pd

            self.df_csv = pd.read_csv(file_path)
            self.csv_path = file_path
            self.mostrar_dataframe_en_tabla(self.df_csv)
        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"No se pudo cargar el archivo CSV.\n{e}",
                icon="warning",
            )

    def mostrar_dataframe_en_tabla(self, df):
        if getattr(self, "tabla_csv", None):
            self.tabla_csv.destroy()

        self.tabla_csv = ttk.Treeview(
            self.frame_tabla_csv, columns=list(df.columns), show="headings"
        )
        for col in df.columns:
            self.tabla_csv.heading(col, text=col)
            self.tabla_csv.column(col, width=100, anchor="center")

        for _, row in df.iterrows():
            self.tabla_csv.insert("", "end", values=list(row))

        self.tabla_csv.pack(expand=True, fill="both", padx=10, pady=10)

    # ------------------------------------------------------------------
    # Pestaña Carta (PDF) y Boleta (PDF)
    # ------------------------------------------------------------------
    def actualizar_treeview_pedido(self):
        for item in self.treeview_menu.get_children():
            self.treeview_menu.delete(item)
        for menu in self.pedido.menus:
            self.treeview_menu.insert(
                "", "end", values=(menu.nombre, menu.cantidad, f"${menu.precio:.2f}")
            )

    def _configurar_pestana_crear_menu(self):
        contenedor = ctk.CTkFrame(self.tab4)
        contenedor.pack(expand=True, fill="both", padx=10, pady=10)

        boton_menu = ctk.CTkButton(
            contenedor,
            text="Generar Carta (PDF)",
            command=self.generar_y_mostrar_carta_pdf,
        )
        boton_menu.pack(pady=10)

        self.pdf_frame_carta = ctk.CTkFrame(contenedor)
        self.pdf_frame_carta.pack(expand=True, fill="both", padx=10, pady=10)

        self.pdf_viewer_carta = None

    def generar_y_mostrar_carta_pdf(self):
        try:
            pdf_path = "carta.pdf"
            create_menu_pdf(
                self.menus,
                pdf_path,
                titulo_negocio="Restaurante",
                subtitulo="Carta Primavera 2025",
                moneda="$",
            )

            if self.pdf_viewer_carta is not None:
                try:
                    self.pdf_viewer_carta.pack_forget()
                    self.pdf_viewer_carta.destroy()
                except Exception:
                    pass
                self.pdf_viewer_carta = None

            abs_pdf = os.path.abspath(pdf_path)
            self.pdf_viewer_carta = CTkPDFViewer(self.pdf_frame_carta, file=abs_pdf)
            self.pdf_viewer_carta.pack(expand=True, fill="both")

        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"No se pudo generar/mostrar la carta.\n{e}",
                icon="warning",
            )

    def _configurar_pestana_ver_boleta(self):
        contenedor = ctk.CTkFrame(self.tab5)
        contenedor.pack(expand=True, fill="both", padx=10, pady=10)

        boton_boleta = ctk.CTkButton(
            contenedor, text="Mostrar Boleta (PDF)", command=self.mostrar_boleta
        )
        boton_boleta.pack(pady=10)

        self.pdf_frame_boleta = ctk.CTkFrame(contenedor)
        self.pdf_frame_boleta.pack(expand=True, fill="both", padx=10, pady=10)

        self.pdf_viewer_boleta = None

    def mostrar_boleta(self):
        """Muestra el archivo PDF de la boleta en el visor de la pestaña 'Boleta'."""
        try:
            pdf_path = "boleta.pdf"
            abs_pdf = os.path.abspath(pdf_path)

            if not os.path.exists(abs_pdf):
                CTkMessagebox(
                    title="Error",
                    message="No se encontró el archivo de boleta. Genera una primero.",
                    icon="warning",
                )
                return

            if self.pdf_viewer_boleta is not None:
                try:
                    self.pdf_viewer_boleta.pack_forget()
                    self.pdf_viewer_boleta.destroy()
                except Exception:
                    pass
                self.pdf_viewer_boleta = None

            self.pdf_viewer_boleta = CTkPDFViewer(self.pdf_frame_boleta, file=abs_pdf)
            self.pdf_viewer_boleta.pack(expand=True, fill="both")

        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"No se pudo mostrar la boleta.\n{e}",
                icon="warning",
            )

    # ------------------------------------------------------------------
    # Pestaña 1: gestión de stock manual
    # ------------------------------------------------------------------
    def configurar_pestana1(self):
        frame_formulario = ctk.CTkFrame(self.tab1)
        frame_formulario.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        frame_treeview = ctk.CTkFrame(self.tab1)
        frame_treeview.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        label_nombre = ctk.CTkLabel(frame_formulario, text="Nombre del Ingrediente:")
        label_nombre.pack(pady=5)
        self.entry_nombre = ctk.CTkEntry(frame_formulario)
        self.entry_nombre.pack(pady=5)

        label_unidad = ctk.CTkLabel(frame_formulario, text="Unidad:")
        label_unidad.pack(pady=5)
        self.combo_unidad = ctk.CTkComboBox(frame_formulario, values=["kg", "unid"])
        self.combo_unidad.pack(pady=5)

        label_cantidad = ctk.CTkLabel(frame_formulario, text="Cantidad:")
        label_cantidad.pack(pady=5)
        self.entry_cantidad = ctk.CTkEntry(frame_formulario)
        self.entry_cantidad.pack(pady=5)

        self.boton_ingresar = ctk.CTkButton(
            frame_formulario,
            text="Ingresar Ingrediente",
            command=self.ingresar_ingrediente,
        )
        self.boton_ingresar.pack(pady=10)

        self.boton_eliminar = ctk.CTkButton(
            frame_treeview,
            text="Eliminar Ingrediente",
            fg_color="black",
            text_color="white",
            command=self.eliminar_ingrediente,
        )
        self.boton_eliminar.pack(pady=10)

        self.tree = ttk.Treeview(
            self.tab1,
            columns=("Nombre", "Unidad", "Cantidad"),
            show="headings",
            height=25,
        )
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Unidad", text="Unidad")
        self.tree.heading("Cantidad", text="Cantidad")
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

        self.boton_generar_menu = ctk.CTkButton(
            frame_treeview, text="Generar Menú", command=self.generar_menus
        )
        self.boton_generar_menu.pack(pady=10)

    # ------------------------------------------------------------------
    # Lógica de pedido / tarjetas
    # ------------------------------------------------------------------
    def tarjeta_click(self, event, menu):
        suficiente_stock = True
        if not self.stock.lista_ingredientes:
            suficiente_stock = False

        requeridos = []  # tuplas (stock_obj, req_cantidad)
        for ingr_req in menu.ingredientes:
            nombre_req = Stock._normalize_name(str(ingr_req.nombre))
            unidad_req = Stock._normalize_unit(str(getattr(ingr_req, "unidad", "") or ""))
            encontrado = None
            for ingr_stock in self.stock.lista_ingredientes:
                nombre_stock = Stock._normalize_name(str(ingr_stock.nombre))
                unidad_stock = Stock._normalize_unit(
                    str(getattr(ingr_stock, "unidad", "") or "")
                )
                if nombre_req == nombre_stock and unidad_req == unidad_stock:
                    encontrado = ingr_stock
                    break
            if not encontrado:
                suficiente_stock = False
                break
            try:
                if float(encontrado.cantidad) < float(ingr_req.cantidad):
                    suficiente_stock = False
                    break
            except (ValueError, TypeError):
                suficiente_stock = False
                break
            requeridos.append((encontrado, float(ingr_req.cantidad)))

        if suficiente_stock:
            for ingr_stock, cant_req in requeridos:
                try:
                    nueva_cant = float(ingr_stock.cantidad) - cant_req
                except (ValueError, TypeError):
                    nueva_cant = 0.0
                if nueva_cant < 0:
                    nueva_cant = 0.0
                ingr_stock.cantidad = round(nueva_cant, 3)

            self.pedido.agregar_menu(menu)
            self.actualizar_treeview()
            self.actualizar_treeview_pedido()
            try:
                self._persist_sync_all()
            except Exception as e:
                print("Advertencia: no se pudo sincronizar stock tras venta:", e)
            total = self.pedido.calcular_total()
            self.label_total.configure(text=f"Total: ${total:.2f}")
        else:
            CTkMessagebox(
                title="Stock Insuficiente",
                message=f"No hay suficientes ingredientes para preparar el menú '{menu.nombre}'.",
                icon="warning",
            )

    def cargar_icono_menu(self, ruta_icono):
        imagen = Image.open(ruta_icono)
        icono_menu = ctk.CTkImage(imagen, size=(64, 64))
        return icono_menu

    def crear_tarjeta(self, menu):
        """Crea una tarjeta visual para un menú dentro de self.tarjetas_frame."""
        num_tarjetas = len(self.menus_creados)
        fila = 0
        columna = num_tarjetas

        tarjeta = ctk.CTkFrame(
            self.tarjetas_frame,
            corner_radius=10,
            border_width=1,
            border_color="#4CAF50",
            width=64,
            height=140,
            fg_color="gray",
        )
        tarjeta.grid(row=fila, column=columna, padx=15, pady=15, sticky="nsew")

        tarjeta.bind("<Button-1>", lambda event: self.tarjeta_click(event, menu))
        tarjeta.bind("<Enter>", lambda event: tarjeta.configure(border_color="#FF0000"))
        tarjeta.bind("<Leave>", lambda event: tarjeta.configure(border_color="#4CAF50"))

        if getattr(menu, "icono_path", None):
            try:
                icono = self.cargar_icono_menu(menu.icono_path)
                imagen_label = ctk.CTkLabel(
                    tarjeta,
                    image=icono,
                    width=64,
                    height=64,
                    text="",
                    fg_color="transparent",
                )
                imagen_label.image = icono
                imagen_label.pack(anchor="center", pady=5, padx=10)
                imagen_label.bind(
                    "<Button-1>", lambda event: self.tarjeta_click(event, menu)
                )
            except Exception as e:
                print(f"No se pudo cargar la imagen '{menu.icono_path}': {e}")

        texto_label = ctk.CTkLabel(
            tarjeta,
            text=f"{menu.nombre}",
            text_color="black",
            font=("Helvetica", 12, "bold"),
            fg_color="transparent",
        )
        texto_label.pack(anchor="center", pady=1)
        texto_label.bind("<Button-1>", lambda event: self.tarjeta_click(event, menu))

    def generar_menus(self):
        if not hasattr(self, "tarjetas_frame") or self.tarjetas_frame is None:
            CTkMessagebox(
                title="Error",
                message="El contenedor de tarjetas no está inicializado.",
                icon="warning",
            )
            return

        for widget in self.tarjetas_frame.winfo_children():
            widget.destroy()
        self.menus_creados.clear()

        creadas = 0
        for menu in self.menus:
            if menu.esta_disponible(self.stock):
                self.crear_tarjeta(menu)
                self.menus_creados.add(menu.nombre)
                creadas += 1

        if creadas == 0:
            CTkMessagebox(
                title="Sin menús disponibles",
                message="No hay menús disponibles con el stock actual.",
                icon="info",
            )
        else:
            try:
                self.tabview.set("Pedido")
            except Exception:
                pass

    def eliminar_menu(self):
        selected = self.treeview_menu.selection()
        if not selected:
            CTkMessagebox(
                title="Error",
                message="Selecciona un menú para eliminar.",
                icon="warning",
            )
            return
        nombre_menu = self.treeview_menu.item(selected[0])["values"][0]
        eliminado = self.pedido.quitar_menu(nombre_menu)
        if eliminado:
            CTkMessagebox(
                title="Menú eliminado",
                message=f"Menú '{nombre_menu}' eliminado del pedido.",
                icon="info",
            )
            self.actualizar_treeview_pedido()
            total = self.pedido.calcular_total()
            self.label_total.configure(text=f"Total: ${total:.2f}")
        else:
            CTkMessagebox(
                title="Error", message="No se pudo eliminar el menú.", icon="warning"
            )

    def generar_boleta(self):
        """
        Genera la boleta en PDF utilizando BoletaFacade
        y guarda el pedido en la BD asociado al cliente seleccionado.
        """
        try:
            if not self.pedido.menus:
                CTkMessagebox(
                    title="Error",
                    message="No hay menús en el pedido para generar la boleta.",
                    icon="warning",
                )
                return

            cliente = self.cliente_seleccionado
            if cliente is None:
                CTkMessagebox(
                    title="Error",
                    message="Debes seleccionar un cliente antes de generar la boleta.",
                    icon="warning",
                )
                return

            # Guardar pedido + detalles en BD
            try:
                pedido_id = self._guardar_pedido_en_bd(cliente.id)
                print("Pedido guardado con id:", pedido_id)
            except Exception as e:
                CTkMessagebox(
                    title="Error",
                    message=f"No se pudo guardar el pedido en la BD.\n{e}",
                    icon="warning",
                )
                return

            # Generar boleta PDF
            boleta = BoletaFacade(self.pedido)
            mensaje = boleta.generar_boleta()
            CTkMessagebox(title="Boleta Generada", message=mensaje, icon="info")

            # Mostrar la boleta en la pestaña correspondiente
            self.mostrar_boleta()

        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"No se pudo generar la boleta.\n{e}",
                icon="warning",
            )

    def configurar_pestana2(self):
        frame_superior = ctk.CTkFrame(self.tab2)
        frame_superior.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        frame_intermedio = ctk.CTkFrame(self.tab2)
        frame_intermedio.pack(side="top", fill="x", padx=10, pady=5)

        # Selector de cliente
        label_cliente = ctk.CTkLabel(frame_intermedio, text="Cliente:")
        label_cliente.pack(side="left", padx=(10, 5))

        self.combo_clientes = ctk.CTkComboBox(
            frame_intermedio,
            values=[],
            width=250,
            command=self._on_cliente_cambiado,
        )
        self.combo_clientes.pack(side="left", padx=(0, 10))

        # Frame donde van las tarjetas de menús
        self.tarjetas_frame = ctk.CTkFrame(frame_superior)
        self.tarjetas_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.boton_eliminar_menu = ctk.CTkButton(
            frame_intermedio, text="Eliminar Menú", command=self.eliminar_menu
        )
        self.boton_eliminar_menu.pack(side="right", padx=10)

        self.label_total = ctk.CTkLabel(
            frame_intermedio,
            text="Total: $0.00",
            anchor="e",
            font=("Helvetica", 12, "bold"),
        )
        self.label_total.pack(side="right", padx=10)

        frame_inferior = ctk.CTkFrame(self.tab2)
        frame_inferior.pack(side="bottom", fill="both", expand=True, padx=10, pady=10)

        self.treeview_menu = ttk.Treeview(
            frame_inferior,
            columns=("Nombre", "Cantidad", "Precio Unitario"),
            show="headings",
        )
        self.treeview_menu.heading("Nombre", text="Nombre del Menú")
        self.treeview_menu.heading("Cantidad", text="Cantidad")
        self.treeview_menu.heading("Precio Unitario", text="Precio Unitario")
        self.treeview_menu.pack(expand=True, fill="both", padx=10, pady=10)

        self.boton_generar_boleta = ctk.CTkButton(
            frame_inferior, text="Generar Boleta", command=self.generar_boleta
        )
        self.boton_generar_boleta.pack(side="bottom", pady=10)

        # Cargar clientes al combobox
        self._cargar_clientes_combobox()

    def _cargar_clientes_combobox(self):
        """Carga los clientes desde la BD al combobox de la pestaña Pedido."""
        try:
            sess = self.session or get_session()
            clientes = listar_clientes(sess, solo_activos=True)
            self._clientes_cache = clientes

            valores = [f"{c.id} - {c.nombre}" for c in clientes]
            if hasattr(self, "combo_clientes"):
                self.combo_clientes.configure(values=valores)
                if valores:
                    self.combo_clientes.set(valores[0])
                    self.cliente_seleccionado = clientes[0]
        except Exception as e:
            CTkMessagebox(
                title="Error",
                message=f"No se pudieron cargar los clientes en el selector:\n{e}",
                icon="warning",
            )

    def _on_cliente_cambiado(self, value: str):
        """Actualiza self.cliente_seleccionado cuando el usuario cambia el combobox."""
        for c in getattr(self, "_clientes_cache", []):
            etiqueta = f"{c.id} - {c.nombre}"
            if etiqueta == value:
                self.cliente_seleccionado = c
                break

    # ------------------------------------------------------------------
    # Validaciones + CRUD de stock manual
    # ------------------------------------------------------------------
    def validar_nombre(self, nombre):
        if re.match(r"^[a-zA-Z\s]+$", nombre):
            return True
        CTkMessagebox(
            title="Error de Validación",
            message="El nombre debe contener solo letras y espacios.",
            icon="warning",
        )
        return False

    def validar_cantidad(self, cantidad):
        try:
            val = float(cantidad)
            if val >= 0:
                return True
        except Exception:
            pass
        CTkMessagebox(
            title="Error de Validación",
            message="La cantidad debe ser un número positivo (ej. 1 o 0.3).",
            icon="warning",
        )
        return False

    def ingresar_ingrediente(self):
        nombre = self.entry_nombre.get().strip()
        unidad = self.combo_unidad.get().strip()
        cantidad = self.entry_cantidad.get().strip()

        if not self.validar_nombre(nombre):
            return
        if not self.validar_cantidad(cantidad):
            return

        try:
            nombre_norm = Stock._normalize_name(nombre)
            unidad_norm = Stock._normalize_unit(unidad)
        except Exception:
            nombre_norm = nombre.strip().casefold()
            unidad_norm = unidad.strip().casefold()

        ingrediente = Ingrediente(
            nombre=nombre_norm, unidad=unidad_norm, cantidad=cantidad
        )
        self.stock.agregar_ingrediente(ingrediente)

        try:
            self._persist_ingrediente_db(ingrediente)
        except Exception as e:
            print("Advertencia: no se pudo persistir tras ingresar ingrediente:", e)

        CTkMessagebox(
            title="Ingrediente agregado",
            message="Ingrediente agregado al stock.",
            icon="info",
        )
        self.actualizar_treeview()

    def eliminar_ingrediente(self):
        selected = self.tree.selection()
        if not selected:
            CTkMessagebox(
                title="Error",
                message="Selecciona un ingrediente para eliminar.",
                icon="warning",
            )
            return
        nombre = self.tree.item(selected[0])["values"][0]
        self.stock.eliminar_ingrediente(nombre)

        try:
            self._remove_ingrediente_db(nombre)
        except Exception as e:
            print("Advertencia: no se pudo persistir eliminación:", e)

        CTkMessagebox(
            title="Ingrediente eliminado",
            message="Ingrediente eliminado del stock.",
            icon="info",
        )
        self.actualizar_treeview()

    def actualizar_treeview(self):
        if not hasattr(self, "tree"):
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        for ingrediente in self.stock.lista_ingredientes:
            try:
                cantidad_mostrar = f"{float(ingrediente.cantidad):.1f}"
            except (ValueError, TypeError):
                cantidad_mostrar = str(ingrediente.cantidad)
            self.tree.insert(
                "",
                "end",
                values=(ingrediente.nombre, ingrediente.unidad, cantidad_mostrar),
            )

    # ------------------------------------------------------------------
    # Persistencia ORM de ingredientes
    # ------------------------------------------------------------------
    def _persist_ingrediente_db(self, ingrediente_obj):
        """Crear o actualizar registro en BD para un objeto Ingrediente (local)."""
        if IngredienteModel is None:
            print("Advertencia: modelo Ingrediente no disponible, no se persiste en BD.")
            return
        session = None
        try:
            session = get_session()
            nombre_norm = (ingrediente_obj.nombre or "").strip()
            existente = (
                session.query(IngredienteModel)
                .filter(func.lower(IngredienteModel.nombre) == nombre_norm.casefold())
                .one_or_none()
            )
            if existente:
                existente.stock_actual = float(
                    getattr(ingrediente_obj, "cantidad", 0.0) or 0.0
                )
                existente.unidad = (
                    getattr(ingrediente_obj, "unidad", existente.unidad)
                    or existente.unidad
                )
                session.add(existente)
            else:
                nuevo = IngredienteModel(
                    nombre=nombre_norm,
                    unidad=getattr(ingrediente_obj, "unidad", "unid") or "unid",
                    stock_actual=float(
                        getattr(ingrediente_obj, "cantidad", 0.0) or 0.0
                    ),
                    stock_minimo=0.0,
                    precio_unitario=0.0,
                    activo=True,
                )
                session.add(nuevo)
            session.commit()
        except Exception as e:
            if session:
                session.rollback()
            print("Advertencia: no se pudo persistir ingrediente en BD:", e)
        finally:
            if session:
                session.close()

    def _remove_ingrediente_db(self, nombre):
        """Marcar ingrediente como inactivo (o eliminar) en BD por nombre."""
        if IngredienteModel is None:
            return
        session = None
        try:
            session = get_session()
            nombre_norm = (nombre or "").strip()
            existente = (
                session.query(IngredienteModel)
                .filter(func.lower(IngredienteModel.nombre) == nombre_norm.casefold())
                .one_or_none()
            )
            if existente:
                existente.activo = False
                session.add(existente)
                session.commit()
        except Exception as e:
            if session:
                session.rollback()
            print("Advertencia: no se pudo eliminar/inhabilitar ingrediente en BD:", e)
        finally:
            if session:
                session.close()

    def _persist_sync_all(self):
        """Sincronizar toda la lista de stock (en memoria) a la BD."""
        for ingr in getattr(self.stock, "lista_ingredientes", []):
            try:
                self._persist_ingrediente_db(ingr)
            except Exception as e:
                print("Advertencia al sincronizar ingrediente:", ingr, e)

    def _guardar_pedido_en_bd(self, cliente_id: int):
        """
        Guarda el pedido actual (self.pedido) en la base de datos usando el ORM.

        - Crea un registro en PedidoModel.
        - Por cada menú del pedido crea un registro en PedidoDetalleModel
          asociando el menu_id correcto (no nulo).
        """
        if PedidoModel is None or PedidoDetalleModel is None or MenuModel is None:
            raise RuntimeError(
                "Modelos ORM de Pedido/Menu/PedidoDetalle no disponibles."
            )

        session = get_session()
        try:
            # 1) Crear el pedido
            total = self.pedido.calcular_total()
            pedido_db = PedidoModel(
                cliente_id=cliente_id,
                fecha=datetime.now(),
                total=total,
                estado="PAGADO",
            )
            session.add(pedido_db)
            session.flush()  # pedido_db.id disponible

            # 2) Crear detalles
            for menu in self.pedido.menus:
                # Buscar el menú en la BD por nombre (case-insensitive)
                menu_db = (
                    session.query(MenuModel)
                    .filter(func.lower(MenuModel.nombre) == menu.nombre.casefold())
                    .one_or_none()
                )

                # Si no existe en BD, lo creamos rápido
                if menu_db is None:
                    menu_db = MenuModel(
                        nombre=menu.nombre,
                        precio=menu.precio,
                        activo=True,
                    )
                    session.add(menu_db)
                    session.flush()  # ahora menu_db.id ya existe

                detalle_db = PedidoDetalleModel(
                    pedido_id=pedido_db.id,
                    menu_id=menu_db.id,  # NOT NULL
                    cantidad=menu.cantidad,
                    subtotal=menu.cantidad * menu.precio,
                )
                session.add(detalle_db)

            session.commit()
            return pedido_db.id

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


# -------------------------------------------------------------------
# Arranque
# -------------------------------------------------------------------
if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)

    app = AplicacionConPestanas()

    try:
        style = ttk.Style(app)
        style.theme_use("clam")
    except Exception:
        pass

    app.mainloop()
