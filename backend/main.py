import json
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import SessionLocal, engine
from models import Base, Cliente, Seguimiento, Cotizacion, Factura
import schemas

Base.metadata.create_all(bind=engine)

# ── Migración automática de columnas ─────────────────────────────────────────
# Amplía las columnas al arrancar para soportar nombres largos de Aspel.
# MySQL ignora el ALTER si ya tiene ese tamaño, así que es seguro correrlo siempre.
def aplicar_migraciones():
    migraciones = [
        "ALTER TABLE clientes MODIFY empresa   VARCHAR(255)  CHARACTER SET utf8mb4",
        "ALTER TABLE clientes MODIFY rfc        VARCHAR(30)   CHARACTER SET utf8mb4",
        "ALTER TABLE clientes MODIFY contacto   VARCHAR(150)  CHARACTER SET utf8mb4",
        "ALTER TABLE clientes MODIFY telefono   VARCHAR(50)   CHARACTER SET utf8mb4",
        "ALTER TABLE clientes MODIFY email      VARCHAR(200)  CHARACTER SET utf8mb4",
        "ALTER TABLE clientes MODIFY ciudad     VARCHAR(150)  CHARACTER SET utf8mb4",
        "ALTER TABLE clientes MODIFY tipo       VARCHAR(30)   CHARACTER SET utf8mb4",
        "ALTER TABLE clientes MODIFY giro       VARCHAR(100)  CHARACTER SET utf8mb4",
        "ALTER TABLE clientes MODIFY puesto     VARCHAR(100)  CHARACTER SET utf8mb4",
    ]
    with engine.connect() as conn:
        for sql in migraciones:
            try:
                conn.execute(text(sql))
            except Exception as e:
                print(f"Migración omitida ({sql[:40]}...): {e}")
        conn.commit()
    print("✅ Migraciones aplicadas.")

try:
    aplicar_migraciones()
except Exception as e:
    print(f"⚠️  No se pudieron aplicar migraciones: {e}")

app = FastAPI(title="Deep Core CRM API")
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", include_in_schema=False)
def inicio():
    return FileResponse(FRONTEND_DIR / "CRM_Del_Toro.html")


# --- Clientes ---
@app.get("/clientes", response_model=list[schemas.Cliente])
def obtener_clientes(db: Session = Depends(get_db)):
    return db.query(Cliente).all()


@app.get("/clientes/{cliente_id}", response_model=schemas.Cliente)
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db)):
    db_cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return db_cliente


@app.post("/clientes", response_model=schemas.Cliente)
def crear_cliente(cliente: schemas.ClienteCreate, db: Session = Depends(get_db)):
    nuevo = Cliente(**cliente.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@app.put("/clientes/{cliente_id}", response_model=schemas.Cliente)
def actualizar_cliente(cliente_id: int, cliente: schemas.ClienteCreate, db: Session = Depends(get_db)):
    db_cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    for key, value in cliente.model_dump().items():
        setattr(db_cliente, key, value)
    
    db.commit()
    db.refresh(db_cliente)
    return db_cliente


@app.delete("/clientes/{cliente_id}")
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    db_cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db.delete(db_cliente)
    db.commit()
    return {"mensaje": "Cliente eliminado"}


# --- Seguimientos ---
@app.get("/seguimientos", response_model=list[schemas.Seguimiento])
def obtener_seguimientos(db: Session = Depends(get_db)):
    return db.query(Seguimiento).all()


@app.post("/seguimientos", response_model=schemas.Seguimiento)
def crear_seguimiento(seguimiento: schemas.SeguimientoCreate, db: Session = Depends(get_db)):
    nuevo = Seguimiento(**seguimiento.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@app.put("/seguimientos/{seguimiento_id}", response_model=schemas.Seguimiento)
def actualizar_seguimiento(seguimiento_id: int, seguimiento: schemas.SeguimientoCreate, db: Session = Depends(get_db)):
    db_seguimiento = db.query(Seguimiento).filter(Seguimiento.id == seguimiento_id).first()
    if not db_seguimiento:
        raise HTTPException(status_code=404, detail="Seguimiento no encontrado")
    
    for key, value in seguimiento.model_dump().items():
        setattr(db_seguimiento, key, value)
        
    db.commit()
    db.refresh(db_seguimiento)
    return db_seguimiento


@app.delete("/seguimientos/{seguimiento_id}")
def eliminar_seguimiento(seguimiento_id: int, db: Session = Depends(get_db)):
    db_seguimiento = db.query(Seguimiento).filter(Seguimiento.id == seguimiento_id).first()
    if not db_seguimiento:
        raise HTTPException(status_code=404, detail="Seguimiento no encontrado")
    db.delete(db_seguimiento)
    db.commit()
    return {"mensaje": "Seguimiento eliminado"}


# --- Cotizaciones ---
@app.get("/cotizaciones", response_model=list[schemas.Cotizacion])
def obtener_cotizaciones(db: Session = Depends(get_db)):
    cotizaciones = db.query(Cotizacion).all()
    for c in cotizaciones:
        if c.items:
            try:
                c.items = json.loads(c.items)
            except:
                c.items = []
        else:
            c.items = []
    return cotizaciones


@app.post("/cotizaciones", response_model=schemas.Cotizacion)
def crear_cotizacion(cotizacion: schemas.CotizacionCreate, db: Session = Depends(get_db)):
    data = cotizacion.model_dump()
    if data.get("items") is not None:
        data["items"] = json.dumps(data["items"])
        
    nuevo = Cotizacion(**data)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    
    if nuevo.items:
        try:
            nuevo.items = json.loads(nuevo.items)
        except:
            nuevo.items = []
    else:
        nuevo.items = []
        
    return nuevo


@app.put("/cotizaciones/{cotizacion_id}", response_model=schemas.Cotizacion)
def actualizar_cotizacion(cotizacion_id: int, cotizacion: schemas.CotizacionCreate, db: Session = Depends(get_db)):
    db_cotizacion = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id).first()
    if not db_cotizacion:
        raise HTTPException(status_code=404, detail="Cotizacion no encontrada")
    
    data = cotizacion.model_dump()
    if data.get("items") is not None:
        data["items"] = json.dumps(data["items"])
        
    for key, value in data.items():
        setattr(db_cotizacion, key, value)
        
    db.commit()
    db.refresh(db_cotizacion)
    
    if db_cotizacion.items:
        try:
            db_cotizacion.items = json.loads(db_cotizacion.items)
        except:
            db_cotizacion.items = []
    else:
        db_cotizacion.items = []
        
    return db_cotizacion


@app.delete("/cotizaciones/{cotizacion_id}")
def eliminar_cotizacion(cotizacion_id: int, db: Session = Depends(get_db)):
    db_cotizacion = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id).first()
    if not db_cotizacion:
        raise HTTPException(status_code=404, detail="Cotizacion no encontrada")
    db.delete(db_cotizacion)
    db.commit()
    return {"mensaje": "Cotizacion eliminada"}


# ─── SINCRONIZACIÓN ASPEL ADM ───────────────────────────────────────────────

from pydantic import BaseModel as PydanticBase
from typing import Optional

class AspelSyncRequest(PydanticBase):
    # Opción A: login automático con credenciales
    rfc: Optional[str] = None
    usuario: Optional[str] = None
    contrasenia: Optional[str] = None
    # Opción B: token manual (fallback)
    idsesion: Optional[str] = None

@app.post("/sync/aspel")
def sincronizar_desde_aspel(req: AspelSyncRequest, db: Session = Depends(get_db)):
    """
    Importa clientes desde Aspel ADM al CRM.
    Soporta dos modos:
      1. Login automático
      2. Token manual
    """

    from aspel.clientes import obtener_clientes_aspel, mapear_cliente_aspel_a_crm

    # -------------------------------------------------------
    # Obtener Token
    # -------------------------------------------------------

    token = req.idsesion

    if not token:

        if not req.rfc or not req.usuario or not req.contrasenia:
            raise HTTPException(
                status_code=400,
                detail="Proporciona RFC, Usuario y Contraseña."
            )

        try:

            from aspel.auth import login_aspel

            token = login_aspel(
                req.rfc,
                req.usuario,
                req.contrasenia
            )

            print("=" * 80)
            print("TOKEN OBTENIDO")
            print(token[:80] + "...")
            print("=" * 80)

        except Exception as e:

            raise HTTPException(
                status_code=401,
                detail=f"Login fallido: {str(e)}"
            )

    # -------------------------------------------------------
    # Consultar clientes Aspel
    # -------------------------------------------------------

    try:

        registros_aspel = obtener_clientes_aspel(token)

    except Exception as e:

        raise HTTPException(
            status_code=502,
            detail=f"Error al consultar clientes de Aspel: {str(e)}"
        )

    if not registros_aspel:

        raise HTTPException(
            status_code=404,
            detail="Aspel no devolvió clientes."
        )

    print("=" * 80)
    print("TOTAL CLIENTES ASPPEL:", len(registros_aspel))
    print("=" * 80)

    # Importar al CRM en lotes de 20 para no saturar MySQL
    creados = 0
    actualizados = 0
    errores = 0
    eliminados = 0
    LOTE = 20

    # Colectar todos los RFC de Aspel para saber cuáles conservar
    rfcs_aspel = set()
    rfcs_vistos_en_este_sync = set()
    
    # Para reporte al usuario
    clientes_duplicados = []
    clientes_sin_nombre = []

    def truncar(val, max_len):
        return (val or "")[:max_len]

    for i, reg in enumerate(registros_aspel):
        try:
            datos = mapear_cliente_aspel_a_crm(reg)

            if not datos["empresa"]:
                # Guardamos info cruda para avisar qué cliente venía sin nombre
                clientes_sin_nombre.append(str(reg.get("data", [])))
                continue

            # Truncar para respetar límites de columna
            datos["empresa"]  = truncar(datos["empresa"], 255)
            datos["rfc"]      = truncar(datos["rfc"], 30)
            datos["contacto"] = truncar(datos["contacto"], 150)
            datos["telefono"] = truncar(datos["telefono"], 50)
            datos["email"]    = truncar(datos["email"], 200)
            datos["ciudad"]   = truncar(datos["ciudad"], 150)
            datos["tipo"]     = truncar(datos["tipo"], 30)

            rfc = datos["rfc"]
            if rfc:
                rfcs_aspel.add(rfc)
                if rfc in rfcs_vistos_en_este_sync:
                    clientes_duplicados.append(f"{datos['empresa']} (RFC: {rfc})")
                rfcs_vistos_en_este_sync.add(rfc)

            cliente_existente = None
            if rfc:
                cliente_existente = db.query(Cliente).filter(Cliente.rfc == rfc).first()

            if cliente_existente:
                for campo, valor in datos.items():
                    if valor:
                        setattr(cliente_existente, campo, valor)
                actualizados += 1
            else:
                nuevo = Cliente(**datos)
                db.add(nuevo)
                creados += 1

            # Commit cada 20 registros para no saturar la conexión
            if (i + 1) % LOTE == 0:
                db.commit()

        except Exception as e:
            print("ERROR reg", i, ":", str(e)[:150])
            db.rollback()
            errores += 1

    # Commit intermedio antes de eliminar
    try:
        db.commit()
    except Exception as e:
        print("ERROR commit intermedio:", str(e))
        db.rollback()

    # ── Eliminar clientes que NO están en Aspel ──────────────────────────────
    # Borra cualquier cliente cuyo RFC no esté en Aspel (incluyendo los sin RFC)
    try:
        clientes_crm = db.query(Cliente).all()
        for c in clientes_crm:
            rfc_c = (c.rfc or "").strip()
            if not rfc_c or rfc_c not in rfcs_aspel:
                db.delete(c)
                eliminados += 1
        db.commit()
    except Exception as e:
        print("ERROR eliminando clientes extra:", str(e))
        db.rollback()

    return {
        "total_aspel": len(registros_aspel),
        "creados": creados,
        "actualizados": actualizados,
        "eliminados": eliminados,
        "errores": errores,
        "duplicados": clientes_duplicados,
        "sin_nombre": clientes_sin_nombre,
        "mensaje": f"✅ Sincronización completa: {creados} nuevos, {actualizados} actualizados, {eliminados} eliminados."
    }


# --- Facturas ---
@app.get("/facturas", response_model=list[schemas.Factura])
def obtener_facturas(db: Session = Depends(get_db)):
    return db.query(Factura).all()

@app.delete("/facturas/{factura_id}")
def eliminar_factura(factura_id: int, db: Session = Depends(get_db)):
    db_fact = db.query(Factura).filter(Factura.id == factura_id).first()
    if not db_fact:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    db.delete(db_fact)
    db.commit()
    return {"mensaje": "Factura eliminada"}

from datetime import datetime, date

@app.get("/facturas/resumen")
def resumen_facturas(db: Session = Depends(get_db)):
    from datetime import datetime as dt

    def _parse_fecha(raw):
        """Intenta parsear una fecha en cualquier formato y devuelve objeto date o None."""
        if not raw:
            return None
        raw = str(raw).strip()[:10]
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
            try:
                return dt.strptime(raw, fmt).date()
            except:
                continue
        return None

    clientes_map = {c.id: c for c in db.query(Cliente).all()}
    facturas_db  = db.query(Factura).all()

    # 1. Ignorar facturas canceladas
    facturas_validas = [f for f in facturas_db if str(f.estado_doc).strip().lower() != "cancelado"]

    # 2. Parsear fecha de antemano para poder ordenar
    for f in facturas_validas:
        f._parsed_date = _parse_fecha(f.fecha) or date.min

    # 3. Ordenar facturas: más recientes primero, si empatan en fecha, por número de factura mayor
    facturas_validas.sort(key=lambda x: (x._parsed_date, x.numero or ""), reverse=True)

    # Solo clientes que tienen AL MENOS una factura válida
    resumen_map = {}
    for f in facturas_validas:
        cid     = f.clienteId
        rfc_val = f.rfc_cliente or "SIN RFC"
        key     = cid if cid else rfc_val

        if key not in resumen_map:
            # Como la lista está ordenada de más reciente a más antigua, 
            # la primera vez que vemos a un cliente, ESTA es su última factura real.
            empresa = (
                clientes_map[cid].empresa
                if cid and cid in clientes_map
                else (f.razon_social or rfc_val)
            )
            resumen_map[key] = {
                "clienteId":      cid,
                "empresa":        empresa,
                "rfc":            f.rfc_cliente,
                "total_facturas": 0,
                "total_vendido":  0.0,
                "ultima_fecha":   f._parsed_date if f._parsed_date != date.min else None,
                "ultimo_numero":  f.numero,
            }
        
        # Acumuladores de totales y conteo (solo de facturas no canceladas)
        resumen_map[key]["total_facturas"] += 1
        resumen_map[key]["total_vendido"] = round(
            resumen_map[key]["total_vendido"] + (f.total or 0.0), 2
        )

    # Añadir clientes de la base de datos que no tuvieron ninguna factura válida
    for cid, c in clientes_map.items():
        if cid not in resumen_map and c.rfc not in resumen_map:
            resumen_map[cid] = {
                "clienteId":      cid,
                "empresa":        c.empresa,
                "rfc":            c.rfc,
                "total_facturas": 0,
                "total_vendido":  0.0,
                "ultima_fecha":   None,
                "ultimo_numero":  None,
            }

    hoy = date.today()
    resultado = []
    for k, v in resumen_map.items():
        dias_sin_comprar = None
        estado = "sin_datos"
        uf = v["ultima_fecha"]  # objeto date o None
        if uf:
            dias_sin_comprar = (hoy - uf).days
            if dias_sin_comprar < 30:   estado = "activo"     # 0-29 días
            elif dias_sin_comprar < 60: estado = "en_riesgo"  # 30-59 días
            else:                       estado = "critico"     # 60+ días
        elif v["total_facturas"] == 0:
            estado = "sin_facturar"

        v["dias_sin_comprar"] = dias_sin_comprar
        v["estado"]           = estado
        # Convertir la fecha a string YYYY-MM-DD para el frontend
        v["ultima_fecha"] = uf.strftime("%Y-%m-%d") if uf else None
        resultado.append(v)

    # Ordenar: críticos primero → en riesgo → activos → sin facturar
    orden = {"critico": 0, "en_riesgo": 1, "activo": 2, "sin_facturar": 3, "sin_datos": 4}
    resultado.sort(key=lambda x: orden.get(x["estado"], 5))
    return resultado



# Estado global del job de sincronización de facturas
_sync_fact_status: dict = {"estado": "idle", "mensaje": "", "total_aspel": 0, "creadas": 0, "actualizadas": 0, "errores": 0}

def _run_sync_facturas_bg(token: str, rfc_cookie: str, usuario_cookie: str):
    """Tarea en segundo plano: descarga e importa facturas de Aspel."""
    from aspel.facturas import obtener_facturas_aspel, mapear_factura_aspel_a_crm
    global _sync_fact_status
    _sync_fact_status = {"estado": "corriendo", "mensaje": "Conectando con Aspel…", "total_aspel": 0, "creadas": 0, "actualizadas": 0, "errores": 0}

    db = SessionLocal()
    try:
        _sync_fact_status["mensaje"] = "Descargando facturas de Aspel…"
        registros_aspel = obtener_facturas_aspel(token, rfc=rfc_cookie, usuario=usuario_cookie)
        _sync_fact_status["total_aspel"] = len(registros_aspel)
        _sync_fact_status["mensaje"] = f"Guardando {len(registros_aspel)} facturas…"

        creadas = actualizadas = errores = 0
        LOTE = 20
        clientes_por_rfc = {c.rfc: c.id for c in db.query(Cliente).all() if c.rfc}

        for i, reg in enumerate(registros_aspel):
            try:
                datos = mapear_factura_aspel_a_crm(reg)
                numero = datos.get("numero")
                if not numero: continue
                rfc_f = datos.get("rfc_cliente")
                if rfc_f and rfc_f in clientes_por_rfc:
                    datos["clienteId"] = clientes_por_rfc[rfc_f]
                exist = db.query(Factura).filter(Factura.numero == numero).first()
                if exist:
                    for k, v in datos.items(): setattr(exist, k, v)
                    actualizadas += 1
                else:
                    db.add(Factura(**datos)); creadas += 1
                if (i + 1) % LOTE == 0:
                    db.commit()
                    _sync_fact_status["mensaje"] = f"Guardando… {i+1}/{len(registros_aspel)}"
            except Exception as e:
                print("ERROR reg fac", i, ":", str(e)[:150])
                db.rollback(); errores += 1

        db.commit()
        _sync_fact_status = {
            "estado": "listo",
            "mensaje": f"✅ Sincronización completa: {creadas} creadas, {actualizadas} actualizadas.",
            "total_aspel": len(registros_aspel),
            "creadas": creadas, "actualizadas": actualizadas, "errores": errores
        }
    except Exception as e:
        _sync_fact_status = {"estado": "error", "mensaje": f"❌ {str(e)}", "total_aspel": 0, "creadas": 0, "actualizadas": 0, "errores": 0}
        try: db.rollback()
        except: pass
    finally:
        db.close()


@app.post("/sync/aspel/facturas")
def sincronizar_facturas(req: AspelSyncRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    global _sync_fact_status
    if _sync_fact_status.get("estado") == "corriendo":
        raise HTTPException(status_code=409, detail="Ya hay una sincronización en proceso. Espera a que termine.")

    token = req.idsesion
    rfc_cookie     = (req.rfc or "").strip().upper()
    usuario_cookie = (req.usuario or "").strip()

    if not token:
        if not req.rfc or not req.usuario or not req.contrasenia:
            raise HTTPException(status_code=400, detail="Proporciona RFC, Usuario y Contraseña.")
        try:
            from aspel.auth import login_aspel
            token = login_aspel(req.rfc, req.usuario, req.contrasenia)
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Login fallido: {str(e)}")

    # Iniciar en segundo plano y responder de inmediato
    _sync_fact_status = {"estado": "corriendo", "mensaje": "Iniciando…", "total_aspel": 0, "creadas": 0, "actualizadas": 0, "errores": 0}
    background_tasks.add_task(_run_sync_facturas_bg, token, rfc_cookie, usuario_cookie)
    return {"estado": "corriendo", "mensaje": "Sincronización iniciada. Consulta /sync/aspel/facturas/status para ver el progreso."}


@app.get("/sync/aspel/facturas/status")
def status_sync_facturas():
    return _sync_fact_status



# ── DEBUG: ver estructura cruda de Aspel ──────────────────────────────────────
class AspelDebugRequest(PydanticBase):
    rfc: Optional[str] = None
    usuario: Optional[str] = None
    contrasenia: Optional[str] = None
    idsesion: Optional[str] = None

@app.post("/sync/aspel/debug")
def debug_aspel(req: AspelDebugRequest):
    """Devuelve los primeros 2 registros crudos de Aspel para diagnóstico."""
    from aspel.clientes import obtener_clientes_aspel

    token = req.idsesion
    if not token:
        from aspel.auth import login_aspel
        token = login_aspel(req.rfc, req.usuario, req.contrasenia)

    registros = obtener_clientes_aspel(token)
    return {
        "total": len(registros),
        "tipo": str(type(registros[0])) if registros else "vacio",
        "muestra": registros[:2] if registros else []
    }