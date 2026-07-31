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