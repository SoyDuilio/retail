from sqlalchemy import Column, Integer, String, DateTime, Numeric
from app.database import Base
from datetime import datetime, timezone

def get_utc_now():
    return datetime.now(timezone.utc)

class UbicacionVendedorModel(Base):
    __tablename__ = "ubicaciones_vendedor"
    
    id = Column(Integer, primary_key=True, index=True)
    vendedor_id = Column(Integer, nullable=False, index=True)
    latitud = Column(Numeric(10, 8), nullable=False)
    longitud = Column(Numeric(11, 8), nullable=False)
    precision_gps = Column(Numeric(10, 2))
    timestamp = Column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)
    tipo_registro = Column(String(20), default='automatico')
    cliente_id = Column(Integer)
    pedido_id = Column(Integer)
    bateria_porcentaje = Column(Integer)
    conectividad = Column(String(20))