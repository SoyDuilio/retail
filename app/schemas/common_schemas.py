# app/schemas/common_schemas.py - COMPLETO
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Union, Generic, TypeVar
from datetime import datetime, timezone
from enum import Enum

# Función auxiliar para obtener la hora actual en UTC
def get_utc_now():
    return datetime.now(timezone.utc)

# =============================================
# TIPOS GENÉRICOS
# =============================================

DataT = TypeVar('DataT')

# =============================================
# ENUMS
# =============================================

class RolUsuario(str, Enum):
    VENDEDOR = "vendedor"
    EVALUADOR = "evaluador" 
    SUPERVISOR = "supervisor"
    CLIENTE = "cliente"

class TipoUsuario(str, Enum):
    VENDEDOR = "vendedor"
    EVALUADOR = "evaluador" 
    SUPERVISOR = "supervisor"
    CLIENTE = "cliente"

class EstadoPedido(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    PREPARANDO = "preparando"
    EN_RUTA = "en_ruta"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"
    DEVUELTO = "devuelto"

class TipoVenta(str, Enum):
    """Tipo de venta del pedido"""
    EXTERNA = "EXTERNA"
    INTERNA = "INTERNA"

class TipoPago(str, Enum):
    """Tipo de pago del pedido"""
    CONTADO = "CONTADO"
    CREDITO = "CREDITO"
    YAPE = "YAPE"
    PLIN = "PLIN"

class TipoMensaje(str, Enum):
    TEXTO = "texto"
    VOZ = "voz"
    IMAGEN = "imagen"
    UBICACION = "ubicacion"
    PEDIDO = "pedido"
    SISTEMA = "sistema"

class EstadoMensaje(str, Enum):
    ENVIADO = "enviado"
    ENTREGADO = "entregado"
    LEIDO = "leido"
    ERROR = "error"

class CategoriaProducto(str, Enum):
    BEBIDAS = "bebidas"
    SNACKS = "snacks"
    LACTEOS = "lacteos"
    PANADERIA = "panaderia"
    LIMPIEZA = "limpieza"
    CUIDADO_PERSONAL = "cuidado_personal"
    OTROS = "otros"

class UnidadMedida(str, Enum):
    UNIDAD = "unidad"
    KILOGRAMO = "kg"
    GRAMO = "g"
    LITRO = "l"
    MILILITRO = "ml"
    CAJA = "caja"
    PAQUETE = "paquete"
    DOCENA = "docena"

class TipoCliente(str, Enum):
    BODEGA = "bodega"
    MINIMARKET = "minimarket"
    RESTAURANTE = "restaurante"
    INSTITUCION = "institucion"
    MAYORISTA = "mayorista"
    OTRO = "otro"

class EstadoStock(str, Enum):
    DISPONIBLE = "disponible"
    AGOTADO = "agotado"
    BAJO_STOCK = "bajo_stock"
    DESCONTINUADO = "descontinuado"
    EN_PEDIDO = "en_pedido"

class EstadoEvaluacion(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROCESO = "en_proceso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=get_utc_now)

# =============================================
# RESPONSES BÁSICAS
# =============================================

class BaseResponse(BaseModel):
    """Respuesta base para todas las APIs"""
    success: bool = True
    message: str = "Operación exitosa"
    timestamp: datetime = Field(default_factory=get_utc_now)

class Response(BaseResponse):
    """Respuesta simple - alias de BaseResponse"""
    pass

class DataResponse(BaseResponse, Generic[DataT]):
    """Respuesta con datos específicos"""
    data: Optional[DataT] = None

class ListResponse(BaseResponse, Generic[DataT]):
    """Respuesta para listas paginadas"""
    data: List[DataT] = []
    total: int = 0
    page: int = 1
    per_page: int = 20
    total_pages: int = 0
    
    @field_validator('total_pages', mode='before')
    @classmethod
    def calculate_total_pages(cls, v, info):
        values = info.data
        per_page = values.get('per_page', 20)
        total = values.get('total', 0)
        return max(1, (total + per_page - 1) // per_page)

class PaginatedResponse(ListResponse[DataT]):
    """Respuesta paginada - alias de ListResponse"""
    pass

class ErrorResponse(BaseResponse):
    """Respuesta para errores"""
    success: bool = False
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

# =============================================
# LOGIN Y AUTENTICACIÓN
# =============================================

class LoginRequest(BaseModel):
    """Solicitud de login"""
    usuario: str      # Cambiar identifier por usuario
    clave: str        # Cambiar password por clave  
    tipo_usuario: str

class LoginResponse(BaseModel):
    """Respuesta exitosa de login"""
    success: bool = True           # ← AGREGAR
    token: str                     # ← CAMBIAR access_token por token
    access_token: str              # ← Mantener ambos por compatibilidad
    token_type: str = "bearer"
    expires_in: int
    usuario_id: int                # ← AGREGAR
    usuario_tipo: str             # ← AGREGAR  
    nombre_completo: str          # ← AGREGAR
    user_info: Dict[str, Any]
    session_id: str
    redirect_url: Optional[str] = None  # ← AGREGAR
    mensaje: str = "Login exitoso"      # ← AGREGAR

class TokenInfo(BaseModel):
    """Información del token de acceso"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos
    refresh_token: Optional[str] = None
    user_info: Optional[Dict[str, Any]] = None

# =============================================
# FILTROS COMUNES
# =============================================

class PaginationParams(BaseModel):
    """Parámetros de paginación"""
    page: int = Field(default=1, ge=1, description="Número de página")
    per_page: int = Field(default=20, ge=1, le=100, description="Elementos por página")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page
    
    @property
    def limit(self) -> int:
        return self.per_page

class DateRangeFilter(BaseModel):
    """Filtro por rango de fechas"""
    fecha_desde: Optional[datetime] = Field(None, description="Fecha inicial")
    fecha_hasta: Optional[datetime] = Field(None, description="Fecha final")
    
    @field_validator('fecha_hasta')
    @classmethod
    def validate_date_range(cls, v, info):
        values = info.data
        if v and 'fecha_desde' in values and values['fecha_desde']:
            if v < values['fecha_desde']:
                raise ValueError('La fecha final debe ser posterior a la inicial')
        return v

class LocationFilter(BaseModel):
    """Filtro por ubicación geográfica"""
    distrito: Optional[str] = None
    provincia: Optional[str] = None
    departamento: Optional[str] = None

class SearchFilter(BaseModel):
    """Filtro de búsqueda general"""
    q: Optional[str] = Field(None, min_length=2, max_length=100, description="Término de búsqueda")
    activo: Optional[bool] = Field(None, description="Filtrar por estado activo")

class FiltrosProductos(BaseModel):
    """Filtros específicos para productos"""
    categoria: Optional[CategoriaProducto] = None
    precio_min: Optional[float] = Field(None, ge=0)
    precio_max: Optional[float] = Field(None, ge=0)
    disponible: Optional[bool] = None
    q: Optional[str] = Field(None, min_length=2, max_length=100)

class FiltrosPedidos(BaseModel):
    """Filtros específicos para pedidos"""
    estado: Optional[EstadoPedido] = None
    vendedor_id: Optional[int] = None
    cliente_id: Optional[int] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    monto_min: Optional[float] = Field(None, ge=0)
    monto_max: Optional[float] = Field(None, ge=0)

# =============================================
# UBICACIÓN Y GEOLOCALIZACIÓN
# =============================================

class Coordenadas(BaseModel):
    """Coordenadas geográficas"""
    latitud: float = Field(..., ge=-90, le=90, description="Latitud")
    longitud: float = Field(..., ge=-180, le=180, description="Longitud")
    precision: Optional[float] = Field(None, ge=0, description="Precisión en metros")
    timestamp: Optional[datetime] = Field(default_factory=get_utc_now)

class Direccion(BaseModel):
    """Dirección completa"""
    direccion_completa: str = Field(..., min_length=5, max_length=500)
    referencia: Optional[str] = Field(None, max_length=200)
    distrito: str = Field(..., min_length=2, max_length=100)
    provincia: str = Field(..., min_length=2, max_length=100) 
    departamento: str = Field(..., min_length=2, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    coordenadas: Optional[Coordenadas] = None

# =============================================
# MODELOS DE RESPUESTA PARA API
# =============================================

class Vendedor(BaseModel):
    """Modelo de respuesta para vendedores"""
    vendedor_id: int
    dni: str
    codigo_vendedor: str
    nombre: str
    apellidos: str
    telefono: str
    email: Optional[str] = None
    activo: bool
    verificado: bool
    fecha_registro: datetime
    ultima_conexion: Optional[datetime] = None
    latitud_actual: Optional[float] = None
    longitud_actual: Optional[float] = None

class Evaluador(BaseModel):
    """Modelo de respuesta para evaluadores"""
    evaluador_id: int
    dni: str
    codigo_evaluador: str
    nombre: str
    apellidos: str
    telefono: str
    email: Optional[str] = None
    activo: bool
    verificado: bool
    fecha_registro: datetime
    ultima_conexion: Optional[datetime] = None

class Supervisor(BaseModel):
    """Modelo de respuesta para supervisores"""
    supervisor_id: int
    dni: str
    codigo_supervisor: str
    nombre: str
    apellidos: str
    telefono: str
    email: Optional[str] = None
    cargo: Optional[str] = None
    nivel_acceso: str
    activo: bool
    verificado: bool
    fecha_registro: datetime

class Cliente(BaseModel):
    """Modelo de respuesta para clientes"""
    cliente_id: int
    codigo_cliente: str
    nombre_comercial: str
    razon_social: Optional[str] = None
    ruc: Optional[str] = None
    tipo_cliente: TipoCliente
    telefono: str
    email: Optional[str] = None
    direccion_completa: str
    distrito: str
    provincia: str
    departamento: str
    activo: bool
    fecha_registro: datetime

class ProductoPrecio(BaseModel):
    """Modelo para productos con precios"""
    producto_id: int
    codigo_producto: str
    nombre: str
    descripcion: Optional[str] = None
    categoria: CategoriaProducto
    unidad_medida: UnidadMedida
    precio_unitario: float
    precio_mayorista: Optional[float] = None
    stock_disponible: int
    activo: bool
    imagen_url: Optional[str] = None

# =============================================
# MODELOS DE CREACIÓN
# =============================================

class PedidoCreate(BaseModel):
    """Modelo para crear pedidos"""
    cliente_id: int
    items: List[Dict[str, Any]] = Field(..., min_length=1)
    observaciones: Optional[str] = None
    coordenadas_entrega: Optional[Coordenadas] = None

# =============================================
# CÁLCULOS Y PRECIOS
# =============================================

class CalculoPrecio(BaseModel):
    """Cálculo de precios para items"""
    producto_id: int
    cantidad: int
    precio_unitario: float
    descuento_porcentaje: float = 0.0
    subtotal: float
    descuento_aplicado: float = 0.0
    total_item: float

class ResultadoPrecio(BaseModel):
    """Resultado completo de cálculo de precios"""
    items: List[CalculoPrecio]
    subtotal_general: float
    descuento_general: float = 0.0
    impuestos: float = 0.0
    total_pedido: float
    moneda: str = "PEN"

# =============================================
# KDS (KITCHEN DISPLAY SYSTEM)
# =============================================

class KDSPedido(BaseModel):
    """Pedido para el sistema KDS"""
    pedido_id: int
    numero_pedido: str
    cliente_nombre: str
    vendedor_nombre: str
    estado: EstadoPedido
    items: List[Dict[str, Any]]
    tiempo_estimado: Optional[int] = None  # minutos
    prioridad: int = 1  # 1=normal, 2=alta, 3=urgente
    observaciones: Optional[str] = None
    fecha_pedido: datetime
    fecha_estimada_entrega: Optional[datetime] = None

# =============================================
# CALIFICACIONES Y EVALUACIONES
# =============================================

class CalificacionUpdate(BaseModel):
    """Actualización de calificación"""
    calificacion: int = Field(..., ge=1, le=5, description="Calificación de 1 a 5")
    comentarios: Optional[str] = Field(None, max_length=500)
    aspectos_calificados: Optional[Dict[str, int]] = None  # {aspecto: puntuacion}

# =============================================
# DASHBOARD Y MÉTRICAS
# =============================================

class DashboardMetricas(BaseModel):
    """Métricas para dashboard"""
    total_pedidos_hoy: int = 0
    total_ventas_hoy: float = 0.0
    pedidos_pendientes: int = 0
    pedidos_completados: int = 0
    vendedores_activos: int = 0
    clientes_atendidos_hoy: int = 0
    promedio_calificacion: float = 0.0
    crecimiento_ventas_porcentaje: float = 0.0

class RankingVendedor(BaseModel):
    """Ranking de vendedores"""
    vendedor_id: int
    nombre_completo: str
    codigo_vendedor: str
    total_ventas: float
    total_pedidos: int
    promedio_calificacion: float
    clientes_unicos: int
    posicion_ranking: int

# =============================================
# MENSAJES Y COMUNICACIÓN
# =============================================

class Mensaje(BaseModel):
    """Mensaje básico"""
    mensaje_id: Optional[int] = None
    remitente_id: int
    destinatario_id: int
    tipo_mensaje: TipoMensaje
    contenido: str
    estado: EstadoMensaje = EstadoMensaje.ENVIADO
    fecha_envio: datetime = Field(default_factory=get_utc_now)
    metadata: Optional[Dict[str, Any]] = None

class ConversacionVozCreate(BaseModel):
    """Crear conversación de voz"""
    vendedor_id: int
    cliente_id: int
    duracion_segundos: float
    archivo_audio_url: str
    transcripcion_inicial: Optional[str] = None
    idioma_detectado: str = "es"

class TranscripcionCreate(BaseModel):
    """Crear transcripción de audio"""
    archivo_audio_url: str
    idioma_origen: str = "es"
    confianza_minima: float = 0.7
    incluir_timestamps: bool = True

# =============================================
# CONFIGURACIONES
# =============================================

class ConfiguracionItem(BaseModel):
    """Item de configuración individual"""
    clave: str = Field(..., min_length=1, max_length=100)
    valor: Union[str, int, float, bool, Dict, List]
    tipo: str = Field(default="string", pattern="^(string|int|float|boolean|json)$")
    descripcion: Optional[str] = None
    categoria: Optional[str] = None

# =============================================
# NOTIFICACIONES
# =============================================

class TipoNotificacion(str, Enum):
    INFO = "info"
    ALERTA = "alerta" 
    ERROR = "error"
    EXITO = "exito"
    PEDIDO = "pedido"
    MENSAJE = "mensaje"
    SISTEMA = "sistema"

class NotificacionBase(BaseModel):
    """Base para notificaciones"""
    titulo: str = Field(..., min_length=1, max_length=100)
    mensaje: str = Field(..., min_length=1, max_length=500)
    tipo: TipoNotificacion = TipoNotificacion.INFO
    data_extra: Optional[Dict[str, Any]] = None

# =============================================
# ARCHIVOS Y MULTIMEDIA
# =============================================

class ArchivoBase(BaseModel):
    """Base para archivos subidos"""
    nombre_archivo: str
    tipo_mime: str
    tamano_bytes: int
    url: Optional[str] = None
    hash_archivo: Optional[str] = None

# =============================================
# ESTADÍSTICAS COMUNES
# =============================================

class EstadisticasBase(BaseModel):
    """Estadísticas básicas"""
    total: int = 0
    activos: int = 0
    inactivos: int = 0
    porcentaje_activos: float = 0.0
    
    @field_validator('porcentaje_activos', mode='before')
    @classmethod
    def calculate_percentage(cls, v, info):
        values = info.data
        total = values.get('total', 0)
        activos = values.get('activos', 0)
        if total > 0:
            return round((activos / total) * 100, 2)
        return 0.0

# =============================================
# UTILIDADES
# =============================================

class HealthCheck(BaseModel):
    """Respuesta de health check"""
    status: str = "ok"
    timestamp: datetime = Field(default_factory=get_utc_now)
    version: str = "1.0.0"
    database_status: str = "connected"

# =============================================
# VALIDADORES COMUNES
# =============================================

def validate_dni(dni: str) -> str:
    """Valida formato de DNI peruano"""
    if not dni or len(dni) != 8 or not dni.isdigit():
        raise ValueError('DNI debe tener exactamente 8 dígitos')
    return dni

def validate_telefono(telefono: str) -> str:
    """Valida formato de teléfono peruano"""
    # Remover espacios y caracteres especiales
    clean_phone = ''.join(filter(str.isdigit, telefono))
    if len(clean_phone) < 9 or len(clean_phone) > 11:
        raise ValueError('Teléfono debe tener entre 9 y 11 dígitos')
    return clean_phone

def validate_email(email: str) -> str:
    """Validación adicional de email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError('Formato de email inválido')
    return email.lower()