from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ClienteBase(BaseModel):
    empresa: str
    rfc: Optional[str] = None
    contacto: Optional[str] = None
    puesto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    ciudad: Optional[str] = None
    tipo: Optional[str] = None
    giro: Optional[str] = None
    notas: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class Cliente(ClienteBase):
    id: int
    fecha_creacion: Optional[Any] = None
    fecha_actualizacion: Optional[Any] = None

    class Config:
        from_attributes = True

class SeguimientoBase(BaseModel):
    clienteId: int
    asunto: str
    monto: Optional[float] = 0
    etapa: Optional[str] = None
    prob: Optional[int] = 50
    fecha: Optional[str] = None
    resp: Optional[str] = None
    notas: Optional[str] = None

class SeguimientoCreate(SeguimientoBase):
    pass

class Seguimiento(SeguimientoBase):
    id: int
    creado: Optional[Any] = None

    class Config:
        from_attributes = True

class CotizacionBase(BaseModel):
    clienteId: int
    desc: Optional[str] = None
    estado: Optional[str] = None
    items: Optional[List[Dict[str, Any]]] = None
    notas: Optional[str] = None

class CotizacionCreate(CotizacionBase):
    pass

class Cotizacion(CotizacionBase):
    id: int
    fecha: Optional[Any] = None

    class Config:
        from_attributes = True

class FacturaBase(BaseModel):
    clienteId: Optional[int] = None
    numero: Optional[str] = None
    folio: Optional[str] = None
    serie: Optional[str] = None
    fecha: Optional[str] = None
    rfc_cliente: Optional[str] = None
    razon_social: Optional[str] = None
    subtotal: Optional[float] = 0
    descuento: Optional[float] = 0
    iva: Optional[float] = 0
    total: Optional[float] = 0
    estado_doc: Optional[str] = None
    forma_pago: Optional[str] = None
    metodo_pago: Optional[str] = None
    conceptos: Optional[str] = None

class FacturaCreate(FacturaBase):
    pass

class Factura(FacturaBase):
    id: int
    creado: Optional[Any] = None

    class Config:
        from_attributes = True