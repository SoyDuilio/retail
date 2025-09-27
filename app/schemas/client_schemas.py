# app/schemas/client_schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from .common_schemas import Coordenadas
from .product_schemas import TipoCliente

# =============================================
# CLIENTES BASE
# =============================================

class ClienteBase(BaseModel):
    ruc: str = Field(..., min_length=11, max_length=11)
    razon_social: Optional[str] = Field(None, max_length=200)
    nombres: Optional[str] = Field(None, max_length=100)
    apellidos: Optional[str] = Field(None, max_length=100)
    direccion: str = Field(..., min_length=10)
    latitud: Optional[Decimal] = Field(None, ge=-90, le=90, decimal_places=8)
    longitud: Optional[Decimal] = Field(None, ge=-180, le=180, decimal_places=8)
    tipo_cliente_id: int
    contacto_nombres: Optional[str] = Field(None, max_length=100)
    whatsapp: Optional[str] = Field(None, max_length=15)
    limite_credito: Decimal = Field(default=0, ge=0, decimal_places=2)
    credito_usado: Decimal = Field(default=0, ge=0, decimal_places=2)
    activo: bool = True

    @validator('ruc')
    def validate_ruc(cls, v):
        if not v.isdigit():
            raise ValueError('RUC debe contener solo números')
        if len(v) != 11:
            raise ValueError('RUC debe tener exactamente 11 dígitos')
        return v

    @validator('whatsapp')
    def validate_whatsapp(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('WhatsApp debe contener solo números')
        return v

    @validator('limite_credito')
    def validate_limite_credito(cls, v):
        if v < 0:
            raise ValueError('Límite de crédito no puede ser negativo')
        return v

class ClienteCreate(ClienteBase):
    @validator('nombres', 'apellidos', 'razon_social', pre=True, always=True)
    def validate_nombre_o_razon_social(cls, v, values):
        # Al menos uno de: (nombres + apellidos) o razon_social debe estar presente
        if 'razon_social' in values:
            if not values.get('razon_social') and not (values.get('nombres') and values.get('apellidos')):
                raise ValueError('Debe proporcionar razón social o nombres y apellidos')
        return v

class ClienteUpdate(BaseModel):
    razon_social: Optional[str] = Field(None, max_length=200)
    nombres: Optional[str] = Field(None, max_length=100)
    apellidos: Optional[str] = Field(None, max_length=100)
    direccion: Optional[str] = Field(None, min_length=10)
    latitud: Optional[Decimal] = Field(None, ge=-90, le=90, decimal_places=8)
    longitud: Optional[Decimal] = Field(None, ge=-180, le=180, decimal_places=8)
    tipo_cliente_id: Optional[int] = None
    contacto_nombres: Optional[str] = Field(None, max_length=100)
    whatsapp: Optional[str] = Field(None, max_length=15)
    limite_credito: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    activo: Optional[bool] = None

class Cliente(ClienteBase):
    id: int
    created_at: datetime
    updated_at: datetime
    tipo_cliente: Optional[TipoCliente] = None
    credito_disponible: Optional[Decimal] = None

    class Config:
        from_attributes = True

# =============================================
# INFORMACIÓN CREDITICIA
# =============================================

class ValidacionCredito(BaseModel):
    cliente_id: int
    monto_solicitado: Decimal = Field(..., gt=0, decimal_places=2)

class ResultadoCredito(BaseModel):
    cliente_id: int
    cliente_nombre: str
    limite_credito: Decimal
    credito_usado: Decimal
    credito_disponible: Decimal
    monto_solicitado: Decimal
    puede_aprobar: bool
    monto_maximo_aprobable: Decimal
    porcentaje_utilizacion: Decimal
    observaciones: Optional[str] = None
    historial_pagos: Optional[str] = None  # bueno, regular, malo

class ActualizarCredito(BaseModel):
    cliente_id: int
    nuevo_limite: Decimal = Field(..., ge=0, decimal_places=2)
    motivo: str = Field(..., min_length=10)
    aprobado_por: int  # ID del supervisor que aprueba

class HistorialCredito(BaseModel):
    id: int
    cliente_id: int
    tipo_movimiento: str  # aumento_limite, disminucion_limite, uso_credito, pago
    monto: Decimal
    limite_anterior: Decimal
    limite_nuevo: Decimal
    motivo: str
    aprobado_por: Optional[int] = None
    created_at: datetime

# =============================================
# UBICACIÓN Y GEOLOCALIZACIÓN
# =============================================

class ClienteUbicacion(BaseModel):
    cliente_id: int
    cliente_nombre: str
    direccion: str
    coordenadas: Optional[Coordenadas] = None
    tipo_cliente: str
    activo: bool
    distancia_km: Optional[float] = None  # Calculada desde punto de referencia

class ClientesCercanos(BaseModel):
    ubicacion_referencia: Coordenadas
    radio_km: float = Field(default=5.0, ge=0.1, le=50)
    tipo_cliente_id: Optional[int] = None
    solo_activos: bool = True

class ResultadoClientesCercanos(BaseModel):
    total_encontrados: int
    radio_busqueda: float
    clientes: List[ClienteUbicacion]
    centro_busqueda: Coordenadas

class ActualizarUbicacion(BaseModel):
    cliente_id: int
    nueva_direccion: Optional[str] = None
    nuevas_coordenadas: Optional[Coordenadas] = None
    verificado: bool = False

# =============================================
# PERFILES Y SEGMENTACIÓN
# =============================================

class PerfilCliente(BaseModel):
    cliente: Cliente
    estadisticas_compras: dict
    promedio_pedido: Decimal
    frecuencia_compra: str  # diario, semanal, quincenal, mensual
    productos_favoritos: List[str]
    canal_preferido: str  # vendedor_externo, vendedor_interno, portal_web
    score_crediticio: int = Field(ge=0, le=100)
    ultima_compra: Optional[datetime] = None

class SegmentoCliente(BaseModel):
    id: int
    nombre: str
    descripcion: str
    criterios: dict  # JSON con criterios de segmentación
    color: str = Field(default="#3B82F6")
    clientes_count: int = 0

class AsignarSegmento(BaseModel):
    cliente_id: int
    segmento_id: int
    asignado_por: int
    motivo: Optional[str] = None

# =============================================
# COMUNICACIÓN Y CONTACTO
# =============================================

class ContactoCliente(BaseModel):
    cliente_id: int
    tipo_contacto: str  # llamada, whatsapp, visita, email
    asunto: str
    mensaje: str
    realizado_por: int
    realizado_por_tipo: str  # vendedor, evaluador, supervisor
    respuesta_cliente: Optional[str] = None
    resultado: str  # exitoso, sin_respuesta, ocupado, rechazado
    created_at: datetime

class ProgramarContacto(BaseModel):
    cliente_id: int
    tipo_contacto: str
    fecha_programada: datetime
    asunto: str
    notas: Optional[str] = None
    asignado_a: int
    prioridad: str = Field(default="media")  # alta, media, baja

class HistorialContactos(BaseModel):
    cliente_id: int
    contactos: List[ContactoCliente]
    ultimo_contacto: Optional[datetime] = None
    proximos_contactos: List[ProgramarContacto]

# =============================================
# FILTROS Y BÚSQUEDAS
# =============================================

class FiltrosClientes(BaseModel):
    tipo_cliente_id: Optional[int] = None
    activo: Optional[bool] = None
    con_credito: Optional[bool] = None
    buscar: Optional[str] = Field(None, min_length=2)
    ruc: Optional[str] = Field(None, min_length=11, max_length=11)
    distrito: Optional[str] = None
    limite_credito_min: Optional[Decimal] = Field(None, ge=0)
    limite_credito_max: Optional[Decimal] = Field(None, ge=0)
    ultima_compra_desde: Optional[datetime] = None
    ultima_compra_hasta: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

class ClienteResumen(BaseModel):
    id: int
    ruc: str
    nombre_completo: str
    tipo_cliente: str
    direccion: str
    credito_disponible: Decimal
    ultima_compra: Optional[datetime] = None
    estado_credito: str  # excelente, bueno, regular, malo
    activo: bool

# =============================================
# REPORTES DE CLIENTES
# =============================================

class ReporteCliente(BaseModel):
    cliente_id: int
    ruc: str
    nombre_completo: str
    tipo_cliente: str
    total_compras: Decimal
    cantidad_pedidos: int
    promedio_pedido: Decimal
    dias_desde_ultima_compra: Optional[int] = None
    score_fidelidad: int

class ReporteTipoCliente(BaseModel):
    tipo_cliente_id: int
    tipo_nombre: str
    cantidad_clientes: int
    clientes_activos: int
    total_ventas: Decimal
    promedio_credito: Decimal
    utilizacion_credito_promedio: Decimal

class ReporteClientesMes(BaseModel):
    mes_ano: str
    clientes_nuevos: int
    clientes_activos: int
    clientes_inactivos: int
    ventas_totales: Decimal
    credito_otorgado: Decimal
    credito_utilizado: Decimal
    tipos_cliente: List[ReporteTipoCliente]

# =============================================
# INTEGRACIÓN Y SINCRONIZACIÓN
# =============================================

class ClienteVFP(BaseModel):
    """Schema para sincronización con Visual FoxPro"""
    codigo_vfp: str
    ruc: str
    nombre: str
    direccion: str
    telefono: Optional[str] = None
    limite_credito: Decimal
    saldo_pendiente: Decimal
    ultima_actualizacion: datetime

class SincronizacionCliente(BaseModel):
    cliente_id: int
    sincronizado_vfp: bool = False
    fecha_ultima_sync: Optional[datetime] = None
    errores_sync: Optional[List[str]] = None

class ResultadoSincronizacion(BaseModel):
    total_clientes: int
    sincronizados_exitosos: int
    con_errores: int
    clientes_nuevos: int
    clientes_actualizados: int
    errores: List[str]