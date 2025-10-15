# app/models/client_models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, func, JSON, Date
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from decimal import Decimal
import json
from .base import Base

# Función auxiliar para obtener la hora actual en UTC
def get_utc_now():
    return datetime.now(timezone.utc)

# =============================================
# CLIENTES PRINCIPALES
# =============================================

class ClienteModel(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo_cliente = Column(String(50), unique=True, index=True)
    nombre_comercial = Column(String(200))  # NO nombres/apellidos
    razon_social = Column(String(200))
    ruc = Column(String(11), unique=True, nullable=False, index=True)
    telefono = Column(String(15))
    email = Column(String(100))
    direccion_completa = Column(Text)  # NO solo direccion
    referencia = Column(Text)
    distrito = Column(String(100))
    provincia = Column(String(100))
    departamento = Column(String(100))
    codigo_postal = Column(String(10))
    latitud = Column(DECIMAL(10, 8), index=True)
    longitud = Column(DECIMAL(11, 8), index=True)
    precision_gps = Column(DECIMAL(5, 2))
    tipo_cliente_id = Column(Integer, ForeignKey("tipos_cliente.id"), nullable=False, index=True)
    activo = Column(Boolean, default=True, index=True)
    verificado = Column(Boolean, default=False)
    fecha_registro = Column(DateTime, default=get_utc_now)
    fecha_modificacion = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    configuraciones = Column(JSON)
    metadatos = Column(JSON)
    # Campos de control de crédito
    es_moroso = Column(Boolean, default=False)
    deuda_actual = Column(DECIMAL(12, 2), default=0)
    ultima_fecha_pago = Column(Date)
    dias_mora = Column(Integer, default=0)
    
    # Relaciones
    tipo_cliente = relationship("TipoClienteModel", back_populates="clientes")
    
    # Relaciones
    tipo_cliente = relationship("TipoClienteModel", back_populates="clientes")
    #pedidos = relationship("PedidoModel", back_populates="cliente")
    #conversaciones_voz = relationship("ConversacionVozModel", back_populates="cliente")
    historial_credito = relationship("HistorialCreditoModel", back_populates="cliente", order_by="HistorialCreditoModel.created_at.desc()")
    contactos = relationship("ContactoClienteModel", back_populates="cliente", order_by="ContactoClienteModel.created_at.desc()")

    pedidos = relationship("PedidoModel", back_populates="cliente")
    
    @property
    def nombre_completo(self):
        """Obtener nombre completo del cliente"""
        if self.razon_social:
            return self.razon_social
        elif self.nombres and self.apellidos:
            return f"{self.nombres} {self.apellidos}"
        elif self.nombres:
            return self.nombres
        else:
            return f"Cliente RUC {self.ruc}"
    
    @property
    def credito_disponible(self):
        """Calcular crédito disponible"""
        limite = float(self.limite_credito or 0)
        usado = float(self.credito_usado or 0)
        return Decimal(str(max(0, limite - usado)))
    
    @property
    def porcentaje_credito_usado(self):
        """Porcentaje de crédito utilizado"""
        if not self.limite_credito or self.limite_credito == 0:
            return 0
        return float(self.credito_usado or 0) / float(self.limite_credito) * 100
    
    @property
    def estado_credito(self):
        """Estado del crédito basado en utilización"""
        porcentaje = self.porcentaje_credito_usado
        if porcentaje >= 95:
            return "critico"
        elif porcentaje >= 80:
            return "alto"
        elif porcentaje >= 50:
            return "medio"
        else:
            return "bajo"
    
    @property
    def tiene_coordenadas(self):
        """¿Tiene coordenadas GPS?"""
        return self.latitud is not None and self.longitud is not None
    
    def puede_comprar(self, monto: float):
        """¿Puede realizar una compra por el monto especificado?"""
        return float(self.credito_disponible) >= monto
    
    def usar_credito(self, monto: float, motivo: str = "Compra"):
        """Usar crédito del cliente"""
        if not self.puede_comprar(monto):
            raise ValueError("Crédito insuficiente")
        
        self.credito_usado = float(self.credito_usado or 0) + monto
        self.updated_at = get_utc_now()
        
        return self.credito_disponible
    
    def liberar_credito(self, monto: float, motivo: str = "Pago"):
        """Liberar crédito del cliente (por pago)"""
        credito_actual = float(self.credito_usado or 0)
        self.credito_usado = max(0, credito_actual - monto)
        self.updated_at = get_utc_now()
        
        return self.credito_disponible
    
    def distancia_a(self, lat: float, lng: float):
        """Calcular distancia en km a coordenadas dadas"""
        if not self.tiene_coordenadas:
            return None
        
        import math
        
        # Fórmula haversine para calcular distancia
        R = 6371  # Radio de la Tierra en km
        
        lat1, lng1 = math.radians(float(self.latitud)), math.radians(float(self.longitud))
        lat2, lng2 = math.radians(lat), math.radians(lng)
        
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def __repr__(self):
        return f"<Cliente {self.ruc} - {self.nombre_completo}>"


class TipoClienteModel(Base):
    __tablename__ = 'tipos_cliente'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)

    clientes = relationship("ClienteModel", back_populates="tipo_cliente")
    precios = relationship("app.models.product_models.PrecioClienteModel", back_populates="tipo_cliente")

    def __repr__(self):
        return f"<TipoCliente {self.nombre}>"

# =============================================
# HISTORIAL CREDITICIO
# =============================================

class HistorialCreditoModel(Base):
    __tablename__ = "historial_credito"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    tipo_movimiento = Column(String(30), nullable=False, index=True)  # aumento_limite, uso_credito, pago, ajuste
    monto = Column(DECIMAL(10, 2), nullable=False)
    limite_anterior = Column(DECIMAL(10, 2))
    limite_nuevo = Column(DECIMAL(10, 2))
    credito_usado_anterior = Column(DECIMAL(10, 2))
    credito_usado_nuevo = Column(DECIMAL(10, 2))
    motivo = Column(String(200), nullable=False)
    referencia_id = Column(String(100))  # ID del pedido, pago, etc.
    aprobado_por = Column(Integer)  # ID del usuario que aprobó el cambio
    aprobado_por_tipo = Column(String(20))  # supervisor, evaluador, sistema
    created_at = Column(DateTime, default=get_utc_now, index=True)
    
    # Relaciones
    cliente = relationship("ClienteModel", back_populates="historial_credito")
    
    @property
    def impacto_credito(self):
        """Impacto del movimiento en el crédito disponible"""
        if self.tipo_movimiento in ["uso_credito"]:
            return -float(self.monto)
        elif self.tipo_movimiento in ["pago", "liberacion_credito"]:
            return float(self.monto)
        elif self.tipo_movimiento in ["aumento_limite"]:
            return float(self.limite_nuevo or 0) - float(self.limite_anterior or 0)
        return 0
    
    def __repr__(self):
        return f"<HistorialCredito {self.tipo_movimiento}: {self.monto} - Cliente {self.cliente_id}>"

# =============================================
# CONTACTOS CON CLIENTES
# =============================================

class ContactoClienteModel(Base):
    __tablename__ = "contactos_clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    tipo_contacto = Column(String(20), nullable=False, index=True)  # llamada, whatsapp, visita, email
    asunto = Column(String(200), nullable=False)
    mensaje = Column(Text)
    realizado_por = Column(Integer, nullable=False)
    realizado_por_tipo = Column(String(20), nullable=False)  # vendedor, evaluador, supervisor
    respuesta_cliente = Column(Text)
    resultado = Column(String(20), nullable=False, index=True)  # exitoso, sin_respuesta, ocupado, rechazado
    fecha_programada = Column(DateTime, index=True)
    fecha_realizada = Column(DateTime, index=True)
    duracion_minutos = Column(Integer)
    notas_adicionales = Column(Text)
    created_at = Column(DateTime, default=get_utc_now, index=True)
    
    # Relaciones
    cliente = relationship("ClienteModel", back_populates="contactos")
    
    @property
    def fue_exitoso(self):
        """¿El contacto fue exitoso?"""
        return self.resultado == "exitoso"
    
    @property
    def dias_desde_contacto(self):
        """Días transcurridos desde el contacto"""
        fecha_ref = self.fecha_realizada or self.created_at
        return (get_utc_now() - fecha_ref).days
    
    def __repr__(self):
        return f"<ContactoCliente {self.tipo_contacto} - {self.cliente.nombre_completo if self.cliente else 'N/A'}>"

# =============================================
# SEGMENTACIÓN DE CLIENTES
# =============================================

class SegmentoClienteModel(Base):
    __tablename__ = "segmentos_clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text)
    criterios = Column(Text)  # JSON con criterios de segmentación
    color = Column(String(7), default="#3B82F6")  # Color hex para UI
    activo = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relaciones
    asignaciones = relationship("AsignacionSegmentoModel", back_populates="segmento")
    
    @property
    def total_clientes(self):
        """Total de clientes asignados a este segmento"""
        return len([a for a in self.asignaciones if a.activo])
    
    def __repr__(self):
        return f"<SegmentoCliente {self.nombre}>"

class AsignacionSegmentoModel(Base):
    __tablename__ = "asignaciones_segmento"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    segmento_id = Column(Integer, ForeignKey("segmentos_clientes.id"), nullable=False, index=True)
    asignado_por = Column(Integer, nullable=False)
    asignado_por_tipo = Column(String(20), nullable=False)
    motivo = Column(Text)
    activo = Column(Boolean, default=True, index=True)
    fecha_asignacion = Column(DateTime, default=get_utc_now)
    fecha_desasignacion = Column(DateTime)
    
    # Relaciones
    cliente = relationship("ClienteModel")
    segmento = relationship("SegmentoClienteModel", back_populates="asignaciones")
    
    def desasignar(self, motivo: str = None):
        """Desasignar cliente del segmento"""
        self.activo = False
        self.fecha_desasignacion = get_utc_now()
        if motivo:
            self.motivo = f"{self.motivo or ''} | Desasignado: {motivo}"
    
    def __repr__(self):
        return f"<AsignacionSegmento Cliente:{self.cliente_id} -> Segmento:{self.segmento_id}>"

# =============================================
# EVALUACIÓN CREDITICIA
# =============================================

class EvaluacionCrediticiaModel(Base):
    __tablename__ = "evaluaciones_crediticias"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    evaluado_por = Column(Integer, nullable=False)
    evaluado_por_tipo = Column(String(20), nullable=False)
    score_crediticio = Column(Integer, nullable=False)  # 0-100
    limite_recomendado = Column(DECIMAL(10, 2), nullable=False)
    limite_anterior = Column(DECIMAL(10, 2))
    factores_positivos = Column(Text)  # JSON con factores positivos
    factores_negativos = Column(Text)  # JSON con factores negativos
    observaciones = Column(Text)
    aprobado = Column(Boolean, default=False)
    aprobado_por = Column(Integer)
    fecha_aprobacion = Column(DateTime)
    vigente_hasta = Column(DateTime)
    created_at = Column(DateTime, default=get_utc_now, index=True)
    
    # Relaciones
    cliente = relationship("ClienteModel")
    
    @property
    def estado_evaluacion(self):
        """Estado de la evaluación crediticia"""
        if not self.aprobado:
            return "pendiente"
        elif self.vigente_hasta and self.vigente_hasta < get_utc_now():
            return "vencida"
        else:
            return "vigente"
    
    @property
    def nivel_riesgo(self):
        """Nivel de riesgo basado en el score"""
        if self.score_crediticio >= 80:
            return "bajo"
        elif self.score_crediticio >= 60:
            return "medio"
        elif self.score_crediticio >= 40:
            return "alto"
        else:
            return "muy_alto"
    
    def aprobar(self, aprobado_por: int):
        """Aprobar evaluación crediticia"""
        self.aprobado = True
        self.aprobado_por = aprobado_por
        self.fecha_aprobacion = get_utc_now()
        # Vigente por 6 meses
        from datetime import timedelta
        self.vigente_hasta = get_utc_now() + timedelta(days=180)
    
    def __repr__(self):
        return f"<EvaluacionCrediticia Cliente:{self.cliente_id} Score:{self.score_crediticio}>"

# =============================================
# UBICACIONES Y ZONAS
# =============================================

class ZonaGeograficaModel(Base):
    __tablename__ = "zonas_geograficas"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    coordenadas_poligono = Column(Text)  # JSON con coordenadas del polígono
    centro_lat = Column(DECIMAL(10, 8))
    centro_lng = Column(DECIMAL(11, 8))
    radio_km = Column(DECIMAL(5, 2))  # Si es zona circular
    activa = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=get_utc_now)
    
    def clientes_en_zona(self, db):
        """Obtener clientes dentro de esta zona"""
        if self.radio_km:
            # Zona circular - usar distancia
            # Implementación básica, en producción usar PostGIS
            return []
        else:
            # Zona poligonal - implementar con PostGIS
            return []
    
    def __repr__(self):
        return f"<ZonaGeografica {self.nombre}>"

# =============================================
# FUNCIONES DE UTILIDAD
# =============================================

def obtener_clientes_cercanos(db, lat: float, lng: float, radio_km: float = 5.0, tipo_cliente_id: int = None, activos_solo: bool = True):
    """Obtener clientes cercanos a una ubicación"""
    query = db.query(ClienteModel).filter(
        ClienteModel.latitud.isnot(None),
        ClienteModel.longitud.isnot(None)
    )
    
    if activos_solo:
        query = query.filter(ClienteModel.activo == True)
    
    if tipo_cliente_id:
        query = query.filter(ClienteModel.tipo_cliente_id == tipo_cliente_id)
    
    clientes = query.all()
    
    # Filtrar por distancia
    clientes_cercanos = []
    for cliente in clientes:
        distancia = cliente.distancia_a(lat, lng)
        if distancia and distancia <= radio_km:
            clientes_cercanos.append({
                "cliente": cliente,
                "distancia_km": round(distancia, 2)
            })
    
    # Ordenar por distancia
    clientes_cercanos.sort(key=lambda x: x["distancia_km"])
    
    return clientes_cercanos

def actualizar_credito_cliente(db, cliente_id: int, nuevo_limite: float, motivo: str, aprobado_por: int, aprobado_por_tipo: str = "supervisor"):
    """Actualizar límite de crédito del cliente"""
    cliente = db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
    if not cliente:
        raise ValueError("Cliente no encontrado")
    
    limite_anterior = float(cliente.limite_credito or 0)
    cliente.limite_credito = nuevo_limite
    cliente.updated_at = get_utc_now()
    
    # Registrar en historial
    historial = HistorialCreditoModel(
        cliente_id=cliente_id,
        tipo_movimiento="aumento_limite" if nuevo_limite > limite_anterior else "disminucion_limite",
        monto=abs(nuevo_limite - limite_anterior),
        limite_anterior=limite_anterior,
        limite_nuevo=nuevo_limite,
        credito_usado_anterior=float(cliente.credito_usado or 0),
        credito_usado_nuevo=float(cliente.credito_usado or 0),
        motivo=motivo,
        aprobado_por=aprobado_por,
        aprobado_por_tipo=aprobado_por_tipo
    )
    
    db.add(historial)
    db.commit()
    
    return cliente

def registrar_uso_credito(db, cliente_id: int, monto: float, referencia_id: str = None, motivo: str = "Compra"):
    """Registrar uso de crédito del cliente"""
    cliente = db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
    if not cliente:
        raise ValueError("Cliente no encontrado")
    
    if not cliente.puede_comprar(monto):
        raise ValueError("Crédito insuficiente")
    
    credito_usado_anterior = float(cliente.credito_usado or 0)
    cliente.usar_credito(monto, motivo)
    
    # Registrar en historial
    historial = HistorialCreditoModel(
        cliente_id=cliente_id,
        tipo_movimiento="uso_credito",
        monto=monto,
        limite_anterior=float(cliente.limite_credito or 0),
        limite_nuevo=float(cliente.limite_credito or 0),
        credito_usado_anterior=credito_usado_anterior,
        credito_usado_nuevo=float(cliente.credito_usado),
        motivo=motivo,
        referencia_id=referencia_id,
        aprobado_por_tipo="sistema"
    )
    
    db.add(historial)
    db.commit()
    
    return cliente

def registrar_pago_cliente(db, cliente_id: int, monto: float, referencia_id: str = None, motivo: str = "Pago"):
    """Registrar pago del cliente (libera crédito)"""
    cliente = db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
    if not cliente:
        raise ValueError("Cliente no encontrado")
    
    credito_usado_anterior = float(cliente.credito_usado or 0)
    cliente.liberar_credito(monto, motivo)
    
    # Registrar en historial
    historial = HistorialCreditoModel(
        cliente_id=cliente_id,
        tipo_movimiento="pago",
        monto=monto,
        limite_anterior=float(cliente.limite_credito or 0),
        limite_nuevo=float(cliente.limite_credito or 0),
        credito_usado_anterior=credito_usado_anterior,
        credito_usado_nuevo=float(cliente.credito_usado),
        motivo=motivo,
        referencia_id=referencia_id,
        aprobado_por_tipo="sistema"
    )
    
    db.add(historial)
    db.commit()
    
    return cliente

def registrar_contacto(db, cliente_id: int, tipo_contacto: str, asunto: str, mensaje: str, 
                      realizado_por: int, realizado_por_tipo: str, resultado: str = "exitoso", 
                      respuesta_cliente: str = None, duracion_minutos: int = None):
    """Registrar contacto con cliente"""
    contacto = ContactoClienteModel(
        cliente_id=cliente_id,
        tipo_contacto=tipo_contacto,
        asunto=asunto,
        mensaje=mensaje,
        realizado_por=realizado_por,
        realizado_por_tipo=realizado_por_tipo,
        respuesta_cliente=respuesta_cliente,
        resultado=resultado,
        fecha_realizada=get_utc_now(),
        duracion_minutos=duracion_minutos
    )
    
    db.add(contacto)
    db.commit()
    
    return contacto

def calcular_score_crediticio(cliente: ClienteModel, db):
    """Calcular score crediticio basado en historial y comportamiento"""
    score = 50  # Score base
    
    # Factor 1: Antigüedad del cliente (max +15 puntos)
    dias_cliente = (get_utc_now() - cliente.created_at).days
    if dias_cliente > 365:
        score += 15
    elif dias_cliente > 180:
        score += 10
    elif dias_cliente > 90:
        score += 5
    
    # Factor 2: Utilización de crédito (max +15 puntos)
    utilizacion = cliente.porcentaje_credito_usado
    if utilizacion < 30:
        score += 15
    elif utilizacion < 60:
        score += 10
    elif utilizacion < 80:
        score += 5
    else:
        score -= 10  # Penalizar alta utilización
    
    # Factor 3: Historial de pagos (max +20 puntos)
    pagos = db.query(HistorialCreditoModel).filter(
        HistorialCreditoModel.cliente_id == cliente.id,
        HistorialCreditoModel.tipo_movimiento == "pago"
    ).count()
    
    if pagos > 10:
        score += 20
    elif pagos > 5:
        score += 15
    elif pagos > 2:
        score += 10
    elif pagos > 0:
        score += 5
    
    # Asegurar que el score esté en el rango válido
    return max(0, min(100, score))

def generar_reporte_clientes(db, tipo_cliente_id: int = None, fecha_desde: datetime = None, fecha_hasta: datetime = None):
    """Generar reporte de clientes"""
    from sqlalchemy import func
    
    query = db.query(ClienteModel)
    
    if tipo_cliente_id:
        query = query.filter(ClienteModel.tipo_cliente_id == tipo_cliente_id)
    
    if fecha_desde:
        query = query.filter(ClienteModel.created_at >= fecha_desde)
    
    if fecha_hasta:
        query = query.filter(ClienteModel.created_at <= fecha_hasta)
    
    clientes = query.all()
    
    # Calcular estadísticas
    total_clientes = len(clientes)
    clientes_activos = len([c for c in clientes if c.activo])
    limite_credito_promedio = sum(float(c.limite_credito or 0) for c in clientes) / max(1, total_clientes)
    credito_usado_total = sum(float(c.credito_usado or 0) for c in clientes)
    
    return {
        "total_clientes": total_clientes,
        "clientes_activos": clientes_activos,
        "clientes_inactivos": total_clientes - clientes_activos,
        "limite_credito_promedio": round(limite_credito_promedio, 2),
        "credito_usado_total": credito_usado_total,
        "utilizacion_credito_promedio": round((credito_usado_total / max(1, limite_credito_promedio * total_clientes)) * 100, 2),
        "fecha_reporte": get_utc_now()
    }