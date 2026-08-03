from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Float, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    empresa = Column(String(255))
    rfc = Column(String(30))
    contacto = Column(String(150))
    puesto = Column(String(100))
    telefono = Column(String(50))
    email = Column(String(200))
    ciudad = Column(String(150))
    tipo = Column(String(30))
    giro = Column(String(100))
    notas = Column(Text)

    fecha_creacion = Column(TIMESTAMP, server_default=func.now())
    fecha_actualizacion = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )


class Seguimiento(Base):
    __tablename__ = "seguimientos"

    id = Column(Integer, primary_key=True, index=True)
    clienteId = Column(Integer, ForeignKey("clientes.id"))
    asunto = Column(String(200))
    monto = Column(Float, default=0)
    etapa = Column(String(30))
    prob = Column(Integer, default=50)
    fecha = Column(String(20))
    resp = Column(String(100))
    notas = Column(Text)
    creado = Column(TIMESTAMP, server_default=func.now())


class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id = Column(Integer, primary_key=True, index=True)
    clienteId = Column(Integer, ForeignKey("clientes.id"))
    desc = Column(String(200))
    estado = Column(String(20))
    items = Column(Text)
    notas = Column(Text)
    fecha = Column(TIMESTAMP, server_default=func.now())

class Factura(Base):
    __tablename__ = "facturas"
    id = Column(Integer, primary_key=True, index=True)
    clienteId = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    numero = Column(String(60))       # CVESER-FOLIO
    folio = Column(String(30))
    serie = Column(String(10))
    fecha = Column(String(30))        # FECREG
    rfc_cliente = Column(String(30))
    razon_social = Column(String(255))
    subtotal = Column(Float, default=0)
    descuento = Column(Float, default=0)
    iva = Column(Float, default=0)
    total = Column(Float, default=0)
    estado_doc = Column(String(50))   # Vigente, Cancelado
    forma_pago = Column(String(50))
    metodo_pago = Column(String(100))
    creado = Column(TIMESTAMP, server_default=func.now())