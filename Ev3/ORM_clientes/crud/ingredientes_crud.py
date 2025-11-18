import os
import csv
from functools import reduce
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# importar modelo con fallback paquete/directo
try:
    from ORM_clientes.models import Ingrediente
except Exception:
    from models import Ingrediente  # type: ignore

# utilidades con lambdas
_normalize = lambda s: (s or "").strip()
_normalize_key = lambda s: _normalize(s).casefold()

def crear_ingrediente(session: Session, nombre: str, unidad: str, stock_actual: float, stock_minimo: float, precio_unitario: float) -> Ingrediente:
    """Crea un ingrediente validando duplicados y valores."""
    nombre_norm = _normalize(nombre)
    if not nombre_norm:
        raise ValueError("El nombre del ingrediente no puede estar vacío.")
    try:
        stock_actual_val = float(stock_actual)
        if stock_actual_val <= 0:
            raise ValueError("El stock_actual debe ser mayor que 0.")
    except Exception:
        raise ValueError("stock_actual debe ser un número válido mayor que 0.")
    # buscar duplicado (case-insensitive)
    existente = session.query(Ingrediente).filter(func.lower(Ingrediente.nombre) == nombre_norm.casefold()).one_or_none()
    if existente:
        raise IntegrityError("duplicate", params=None, orig=None)
    ing = Ingrediente(
        nombre=nombre_norm,
        unidad=_normalize(unidad) or "unid",
        stock_actual=stock_actual_val,
        stock_minimo=float(stock_minimo or 0.0),
        precio_unitario=float(precio_unitario or 0.0),
        activo=True,
    )
    session.add(ing)
    session.commit()
    session.refresh(ing)
    return ing

def listar_ingredientes(session: Session, solo_activos: bool = False) -> List[Ingrediente]:
    q = session.query(Ingrediente)
    if solo_activos:
        q = q.filter(Ingrediente.activo == True)
    return q.order_by(Ingrediente.nombre).all()

def cargar_ingredientes_desde_csv(session: Session, csv_path: str) -> Dict[str, Any]:
    """
    Carga masiva desde CSV. Columnas esperadas (case-insensitive):
    nombre, unidad, stock_actual, stock_minimo, precio_unitario
    Devuelve resumen con importados, actualizados y lista de errores.
    """
    required = {"nombre", "unidad", "stock_actual", "stock_minimo", "precio_unitario"}
    resumen = {"importados": 0, "actualizados": 0, "errores": 0, "detalles": []}

    try:
        with open(csv_path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames:
                return {"importados": 0, "actualizados": 0, "errores": 1, "detalles": ["CSV sin cabeceras"]}
            # normalizar nombres de columna a minúsculas para comparar
            cols_map = {c: c.strip() for c in reader.fieldnames}
            cols_lower = {c.strip().casefold(): c for c in reader.fieldnames}
            if not required.issubset({k.casefold() for k in reader.fieldnames}):
                faltan = required - set(k.strip().casefold() for k in reader.fieldnames)
                return {"importados": 0, "actualizados": 0, "errores": 1, "detalles": [f"Faltan columnas: {faltan}"]}

            filas = list(reader)

            # pipeline: limpiar filas -> filtrar sin nombre -> convertir tipos
            normalizar_fila = lambda r: {k.strip(): (r.get(k) or "").strip() for k in r.keys()}
            filas_norm = list(map(normalizar_fila, filas))
            filas_con_nombre = list(filter(lambda r: bool(_normalize(r.get("nombre"))), filas_norm))

            def to_typed(r, lineno):
                try:
                    return {
                        "lineno": lineno,
                        "nombre": _normalize(r.get("nombre")),
                        "unidad": _normalize(r.get("unidad")) or "unid",
                        "stock_actual": float(r.get("stock_actual") or 0.0),
                        "stock_minimo": float(r.get("stock_minimo") or 0.0),
                        "precio_unitario": float(r.get("precio_unitario") or 0.0),
                    }
                except Exception as e:
                    raise ValueError(f"Línea {lineno}: error de formato - {e}")

            typed_rows = []
            for i, r in enumerate(filas_con_nombre, start=1):
                try:
                    typed_rows.append(to_typed(r, i))
                except Exception as e:
                    resumen["detalles"].append(str(e))

            errors: List[str] = []

            def aplicar(acc, row):
                lineno = row["lineno"]
                try:
                    nombre_key = _normalize_key(row["nombre"])
                    existente = session.query(Ingrediente).filter(func.lower(Ingrediente.nombre) == nombre_key).one_or_none()
                    if existente:
                        # actualizar: sumar stock y ajustar campos no vacíos
                        existente.stock_actual = float((existente.stock_actual or 0.0)) + float(row["stock_actual"])
                        existente.unidad = row["unidad"] or existente.unidad
                        existente.stock_minimo = float(row["stock_minimo"] or existente.stock_minimo or 0.0)
                        existente.precio_unitario = float(row["precio_unitario"] or existente.precio_unitario or 0.0)
                        session.add(existente)
                        acc["actualizados"] += 1
                    else:
                        if row["stock_actual"] <= 0:
                            errors.append(f"Línea {lineno} ({row['nombre']}): stock_actual debe ser > 0")
                        else:
                            nuevo = Ingrediente(
                                nombre=row["nombre"],
                                unidad=row["unidad"],
                                stock_actual=row["stock_actual"],
                                stock_minimo=row["stock_minimo"],
                                precio_unitario=row["precio_unitario"],
                                activo=True
                            )
                            session.add(nuevo)
                            acc["importados"] += 1
                    # flush para detectar constraints temprano
                    session.flush()
                except IntegrityError as ie:
                    session.rollback()
                    errors.append(f"Línea {lineno} ({row.get('nombre')}): duplicado o constraint ({ie})")
                except Exception as e:
                    session.rollback()
                    errors.append(f"Línea {lineno} ({row.get('nombre')}): {e}")
                return acc

            summary = reduce(aplicar, typed_rows, {"importados": 0, "actualizados": 0})

            # intentar commit final si no hubo errores fatales
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                errors.append(f"Commit falló: {e}")

            resumen["importados"] = summary["importados"]
            resumen["actualizados"] = summary["actualizados"]
            resumen["errores"] = len(resumen["detalles"]) + len(errors)
            resumen["detalles"].extend(errors)
            return resumen

    except FileNotFoundError:
        return {"importados": 0, "actualizados": 0, "errores": 1, "detalles": [f"No se encontró {csv_path}"]}
    except Exception as e:
        return {"importados": 0, "actualizados": 0, "errores": 1, "detalles": [str(e)]}
