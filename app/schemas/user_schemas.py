# app/schemas/user_schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
from .common_schemas import RolUsuario

# Función auxiliar para obtener la hora actual en UTC
def get_utc_now():
    return datetime.now(timezone.utc)

# =============================================
# VENDEDORES
# =============================================

class VendedorBase(BaseModel):
    dni: str = Field(..., min_length=8, max_length=8)
    nombres: str = Field(..., max_length=100)
    apellidos: str = Field(..., max_length=100)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    activo: bool = True

    @field_validator('dni')
    def validate_dni(cls, v):
        if not v.isdigit():
            raise ValueError('DNI debe contener solo números')
        return v

class VendedorCreate(VendedorBase):
    pass

class VendedorUpdate(BaseModel):
    nombres: Optional[str] = Field(None, max_length=100)
    apellidos: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    activo: Optional[bool] = None

class Vendedor(VendedorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class VendedorStats(BaseModel):
    vendedor_id: int
    vendedor_nombre: str
    vendedor_dni: str
    pedidos_hoy: int
    ventas_hoy: Decimal
    pedidos_pendientes: int
    pedidos_aprobados: int
    tasa_aprobacion: Decimal
    promedio_pedido: Decimal

class VendedorDashboard(BaseModel):
    vendedor: Vendedor
    stats: VendedorStats
    ubicacion_actual: Optional[dict] = None
    estado_conexion: str = "offline"

# =============================================
# EVALUADORES
# =============================================

class EvaluadorBase(BaseModel):
    dni: str = Field(..., min_length=8, max_length=8)
    nombres: str = Field(..., max_length=100)
    apellidos: str = Field(..., max_length=100)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    activo: bool = True

    @field_validator('dni')
    def validate_dni(cls, v):
        if not v.isdigit():
            raise ValueError('DNI debe contener solo números')
        return v

class EvaluadorCreate(EvaluadorBase):
    pass

class EvaluadorUpdate(BaseModel):
    nombres: Optional[str] = Field(None, max_length=100)
    apellidos: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    activo: Optional[bool] = None

class Evaluador(EvaluadorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EvaluadorStats(BaseModel):
    evaluador_id: int
    evaluador_nombre: str
    evaluador_dni: str
    evaluaciones_hoy: int
    evaluaciones_pendientes: int
    evaluaciones_aprobadas: int
    evaluaciones_rechazadas: int
    tiempo_promedio_evaluacion: int  # segundos
    tasa_aprobacion: Decimal

class EvaluadorKDS(BaseModel):
    evaluador: Evaluador
    stats: EvaluadorStats
    pedidos_pendientes: int
    tiempo_sesion: int  # minutos conectado

# =============================================
# SUPERVISORES
# =============================================

class SupervisorBase(BaseModel):
    dni: str = Field(..., min_length=8, max_length=8)
    nombres: str = Field(..., max_length=100)
    apellidos: str = Field(..., max_length=100)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    activo: bool = True

    @field_validator('dni')
    def validate_dni(cls, v):
        if not v.isdigit():
            raise ValueError('DNI debe contener solo números')
        return v

class SupervisorCreate(SupervisorBase):
    pass

class SupervisorUpdate(BaseModel):
    nombres: Optional[str] = Field(None, max_length=100)
    apellidos: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    activo: Optional[bool] = None

class Supervisor(SupervisorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SupervisorDashboard(BaseModel):
    supervisor: Supervisor
    metricas_generales: dict
    vendedores_activos: int
    evaluadores_activos: int
    alertas_pendientes: int

# =============================================
# AUTENTICACIÓN
# =============================================

class LoginRequest(BaseModel):
    usuario: str  # DNI para trabajadores, RUC para clientes
    clave: str    # DNI para trabajadores, RUC para clientes
    tipo_usuario: RolUsuario
    ubicacion_lat: Optional[float] = Field(None, ge=-90, le=90)
    ubicacion_lng: Optional[float] = Field(None, ge=-180, le=180)

    @field_validator('usuario')
    def validate_usuario_format(cls, v, values):
        tipo_usuario = values.get('tipo_usuario')
        if tipo_usuario in ['vendedor', 'evaluador', 'supervisor']:
            # Validar DNI (8 dígitos)
            if len(v) != 8 or not v.isdigit():
                raise ValueError('DNI debe tener 8 dígitos numéricos')
        elif tipo_usuario == 'cliente':
            # Validar RUC (11 dígitos)
            if len(v) != 11 or not v.isdigit():
                raise ValueError('RUC debe tener 11 dígitos numéricos')
        return v

class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    usuario_id: Optional[int] = None
    usuario_tipo: Optional[RolUsuario] = None
    nombre_completo: Optional[str] = None
    redirect_url: Optional[str] = None
    mensaje: Optional[str] = None
    expires_at: Optional[datetime] = None

class TokenData(BaseModel):
    usuario_id: Optional[int] = None
    usuario_tipo: Optional[str] = None
    dni_ruc: Optional[str] = None

class UserProfile(BaseModel):
    id: int
    tipo: RolUsuario
    nombre_completo: str
    dni_ruc: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    activo: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str

    @field_validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Las contraseñas no coinciden')
        return v

# =============================================
# SESIONES Y ACTIVIDAD
# =============================================

class SesionActiva(BaseModel):
    id: int
    usuario_id: int
    usuario_tipo: RolUsuario
    token_session: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    ubicacion_lat: Optional[str] = None
    ubicacion_lng: Optional[str] = None
    ultimo_ping: datetime
    created_at: datetime
    expires_at: datetime
    activa: bool = True

    class Config:
        from_attributes = True

class ActividadUsuario(BaseModel):
    id: int
    usuario_id: int
    usuario_tipo: RolUsuario
    accion: str
    detalles: Optional[str] = None
    ip_address: Optional[str] = None
    ubicacion_lat: Optional[str] = None
    ubicacion_lng: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class CreateSessionRequest(BaseModel):
    usuario_id: int
    usuario_tipo: RolUsuario
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    ubicacion_lat: Optional[float] = None
    ubicacion_lng: Optional[float] = None
    expires_hours: int = Field(default=8, ge=1, le=24)

# =============================================
# RANKINGS Y REPORTES
# =============================================

class RankingVendedor(BaseModel):
    posicion: int
    vendedor_id: int
    vendedor_nombre: str
    vendedor_dni: str
    total_pedidos: int
    total_ventas: Decimal
    promedio_pedido: Decimal
    pedidos_aprobados: int
    tasa_aprobacion: Decimal
    puntuacion: Decimal

class RankingEvaluador(BaseModel):
    posicion: int
    evaluador_id: int
    evaluador_nombre: str
    evaluador_dni: str
    total_evaluaciones: int
    evaluaciones_aprobadas: int
    tasa_aprobacion: Decimal
    tiempo_promedio: int  # segundos
    eficiencia_score: Decimal

class ReporteUsuarios(BaseModel):
    total_vendedores: int
    vendedores_activos: int
    total_evaluadores: int
    evaluadores_activos: int
    total_supervisores: int
    supervisores_activos: int
    sesiones_activas: int
    ultimo_reporte: datetime

# =============================================
# FILTROS ESPECÍFICOS
# =============================================

class FiltroVendedores(BaseModel):
    activo: Optional[bool] = None
    buscar: Optional[str] = Field(None, min_length=2)
    dni: Optional[str] = Field(None, min_length=8, max_length=8)
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

class FiltroEvaluadores(BaseModel):
    activo: Optional[bool] = None
    buscar: Optional[str] = Field(None, min_length=2)
    dni: Optional[str] = Field(None, min_length=8, max_length=8)
    con_evaluaciones: Optional[bool] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

# =============================================
# NOTIFICACIONES DE USUARIOS
# =============================================

class NotificacionUsuario(BaseModel):
    id: int
    usuario_id: int
    usuario_tipo: RolUsuario
    titulo: str
    mensaje: str
    tipo: str  # info, success, warning, error
    leida: bool = False
    fecha_envio: datetime
    fecha_lectura: Optional[datetime] = None

    class Config:
        from_attributes = True

class CreateNotificacion(BaseModel):
    usuario_id: int
    usuario_tipo: RolUsuario
    titulo: str = Field(..., max_length=200)
    mensaje: str
    tipo: str = Field(default="info")
    sonido: bool = True

# =============================================
# ESTADÍSTICAS GENERALES
# =============================================

class EstadisticasGenerales(BaseModel):
    usuarios_registrados: int
    usuarios_activos_hoy: int
    sesiones_activas: int
    promedio_tiempo_sesion: int  # minutos
    pico_usuarios_simultaneos: int
    fecha_reporte: datetime



# AGREGAR ESTAS CLASES AL FINAL DE app/schemas/user_schemas.py

# =============================================
# SCHEMAS DE RESPUESTA 
# =============================================

class VendedorResponse(BaseModel):
    """Schema de respuesta para vendedor"""
    vendedor_id: int
    dni: str
    codigo_vendedor: str
    nombre: str
    apellidos: str
    telefono: str
    email: Optional[str] = None
    direccion: Optional[str] = None
    distrito: Optional[str] = None
    provincia: Optional[str] = None
    departamento: Optional[str] = None
    activo: bool
    verificado: bool
    fecha_registro: datetime
    ultima_conexion: Optional[datetime] = None
    latitud_actual: Optional[float] = None
    longitud_actual: Optional[float] = None
    precision_gps: Optional[float] = None
    ultima_ubicacion: Optional[datetime] = None
    configuraciones: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class EvaluadorResponse(BaseModel):
    """Schema de respuesta para evaluador"""
    evaluador_id: int
    dni: str
    codigo_evaluador: str
    nombre: str
    apellidos: str
    telefono: str
    email: Optional[str] = None
    direccion_trabajo: Optional[str] = None
    distrito_asignado: Optional[str] = None
    provincia_asignada: Optional[str] = None
    departamento_asignado: Optional[str] = None
    activo: bool
    verificado: bool
    fecha_registro: datetime
    ultima_conexion: Optional[datetime] = None
    latitud_actual: Optional[float] = None
    longitud_actual: Optional[float] = None
    precision_gps: Optional[float] = None
    ultima_ubicacion: Optional[datetime] = None
    configuraciones: Optional[Dict[str, Any]] = None
    areas_evaluacion: Optional[List[str]] = None
    
    class Config:
        from_attributes = True

class SupervisorResponse(BaseModel):
    """Schema de respuesta para supervisor"""
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
    ultima_conexion: Optional[datetime] = None
    permisos: Optional[Dict[str, bool]] = None
    configuraciones: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class SesionActivaResponse(BaseModel):
    """Schema de respuesta para sesión activa"""
    sesion_id: str
    tipo_usuario: str
    ip_origen: Optional[str] = None
    fecha_inicio: datetime
    fecha_expiracion: datetime
    ultima_actividad: datetime
    activa: bool
    dispositivo_info: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# =============================================
# SCHEMAS DE ESTADÍSTICAS DE USUARIOS
# =============================================

class VendedorStats(BaseModel):
    """Estadísticas de vendedor"""
    vendedor_id: int
    nombre_completo: str
    codigo_vendedor: str
    total_pedidos: int = 0
    total_ventas: float = 0.0
    promedio_calificacion: float = 0.0
    clientes_unicos: int = 0
    pedidos_hoy: int = 0
    ventas_hoy: float = 0.0
    tiempo_promedio_atencion: Optional[float] = None  # minutos
    eficiencia_porcentaje: float = 0.0
    ultima_actividad: Optional[datetime] = None

class EvaluadorStats(BaseModel):
    """Estadísticas de evaluador"""
    evaluador_id: int
    nombre_completo: str
    codigo_evaluador: str
    total_evaluaciones: int = 0
    evaluaciones_completadas: int = 0
    evaluaciones_pendientes: int = 0
    promedio_tiempo_evaluacion: Optional[float] = None  # minutos
    calificacion_promedio_otorgada: float = 0.0
    areas_cubiertas: List[str] = []
    eficiencia_porcentaje: float = 0.0

class SupervisorStats(BaseModel):
    """Estadísticas de supervisor"""
    supervisor_id: int
    nombre_completo: str
    codigo_supervisor: str
    vendedores_supervisados: int = 0
    reportes_generados: int = 0
    alertas_gestionadas: int = 0
    tiempo_respuesta_promedio: Optional[float] = None  # horas
    nivel_actividad: str = "normal"  # bajo, normal, alto

# =============================================
# SCHEMAS PARA UBICACIÓN GPS
# =============================================

class UbicacionUpdate(BaseModel):
    """Actualización de ubicación GPS"""
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    precision: Optional[float] = Field(None, ge=0)
    timestamp: Optional[datetime] = Field(default_factory=get_utc_now)

class UbicacionResponse(BaseModel):
    """Respuesta de ubicación"""
    usuario_id: int
    tipo_usuario: str
    latitud: float
    longitud: float
    precision: Optional[float] = None
    ultima_actualizacion: datetime
    direccion_aproximada: Optional[str] = None

# =============================================
# SCHEMAS PARA CAMBIO DE CONTRASEÑA
# =============================================

class CambioPassword(BaseModel):
    """Cambio de contraseña"""
    password_actual: str = Field(..., min_length=6)
    password_nueva: str = Field(..., min_length=8)
    confirmar_password: str = Field(..., min_length=8)
    
    @field_validator('confirmar_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password_nueva' in info.data and v != info.data['password_nueva']:
            raise ValueError('Las contraseñas no coinciden')
        return v

class ResetPassword(BaseModel):
    """Reset de contraseña"""
    identifier: str = Field(..., description="DNI, código o email")
    tipo_usuario: str = Field(..., description="Tipo de usuario")

# =============================================
# SCHEMAS PARA CONFIGURACIONES DE USUARIO
# =============================================

class ConfiguracionUsuario(BaseModel):
    """Configuración de usuario"""
    notificaciones_push: bool = True
    notificaciones_email: bool = True
    gps_tracking: bool = True
    idioma: str = "es"
    tema_interfaz: str = "light"  # light, dark
    frecuencia_sync: int = 300  # segundos
    configuraciones_avanzadas: Optional[Dict[str, Any]] = None

class ConfiguracionUpdate(BaseModel):
    """Actualización de configuración"""
    clave: str = Field(..., min_length=1, max_length=100)
    valor: Any
    categoria: Optional[str] = None