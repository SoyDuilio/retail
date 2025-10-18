# app/schemas/client_schemas.py
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from .common_schemas import Coordenadas
from .product_schemas import TipoCliente

# ============================================================================
# SCHEMAS PARA CLIENTES
# ============================================================================

class ClienteBase(BaseModel):
    nombre_comercial: str
    razon_social: str
    ruc: str
    telefono: str
    email: Optional[EmailStr] = None
    direccion_completa: str
    referencia: Optional[str] = None
    distrito: str
    provincia: str
    departamento: str
    codigo_postal: Optional[str] = None
    tipo_cliente_id: int
    
    @field_validator('ruc')
    @classmethod
    def validar_ruc(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError('RUC debe contener solo números')
        if len(v) != 11:
            raise ValueError('RUC debe tener 11 dígitos')
        return v
    
    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError('Teléfono debe contener solo números')
        if len(v) < 7 or len(v) > 15:
            raise ValueError('Teléfono debe tener entre 7 y 15 dígitos')
        return v


class ClienteCreate(ClienteBase):
    """Schema para crear un nuevo cliente desde el formulario web"""
    # Campos adicionales del titular (se guardarán en contactos)
    dni_titular: Optional[str] = None
    nombres_titular: Optional[str] = None
    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    precision_gps: Optional[Decimal] = None
    
    @field_validator('dni_titular')
    @classmethod
    def validar_dni(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            if not v.isdigit():
                raise ValueError('DNI debe contener solo números')
            if len(v) != 8:
                raise ValueError('DNI debe tener 8 dígitos')
        return v


class ClienteUpdate(BaseModel):
    """Schema para actualizar cliente"""
    nombre_comercial: Optional[str] = None
    razon_social: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    direccion_completa: Optional[str] = None
    referencia: Optional[str] = None
    distrito: Optional[str] = None
    provincia: Optional[str] = None
    departamento: Optional[str] = None
    codigo_postal: Optional[str] = None
    tipo_cliente_id: Optional[int] = None
    activo: Optional[bool] = None
    verificado: Optional[bool] = None
    
    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            if not v.isdigit():
                raise ValueError('Teléfono debe contener solo números')
            if len(v) < 7 or len(v) > 15:
                raise ValueError('Teléfono debe tener entre 7 y 15 dígitos')
        return v


class ClienteResponse(ClienteBase):
    """Schema para respuesta de cliente"""
    id: int
    codigo_cliente: str
    activo: bool
    verificado: bool
    fecha_registro: datetime
    es_moroso: bool
    deuda_actual: Decimal
    dias_mora: int
    
    model_config = {
        "from_attributes": True
    }


class ClienteListResponse(BaseModel):
    """Schema para lista de clientes (simplificado)"""
    id: int
    codigo_cliente: str
    nombre_comercial: str
    razon_social: str
    ruc: str
    telefono: str
    distrito: str
    provincia: str
    activo: bool
    verificado: bool
    es_moroso: bool
    deuda_actual: Decimal
    
    model_config = {
        "from_attributes": True
    }


class ClienteSelectResponse(BaseModel):
    """Schema simple para select/dropdown"""
    id: int
    codigo_cliente: str
    nombre_comercial: str
    ruc: str
    
    model_config = {
        "from_attributes": True
    }

# =============================================
# SOBRAN???? 👇
# =============================================

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