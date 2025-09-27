# app/models/message_models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

# Import para timedelta:
from datetime import datetime, timedelta

from .base import Base

# Función auxiliar para obtener la hora actual en UTC
def get_utc_now():
    return datetime.now(timezone.utc)

# =============================================
# ENUMS PARA MENSAJERÍA
# =============================================

class TipoMensajeEnum(enum.Enum):
    PEDIDO_NUEVO = "pedido_nuevo"
    PEDIDO_APROBADO = "pedido_aprobado"
    PEDIDO_RECHAZADO = "pedido_rechazado"
    MENSAJE_GENERAL = "mensaje_general"
    CHAT_VOZ = "chat_voz"
    STOCK_BAJO = "stock_bajo"
    EMERGENCIA = "emergencia"

class RolUsuarioEnum(enum.Enum):
    VENDEDOR = "vendedor"
    EVALUADOR = "evaluador"
    SUPERVISOR = "supervisor"
    CLIENTE = "cliente"

class EstadoMensajeEnum(enum.Enum):
    PENDIENTE = "pendiente"
    ENVIADO = "enviado"
    ENTREGADO = "entregado"
    LEIDO = "leido"
    FALLIDO = "fallido"

# =============================================
# MENSAJES PRINCIPALES
# =============================================

class MensajeModel(Base):
    __tablename__ = "mensajes"
    
    id = Column(Integer, primary_key=True, index=True)
    remitente_id = Column(Integer, nullable=False, index=True)
    remitente_tipo = Column(SQLEnum(RolUsuarioEnum), nullable=False, index=True)
    destinatario_id = Column(Integer, index=True)  # NULL para broadcast
    destinatario_tipo = Column(SQLEnum(RolUsuarioEnum), index=True)
    tipo_mensaje = Column(SQLEnum(TipoMensajeEnum), nullable=False, index=True)
    titulo = Column(String(200), nullable=False)
    contenido = Column(Text, nullable=False)
    datos_adicionales = Column(Text)  # JSON con datos extra
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), index=True)
    prioridad = Column(String(10), default="normal", index=True)  # normal, high, urgent
    sonido = Column(Boolean, default=True)
    vibrar = Column(Boolean, default=True)
    
    # Estado del mensaje
    leido = Column(Boolean, default=False, index=True)
    enviado = Column(Boolean, default=False, index=True)
    fecha_envio = Column(DateTime, default=get_utc_now, index=True)
    fecha_lectura = Column(DateTime, index=True)
    intentos_envio = Column(Integer, default=0)
    error_envio = Column(Text)
    
    # Metadatos
    ip_address = Column(String(45))
    user_agent = Column(Text)
    dispositivo_info = Column(Text)  # JSON con info del dispositivo
    
    created_at = Column(DateTime, default=get_utc_now, index=True)
    
    # Relaciones
    conversacion = relationship("ConversacionVozModel", back_populates="transcripciones")
    
    @property
    def timestamp_formateado(self):
        """Timestamp en formato MM:SS"""
        if not self.timestamp_audio:
            return "00:00"
        
        segundos_total = int(float(self.timestamp_audio))
        minutos = segundos_total // 60
        segundos = segundos_total % 60
        
        return f"{minutos:02d}:{segundos:02d}"
    
    @property
    def confianza_porcentaje(self):
        """Confianza en porcentaje"""
        if not self.confianza:
            return 0
        return int(float(self.confianza) * 100)
    
    @property
    def texto_final(self):
        """Texto final (procesado si existe, original si no)"""
        return self.texto_procesado or self.texto_original
    
    def editar_texto(self, nuevo_texto: str, editado_por: int):
        """Editar el texto procesado"""
        self.texto_procesado = nuevo_texto
        self.editado = True
        self.editado_por = editado_por
        self.fecha_edicion = get_utc_now()
    
    def __repr__(self):
        return f"<Transcripcion {self.hablante} - {self.timestamp_formateado}: {self.texto_original[:50]}...>"

# =============================================
# PLANTILLAS DE MENSAJES
# =============================================

class PlantillaMensajeModel(Base):
    __tablename__ = "plantillas_mensajes"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, index=True)
    categoria = Column(String(50), nullable=False, index=True)  # bienvenida, seguimiento, promocion, etc.
    descripcion = Column(Text)
    
    # Plantilla
    titulo_template = Column(String(200), nullable=False)
    contenido_template = Column(Text, nullable=False)
    variables = Column(Text)  # JSON array con variables disponibles
    
    # Configuración
    tipo_usuario_objetivo = Column(SQLEnum(RolUsuarioEnum))  # Para qué tipo de usuario es
    tipo_mensaje = Column(SQLEnum(TipoMensajeEnum), default=TipoMensajeEnum.MENSAJE_GENERAL)
    prioridad = Column(String(10), default="normal")
    sonido = Column(Boolean, default=True)
    
    # Estado
    activa = Column(Boolean, default=True, index=True)
    uso_contador = Column(Integer, default=0)
    
    # Metadatos
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relaciones
    mensajes_generados = relationship("MensajePlantillaModel", back_populates="plantilla")
    
    @property
    def variables_lista(self):
        """Lista de variables disponibles"""
        if not self.variables:
            return []
        
        import json
        try:
            return json.loads(self.variables)
        except json.JSONDecodeError:
            return []
    
    def renderizar(self, variables_valores: dict):
        """Renderizar plantilla con valores"""
        titulo = self.titulo_template
        contenido = self.contenido_template
        
        # Reemplazar variables
        for variable, valor in variables_valores.items():
            placeholder = f"{{{variable}}}"
            titulo = titulo.replace(placeholder, str(valor))
            contenido = contenido.replace(placeholder, str(valor))
        
        return {
            "titulo": titulo,
            "contenido": contenido,
            "tipo_mensaje": self.tipo_mensaje,
            "prioridad": self.prioridad,
            "sonido": self.sonido
        }
    
    def incrementar_uso(self):
        """Incrementar contador de uso"""
        self.uso_contador += 1
    
    def __repr__(self):
        return f"<PlantillaMensaje {self.nombre} - {self.categoria}>"

class MensajePlantillaModel(Base):
    __tablename__ = "mensajes_plantilla"
    
    id = Column(Integer, primary_key=True, index=True)
    mensaje_id = Column(Integer, ForeignKey("mensajes.id", ondelete="CASCADE"), nullable=False, index=True)
    plantilla_id = Column(Integer, ForeignKey("plantillas_mensajes.id"), nullable=False, index=True)
    variables_utilizadas = Column(Text)  # JSON con variables y valores usados
    created_at = Column(DateTime, default=get_utc_now)
    
    # Relaciones
    mensaje = relationship("MensajeModel")
    plantilla = relationship("PlantillaMensajeModel", back_populates="mensajes_generados")
    
    def __repr__(self):
        return f"<MensajePlantilla M:{self.mensaje_id} P:{self.plantilla_id}>"

# =============================================
# CAMPAÑAS DE MENSAJERÍA
# =============================================

class CampanaMensajesModel(Base):
    __tablename__ = "campanas_mensajes"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    plantilla_id = Column(Integer, ForeignKey("plantillas_mensajes.id"), nullable=False, index=True)
    
    # Configuración de la campaña
    destinatarios_config = Column(Text, nullable=False)  # JSON con criterios de destinatarios
    fecha_inicio = Column(DateTime, nullable=False, index=True)
    fecha_fin = Column(DateTime, index=True)
    
    # Estado de la campaña
    estado = Column(String(20), default="borrador", index=True)  # borrador, programada, enviando, completada, pausada
    
    # Estadísticas
    total_destinatarios = Column(Integer, default=0)
    enviados = Column(Integer, default=0)
    exitosos = Column(Integer, default=0)
    fallidos = Column(Integer, default=0)
    leidos = Column(Integer, default=0)
    
    # Control
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relaciones
    plantilla = relationship("PlantillaMensajeModel")
    envios = relationship("EnvioCampanaModel", back_populates="campana")
    
    @property
    def tasa_exito(self):
        """Tasa de éxito de la campaña"""
        if self.enviados == 0:
            return 0
        return (self.exitosos / self.enviados) * 100
    
    @property
    def tasa_lectura(self):
        """Tasa de lectura de la campaña"""
        if self.exitosos == 0:
            return 0
        return (self.leidos / self.exitosos) * 100
    
    @property
    def progreso_porcentaje(self):
        """Porcentaje de progreso de envío"""
        if self.total_destinatarios == 0:
            return 0
        return (self.enviados / self.total_destinatarios) * 100
    
    def puede_iniciar(self):
        """¿Puede iniciarse la campaña?"""
        return (self.estado in ["borrador", "pausada"] and 
                self.fecha_inicio <= get_utc_now() and
                self.total_destinatarios > 0)
    
    def iniciar(self):
        """Iniciar campaña"""
        if self.puede_iniciar():
            self.estado = "enviando"
            self.updated_at = get_utc_now()
    
    def pausar(self):
        """Pausar campaña"""
        if self.estado == "enviando":
            self.estado = "pausada"
            self.updated_at = get_utc_now()
    
    def completar(self):
        """Marcar campaña como completada"""
        self.estado = "completada"
        if not self.fecha_fin:
            self.fecha_fin = get_utc_now()
        self.updated_at = get_utc_now()
    
    def __repr__(self):
        return f"<CampanaMensajes {self.nombre} - {self.estado}>"

class EnvioCampanaModel(Base):
    __tablename__ = "envios_campana"
    
    id = Column(Integer, primary_key=True, index=True)
    campana_id = Column(Integer, ForeignKey("campanas_mensajes.id", ondelete="CASCADE"), nullable=False, index=True)
    mensaje_id = Column(Integer, ForeignKey("mensajes.id"), index=True)
    
    # Destinatario
    destinatario_id = Column(Integer, nullable=False, index=True)
    destinatario_tipo = Column(SQLEnum(RolUsuarioEnum), nullable=False, index=True)
    
    # Estado del envío
    estado = Column(String(20), default="pendiente", index=True)  # pendiente, enviado, fallido, leido
    fecha_envio = Column(DateTime, index=True)
    fecha_lectura = Column(DateTime, index=True)
    error_envio = Column(Text)
    intentos = Column(Integer, default=0)
    
    # Variables personalizadas para este destinatario
    variables_personalizadas = Column(Text)  # JSON
    
    created_at = Column(DateTime, default=get_utc_now, index=True)
    
    # Relaciones
    campana = relationship("CampanaMensajesModel", back_populates="envios")
    mensaje = relationship("MensajeModel")
    
    def marcar_como_enviado(self, mensaje_id: int = None):
        """Marcar envío como exitoso"""
        self.estado = "enviado"
        self.fecha_envio = get_utc_now()
        if mensaje_id:
            self.mensaje_id = mensaje_id
    
    def marcar_como_fallido(self, error: str):
        """Marcar envío como fallido"""
        self.estado = "fallido"
        self.error_envio = error
        self.intentos += 1
    
    def marcar_como_leido(self):
        """Marcar como leído"""
        if self.estado == "enviado":
            self.estado = "leido"
            self.fecha_lectura = get_utc_now()
    
    def __repr__(self):
        return f"<EnvioCampana C:{self.campana_id} - {self.destinatario_tipo.value}#{self.destinatario_id}>"

# =============================================
# INTEGRACIONES EXTERNAS
# =============================================

class IntegracionWhatsAppModel(Base):
    __tablename__ = "integraciones_whatsapp"
    
    id = Column(Integer, primary_key=True, index=True)
    mensaje_id = Column(Integer, ForeignKey("mensajes.id"), nullable=False, index=True)
    numero_whatsapp = Column(String(20), nullable=False, index=True)
    
    # Configuración del mensaje
    tipo_mensaje_wa = Column(String(20), default="text")  # text, template, media
    template_nombre = Column(String(100))
    parametros_template = Column(Text)  # JSON array
    media_url = Column(String(500))
    
    # Estado en WhatsApp
    whatsapp_id = Column(String(100), index=True)  # ID asignado por WhatsApp
    estado_wa = Column(String(20), default="pendiente", index=True)  # pendiente, enviado, entregado, leido, fallido
    fecha_estado = Column(DateTime, index=True)
    error_wa = Column(Text)
    
    # Metadatos
    webhook_data = Column(Text)  # JSON con data del webhook
    created_at = Column(DateTime, default=get_utc_now, index=True)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relaciones
    mensaje = relationship("MensajeModel")
    
    def actualizar_estado(self, nuevo_estado: str, whatsapp_id: str = None, error: str = None):
        """Actualizar estado desde webhook de WhatsApp"""
        self.estado_wa = nuevo_estado
        self.fecha_estado = get_utc_now()
        
        if whatsapp_id:
            self.whatsapp_id = whatsapp_id
        
        if error:
            self.error_wa = error
        
        self.updated_at = get_utc_now()
    
    def __repr__(self):
        return f"<IntegracionWhatsApp {self.numero_whatsapp} - {self.estado_wa}>"

# =============================================
# CONFIGURACIÓN DE MENSAJERÍA
# =============================================

class ConfiguracionMensajeriaModel(Base):
    __tablename__ = "configuracion_mensajeria"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    usuario_tipo = Column(SQLEnum(RolUsuarioEnum), nullable=False, index=True)
    
    # Configuraciones de notificaciones
    notificaciones_push = Column(Boolean, default=True)
    sonidos_habilitados = Column(Boolean, default=True)
    vibracion_habilitada = Column(Boolean, default=True)
    
    # Horarios
    horario_no_molestar_inicio = Column(String(5))  # "22:00"
    horario_no_molestar_fin = Column(String(5))  # "08:00"
    dias_no_molestar = Column(String(20))  # JSON array con días
    
    # Tipos de mensaje
    recibir_pedidos = Column(Boolean, default=True)
    recibir_evaluaciones = Column(Boolean, default=True)
    recibir_promociones = Column(Boolean, default=True)
    recibir_sistema = Column(Boolean, default=True)
    
    # Configuración de voz
    idioma_voz = Column(String(10), default="es-ES")
    sensibilidad_voz = Column(DECIMAL(3, 2), default=0.7)
    auto_transcripcion = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    @property
    def en_horario_no_molestar(self):
        """¿Está en horario de no molestar?"""
        if not self.horario_no_molestar_inicio or not self.horario_no_molestar_fin:
            return False
        
        from datetime import time
        hora_actual = datetime.now().time()
        inicio = time.fromisoformat(self.horario_no_molestar_inicio)
        fin = time.fromisoformat(self.horario_no_molestar_fin)
        
        if inicio <= fin:
            return inicio <= hora_actual <= fin
        else:  # Cruza medianoche
            return hora_actual >= inicio or hora_actual <= fin
    
    def __repr__(self):
        return f"<ConfiguracionMensajeria {self.usuario_tipo.value}#{self.usuario_id}>"

# =============================================
# FUNCIONES DE UTILIDAD
# =============================================

def enviar_mensaje_sistema(db, destinatario_id: int, destinatario_tipo: str, titulo: str, contenido: str,
                          tipo_mensaje: str = "mensaje_general", prioridad: str = "normal", 
                          pedido_id: str = None, datos_adicionales: dict = None):
    """Enviar mensaje del sistema"""
    mensaje = MensajeModel(
        remitente_id=0,  # Sistema
        remitente_tipo=RolUsuarioEnum.SUPERVISOR,  # Usar supervisor como sistema
        destinatario_id=destinatario_id,
        destinatario_tipo=RolUsuarioEnum(destinatario_tipo),
        tipo_mensaje=TipoMensajeEnum(tipo_mensaje),
        titulo=titulo,
        contenido=contenido,
        prioridad=prioridad,
        pedido_id=pedido_id,
        datos_adicionales=str(datos_adicionales) if datos_adicionales else None,
        enviado=True
    )
    
    db.add(mensaje)
    db.commit()
    
    return mensaje

def broadcast_mensaje(db, remitente_id: int, remitente_tipo: str, titulo: str, contenido: str,
                     destinatario_tipo: str = None, tipo_mensaje: str = "mensaje_general"):
    """Enviar mensaje broadcast a todos los usuarios de un tipo"""
    mensaje = MensajeModel(
        remitente_id=remitente_id,
        remitente_tipo=RolUsuarioEnum(remitente_tipo),
        destinatario_id=None,  # Broadcast
        destinatario_tipo=RolUsuarioEnum(destinatario_tipo) if destinatario_tipo else None,
        tipo_mensaje=TipoMensajeEnum(tipo_mensaje),
        titulo=titulo,
        contenido=contenido,
        enviado=True
    )
    
    db.add(mensaje)
    db.commit()
    
    return mensaje

def obtener_mensajes_no_leidos(db, usuario_id: int, usuario_tipo: str, limite: int = 50):
    """Obtener mensajes no leídos de un usuario"""
    return db.query(MensajeModel).filter(
        MensajeModel.destinatario_id == usuario_id,
        MensajeModel.destinatario_tipo == RolUsuarioEnum(usuario_tipo),
        MensajeModel.leido == False,
        MensajeModel.enviado == True
    ).order_by(MensajeModel.fecha_envio.desc()).limit(limite).all()

def marcar_mensajes_como_leidos(db, usuario_id: int, usuario_tipo: str, mensaje_ids: list = None):
    """Marcar mensajes como leídos"""
    query = db.query(MensajeModel).filter(
        MensajeModel.destinatario_id == usuario_id,
        MensajeModel.destinatario_tipo == RolUsuarioEnum(usuario_tipo),
        MensajeModel.leido == False
    )
    
    if mensaje_ids:
        query = query.filter(MensajeModel.id.in_(mensaje_ids))
    
    mensajes = query.all()
    timestamp = get_utc_now()
    
    for mensaje in mensajes:
        mensaje.marcar_como_leido(timestamp)
    
    db.commit()
    
    return len(mensajes)

# Corrección:
def limpiar_mensajes_antiguos(db, dias_antiguedad: int = 30):
    """Limpiar mensajes antiguos del sistema"""
    fecha_limite = get_utc_now() - timedelta(days=dias_antiguedad)
    
    mensajes_antiguos = db.query(MensajeModel).filter(
        MensajeModel.fecha_envio < fecha_limite,
        MensajeModel.tipo_mensaje.in_([
            TipoMensajeEnum.MENSAJE_GENERAL,
            TipoMensajeEnum.STOCK_BAJO
        ])
    ).all()
    
    for mensaje in mensajes_antiguos:
        db.delete(mensaje)
    
        db.commit()
    
        return len(mensajes_antiguos)  # Elimina la parte "=get_utc_now, index=True)"

    
    # Relaciones
    pedido = relationship("PedidoModel")
    respuestas = relationship("MensajeModel", backref="mensaje_padre", remote_side=[id])
    
    # Relaciones polimórficas para remitente
    vendedor_remitente = relationship(
        "VendedorModel",
        foreign_keys="[MensajeModel.remitente_id]",
        primaryjoin="and_(MensajeModel.remitente_id==VendedorModel.id, MensajeModel.remitente_tipo=='vendedor')",
        back_populates="mensajes_enviados",
        overlaps="evaluador_remitente,supervisor_remitente"
    )
    
    evaluador_remitente = relationship(
        "EvaluadorModel",
        foreign_keys="[MensajeModel.remitente_id]",
        primaryjoin="and_(MensajeModel.remitente_id==EvaluadorModel.id, MensajeModel.remitente_tipo=='evaluador')",
        back_populates="mensajes_enviados",
        overlaps="vendedor_remitente,supervisor_remitente"
    )
    
    supervisor_remitente = relationship(
        "SupervisorModel",
        foreign_keys="[MensajeModel.remitente_id]",
        primaryjoin="and_(MensajeModel.remitente_id==SupervisorModel.id, MensajeModel.remitente_tipo=='supervisor')",
        back_populates="mensajes_enviados",
        overlaps="vendedor_remitente,evaluador_remitente"
    )
    
    @property
    def es_broadcast(self):
        """¿Es un mensaje broadcast?"""
        return self.destinatario_id is None
    
    @property
    def tiempo_sin_leer(self):
        """Tiempo transcurrido sin leer (en minutos)"""
        if self.leido:
            return 0
        
        delta = get_utc_now() - self.fecha_envio
        return delta.days * 24 * 60 + delta.seconds // 60
    
    @property
    def requiere_atencion(self):
        """¿Requiere atención urgente?"""
        return (not self.leido and 
                (self.prioridad == "urgent" or 
                 self.tiempo_sin_leer > 30 or
                 self.tipo_mensaje == TipoMensajeEnum.EMERGENCIA))
    
    @property
    def remitente_nombre(self):
        """Nombre del remitente"""
        if self.vendedor_remitente:
            return f"{self.vendedor_remitente.nombres} {self.vendedor_remitente.apellidos}"
        elif self.evaluador_remitente:
            return f"{self.evaluador_remitente.nombres} {self.evaluador_remitente.apellidos}"
        elif self.supervisor_remitente:
            return f"{self.supervisor_remitente.nombres} {self.supervisor_remitente.apellidos}"
        else:
            return "Sistema"
    
    def marcar_como_leido(self, timestamp: datetime = None):
        """Marcar mensaje como leído"""
        if not self.leido:
            self.leido = True
            self.fecha_lectura = timestamp or get_utc_now()
    
    def incrementar_intento_envio(self, error: str = None):
        """Incrementar contador de intentos de envío"""
        self.intentos_envio += 1
        if error:
            self.error_envio = error
    
    def marcar_como_enviado(self):
        """Marcar como enviado exitosamente"""
        self.enviado = True
        self.error_envio = None
    
    def __repr__(self):
        return f"<Mensaje {self.tipo_mensaje.value} - {self.remitente_tipo.value}#{self.remitente_id}>"

# =============================================
# CONVERSACIONES DE VOZ
# =============================================

class ConversacionVozModel(Base):
    __tablename__ = "conversaciones_voz"
    
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), index=True)
    vendedor_id = Column(Integer, ForeignKey("vendedores.vendedor_id"), nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    
    # Configuración de la conversación
    metodo_transcripcion = Column(String(50), default="web_speech_api")
    idioma = Column(String(10), default="es-ES")
    calidad_audio = Column(String(20))  # excelente, buena, regular, mala
    
    # Tiempos
    fecha_inicio = Column(DateTime, default=get_utc_now, index=True)
    fecha_fin = Column(DateTime, index=True)
    duracion_segundos = Column(Integer, index=True)
    
    # Análisis
    transcripcion_completa = Column(Text)
    confianza_promedio = Column(DECIMAL(3, 2))  # 0.00 a 1.00
    palabras_clave_detectadas = Column(Text)  # JSON array
    intenciones_detectadas = Column(Text)  # JSON array
    productos_mencionados = Column(Text)  # JSON array
    
    # Estado
    procesamiento_completado = Column(Boolean, default=False, index=True)
    requiere_revision = Column(Boolean, default=False, index=True)
    revisado_por = Column(Integer)
    fecha_revision = Column(DateTime)
    
    created_at = Column(DateTime, default=get_utc_now, index=True)
    
    # Relaciones
    pedido = relationship("PedidoModel")
    vendedor = relationship("VendedorModel", back_populates="conversaciones_voz")
    cliente = relationship("ClienteModel", back_populates="conversaciones_voz")
    transcripciones = relationship("TranscripcionModel", back_populates="conversacion", order_by="TranscripcionModel.timestamp_audio.asc()")
    
    @property
    def duracion_formateada(self):
        """Duración en formato legible"""
        if not self.duracion_segundos:
            return "0s"
        
        minutos = self.duracion_segundos // 60
        segundos = self.duracion_segundos % 60
        
        if minutos > 0:
            return f"{minutos}m {segundos}s"
        else:
            return f"{segundos}s"
    
    @property
    def esta_activa(self):
        """¿La conversación está activa?"""
        return self.fecha_fin is None
    
    @property
    def nivel_confianza(self):
        """Nivel de confianza de la transcripción"""
        if not self.confianza_promedio:
            return "desconocido"
        
        confianza = float(self.confianza_promedio)
        if confianza >= 0.9:
            return "excelente"
        elif confianza >= 0.75:
            return "bueno"
        elif confianza >= 0.6:
            return "regular"
        else:
            return "bajo"
    
    def finalizar(self, timestamp: datetime = None):
        """Finalizar conversación"""
        if not self.esta_activa:
            return
        
        fin = timestamp or get_utc_now()
        self.fecha_fin = fin
        
        if self.fecha_inicio:
            delta = fin - self.fecha_inicio
            self.duracion_segundos = delta.seconds + (delta.days * 24 * 3600)
    
    def generar_transcripcion_completa(self):
        """Generar transcripción completa concatenada"""
        if not self.transcripciones:
            return ""
        
        lineas = []
        for transcripcion in self.transcripciones:
            hablante = transcripcion.hablante.upper()
            texto = transcripcion.texto_procesado or transcripcion.texto_original
            timestamp = f"[{transcripcion.timestamp_audio or 0:.1f}s]"
            lineas.append(f"{timestamp} {hablante}: {texto}")
        
        self.transcripcion_completa = "\n".join(lineas)
        return self.transcripcion_completa
    
    def __repr__(self):
        return f"<ConversacionVoz {self.id} - V:{self.vendedor_id} C:{self.cliente_id} - {self.duracion_formateada}>"

# =============================================
# TRANSCRIPCIONES DE VOZ
# =============================================

class TranscripcionModel(Base):
    __tablename__ = "transcripciones"
    
    id = Column(Integer, primary_key=True, index=True)
    conversacion_id = Column(Integer, ForeignKey("conversaciones_voz.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Identificación del hablante
    hablante = Column(String(20), nullable=False, index=True)  # vendedor, cliente
    
    # Contenido de la transcripción
    texto_original = Column(Text, nullable=False)
    texto_procesado = Column(Text)  # Texto corregido/procesado
    
    # Metadatos de la transcripción
    confianza = Column(DECIMAL(3, 2), index=True)  # 0.00 a 1.00
    timestamp_audio = Column(DECIMAL(8, 2), index=True)  # Segundo en el audio
    idioma_detectado = Column(String(10))
    
    # Análisis del contenido
    palabras_clave = Column(Text)  # JSON array
    emociones_detectadas = Column(Text)  # JSON object
    intenciones = Column(Text)  # JSON array
    productos_mencionados = Column(Text)  # JSON array
    cantidades_detectadas = Column(Text)  # JSON array
    
    # Control de calidad
    editado = Column(Boolean, default=False, index=True)
    editado_por = Column(Integer)
    fecha_edicion = Column(DateTime)
    requiere_revision = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=get_utc_now, index=True)
    #created_at = Column(DateTime, default  