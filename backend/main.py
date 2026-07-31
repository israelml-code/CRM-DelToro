import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Base, Cliente, Seguimiento, Cotizacion
import schemas

Base.metadata.create_all(bind=engine)

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
    LOTE = 20

    def truncar(val, max_len):
        return (val or "")[:max_len]

    for i, reg in enumerate(registros_aspel):
        try:
            datos = mapear_cliente_aspel_a_crm(reg)

            if not datos["empresa"]:
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

    # Commit final
    try:
        db.commit()
    except Exception as e:
        print("ERROR commit final:", str(e))
        db.rollback()

    return {
        "total_aspel": len(registros_aspel),
        "creados": creados,
        "actualizados": actualizados,
        "errores": errores,
        "mensaje": f"✅ Sincronización completa: {creados} nuevos, {actualizados} actualizados."
    }



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