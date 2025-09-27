# app/schemas/message_schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid

from .common_schemas import TipoMensaje, RolUsuario

# =============================================
# MENSAJES BASE
# =============================================

class MensajeBase(BaseModel):
    remitente_id: int
    remitente_tipo: RolUsuario
    destinatario_id: Optional[int] = None
    destinatario_tipo: Optional[RolUsuario] = None
    tipo_mensaje: TipoMensaje
    titulo: str = Field(..., max_length=200)
    contenido: str
    pedido_id: Optional[uuid.UUID] = None
    datos_adicionales: Optional[Dict[str, Any]] = None
    prioridad: str = Field(default="normal")  # normal, high, urgent
    sonido: bool = True

    @validator('titulo')
    def validate_titulo(cls, v):
        if not v.strip():
            raise ValueError('Título no puede estar vacío')
        return v.strip()

    @validator('contenido')
    def validate_contenido(cls, v):
        if not v.strip():
            raise ValueError('Contenido no puede estar vacío')
        return v.strip()

class MensajeCreate(MensajeBase):
    pass

class MensajeUpdate(BaseModel):
    titulo: Optional[str] = Field(None, max_length=200)
    contenido: Optional[str] = None
    leido: Optional[bool] = None
    datos_adicionales: Optional[Dict[str, Any]] = None

class Mensaje(MensajeBase):
    id: int
    leido: bool = False
    enviado: bool = False
    fecha_envio: datetime
    fecha_lectura: Optional[datetime] = None
    intentos_envio: int = 0
    error_envio: Optional[str] = None

    class Config:
        from_attributes = True

# =============================================
# NOTIFICACIONES PUSH
# =============================================

class NotificacionPush(BaseModel):
    usuario_id: int
    usuario_tipo: RolUsuario
    titulo: str = Field(..., max_length=200)
    mensaje: str
    data: Optional[Dict[str, Any]] = None
    sonido: bool = True
    vibrar: bool = True
    icono: Optional[str] = None
    imagen: Optional[str] = None
    accion_url: Optional[str] = None
    tiempo_vida: int = Field(default=24)  # horas antes de expirar

class NotificacionResponse(BaseModel):
    success: bool
    notification_id: Optional[str] = None
    enviado_a: int
    mensaje: str
    timestamp: datetime

# =============================================
# CONVERSACIONES DE VOZ
# =============================================

class ConversacionVozBase(BaseModel):
    pedido_id: Optional[uuid.UUID] = None
    vendedor_id: int
    cliente_id: int
    metodo_transcripcion: str = Field(default="web_speech_api")
    idioma: str = Field(default="es-ES")

    @validator('metodo_transcripcion')
    def validate_metodo(cls, v):
        metodos_validos = ["web_speech_api", "google_speech_to_text", "amazon_transcribe"]
        if v not in metodos_validos:
            raise ValueError(f'Método debe ser uno de: {metodos_validos}')
        return v

class ConversacionVozCreate(ConversacionVozBase):
    pass

class ConversacionVoz(ConversacionVozBase):
    id: int
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    duracion_segundos: Optional[int] = None
    calidad_audio: Optional[str] = None  # excelente, buena, regular, mala
    transcripcion_completa: Optional[str] = None
    confianza_promedio: Optional[Decimal] = None

    class Config:
        from_attributes = True

# =============================================
# TRANSCRIPCIONES
# =============================================

class TranscripcionBase(BaseModel):
    conversacion_id: int
    hablante: str = Field(..., regex="^(vendedor|cliente)$")
    texto_original: str
    texto_procesado: Optional[str] = None
    confianza: Optional[Decimal] = Field(None, ge=0, le=1, decimal_places=2)
    timestamp_audio: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    idioma_detectado: Optional[str] = None
    palabras_clave: Optional[List[str]] = None

    @validator('texto_original')
    def validate_texto(cls, v):
        if not v.strip():
            raise ValueError('Texto original no puede estar vacío')
        return v.strip()

class TranscripcionCreate(TranscripcionBase):
    pass

class TranscripcionUpdate(BaseModel):
    texto_procesado: Optional[str] = None
    palabras_clave: Optional[List[str]] = None

class Transcripcion(TranscripcionBase):
    id: int
    created_at: datetime
    editado: bool = False
    editado_por: Optional[int] = None

    class Config:
        from_attributes = True

# =============================================
# ANÁLISIS DE VOZ Y PROCESAMIENTO
# =============================================

class AnalisisVoz(BaseModel):
    conversacion_id: int
    productos_mencionados: List[str]
    cantidades_detectadas: List[int]
    intenciones: List[str]  # comprar, consultar, cancelar, etc.
    sentimiento: str  # positivo, neutro, negativo
    confianza_analisis: Decimal = Field(ge=0, le=1, decimal_places=2)
    requiere_revision: bool = False

class ComandosVoz(BaseModel):
    """Comandos de voz reconocidos del sistema"""
    comando: str
    accion: str
    parametros: Optional[Dict[str, Any]] = None
    confianza: Decimal
    ejecutado: bool = False

class ConfiguracionVoz(BaseModel):
    idioma_principal: str = "es-ES"
    idiomas_secundarios: List[str] = ["en-US"]
    sensibilidad: Decimal = Field(default=0.7, ge=0, le=1)
    filtro_ruido: bool = True
    auto_puntuacion: bool = True
    palabras_personalizadas: List[str] = []

# =============================================
# CHAT EN TIEMPO REAL
# =============================================

class MensajeChat(BaseModel):
    conversacion_id: Optional[str] = None
    remitente_id: int
    remitente_tipo: RolUsuario
    destinatario_id: int
    destinatario_tipo: RolUsuario
    mensaje: str
    tipo_mensaje: str = "texto"  # texto, voz, imagen, ubicacion
    archivo_adjunto: Optional[str] = None
    ubicacion_lat: Optional[Decimal] = None
    ubicacion_lng: Optional[Decimal] = None
    responder_a: Optional[int] = None  # ID del mensaje al que responde

class EstadoChat(BaseModel):
    usuario_id: int
    usuario_tipo: RolUsuario
    estado: str = "online"  # online, offline, ocupado, ausente
    ultimo_visto: datetime
    escribiendo: bool = False

class ConversacionChat(BaseModel):
    id: str
    participantes: List[Dict[str, Any]]
    ultimo_mensaje: Optional[MensajeChat] = None
    mensajes_no_leidos: int = 0
    activa: bool = True
    created_at: datetime

# =============================================
# PLANTILLAS DE MENSAJES
# =============================================

class PlantillaMensaje(BaseModel):
    id: int
    nombre: str
    categoria: str  # bienvenida, seguimiento, promocion, etc.
    titulo_template: str
    contenido_template: str
    variables: List[str]  # {nombre_cliente}, {monto}, etc.
    tipo_usuario: Optional[RolUsuario] = None  # Para qué tipo de usuario es
    activa: bool = True

class MensajeDePlantilla(BaseModel):
    plantilla_id: int
    destinatario_id: int
    destinatario_tipo: RolUsuario
    variables_valores: Dict[str, str]
    programar_envio: Optional[datetime] = None

# =============================================
# CAMPAÑAS DE MENSAJERÍA
# =============================================

class CampanaMensajes(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    plantilla_id: int
    destinatarios: List[Dict[str, Any]]  # Lista de usuarios target
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    estado: str = "borrador"  # borrador, programada, enviando, completada, pausada
    enviados: int = 0
    exitosos: int = 0
    fallidos: int = 0

class ResultadoCampana(BaseModel):
    campana_id: int
    total_destinatarios: int
    mensajes_enviados: int
    mensajes_exitosos: int
    mensajes_fallidos: int
    tasa_exito: Decimal
    errores: List[str]

# =============================================
# FILTROS Y CONSULTAS
# =============================================

class FiltrosMensajes(BaseModel):
    remitente_id: Optional[int] = None
    remitente_tipo: Optional[RolUsuario] = None
    destinatario_id: Optional[int] = None
    destinatario_tipo: Optional[RolUsuario] = None
    tipo_mensaje: Optional[TipoMensaje] = None
    leido: Optional[bool] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    pedido_id: Optional[uuid.UUID] = None
    buscar: Optional[str] = None
    prioridad: Optional[str] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

class FiltrosConversaciones(BaseModel):
    usuario_id: int
    usuario_tipo: RolUsuario
    activas_solo: bool = True
    con_no_leidos: Optional[bool] = None
    fecha_desde: Optional[datetime] = None

# =============================================
# ESTADÍSTICAS Y REPORTES
# =============================================

class EstadisticasMensajeria(BaseModel):
    total_mensajes: int
    mensajes_enviados: int
    mensajes_leidos: int
    mensajes_pendientes: int
    tasa_lectura: Decimal
    tiempo_promedio_respuesta: int  # minutos
    usuarios_activos: int
    conversaciones_activas: int

class ReporteMensajeria(BaseModel):
    periodo: str
    mensajes_por_tipo: Dict[str, int]
    mensajes_por_usuario: List[Dict[str, Any]]
    conversaciones_iniciadas: int
    tiempo_respuesta_promedio: int
    satisfaccion_promedio: Optional[Decimal] = None

# =============================================
# WEBHOOKS Y INTEGRACIONES
# =============================================

class WebhookMensaje(BaseModel):
    evento: str  # mensaje_enviado, mensaje_leido, conversacion_iniciada
    timestamp: datetime
    usuario_id: int
    usuario_tipo: RolUsuario
    datos: Dict[str, Any]
    url_callback: Optional[str] = None

class IntegracionWhatsApp(BaseModel):
    """Para integración con WhatsApp Business API"""
    numero_whatsapp: str
    mensaje: str
    tipo_mensaje: str = "text"
    adjunto_url: Optional[str] = None
    plantilla_nombre: Optional[str] = None
    parametros_plantilla: Optional[List[str]] = None

class EstadoWhatsApp(BaseModel):
    numero: str
    estado: str  # enviado, entregado, leido, fallido
    timestamp: datetime
    error: Optional[str] = None

# =============================================
# CONFIGURACIÓN Y ADMINISTRACIÓN
# =============================================

class ConfiguracionMensajeria(BaseModel):
    notificaciones_push_habilitadas: bool = True
    sonidos_habilitados: bool = True
    horario_no_molestar_inicio: Optional[str] = None  # "22:00"
    horario_no_molestar_fin: Optional[str] = None  # "08:00"
    max_intentos_envio: int = 3
    tiempo_expiracion_horas: int = 24
    webhook_url: Optional[str] = None

class LogMensaje(BaseModel):
    """Para auditoría y debugging"""
    mensaje_id: int
    accion: str  # creado, enviado, leido, fallido
    timestamp: datetime
    detalles: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None