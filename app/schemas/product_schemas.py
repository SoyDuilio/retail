# app/schemas/product_schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from .common_schemas import CategoriaProducto, UnidadMedida, EstadoStock
# =============================================
# TIPOS DE CLIENTE
# =============================================

class TipoClienteBase(BaseModel):
    nombre: str = Field(..., max_length=50)
    descripcion: Optional[str] = None
    activo: bool = True

class TipoClienteCreate(TipoClienteBase):
    pass

class TipoClienteUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=50)
    descripcion: Optional[str] = None
    activo: Optional[bool] = None

class TipoCliente(TipoClienteBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# =============================================
# CATEGORÍAS DE PRODUCTOS
# =============================================

class CategoriaBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    activo: bool = True

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    activo: Optional[bool] = None

class Categoria(CategoriaBase):
    id: int
    created_at: datetime
    total_productos: Optional[int] = None

    class Config:
        from_attributes = True

# =============================================
# UNIDADES DE MEDIDA
# =============================================

class UnidadMedidaBase(BaseModel):
    nombre: str = Field(..., max_length=20)
    abreviatura: str = Field(..., max_length=5)
    activo: bool = True

class UnidadMedidaCreate(UnidadMedidaBase):
    pass

class UnidadMedidaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=20)
    abreviatura: Optional[str] = Field(None, max_length=5)
    activo: Optional[bool] = None

class UnidadMedida(UnidadMedidaBase):
    id: int

    class Config:
        from_attributes = True

# =============================================
# PRODUCTOS
# =============================================

class ProductoBase(BaseModel):
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    categoria_id: int
    unidad_medida_id: int
    precio_base: Decimal = Field(..., ge=0, decimal_places=2)
    stock_actual: int = Field(default=0, ge=0)
    stock_minimo: int = Field(default=0, ge=0)
    activo: bool = True

    @validator('codigo')
    def validate_codigo(cls, v):
        if not v.strip():
            raise ValueError('Código no puede estar vacío')
        return v.upper().strip()

    @validator('precio_base')
    def validate_precio(cls, v):
        if v < 0:
            raise ValueError('Precio no puede ser negativo')
        return v

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(BaseModel):
    codigo: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    categoria_id: Optional[int] = None
    unidad_medida_id: Optional[int] = None
    precio_base: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    stock_actual: Optional[int] = Field(None, ge=0)
    stock_minimo: Optional[int] = Field(None, ge=0)
    activo: Optional[bool] = None

class Producto(ProductoBase):
    id: int
    created_at: datetime
    updated_at: datetime
    categoria: Optional[Categoria] = None
    unidad_medida: Optional[UnidadMedida] = None
    estado_stock: Optional[EstadoStock] = None

    class Config:
        from_attributes = True

class ProductoList(BaseModel):
    id: int
    codigo: str
    nombre: str
    categoria: str
    precio_base: Decimal
    stock_actual: int
    estado_stock: EstadoStock
    activo: bool

# =============================================
# PRECIOS POR TIPO DE CLIENTE
# =============================================

class PrecioClienteBase(BaseModel):
    producto_id: int
    tipo_cliente_id: int
    precio: Decimal = Field(..., ge=0, decimal_places=2)
    descuento_volumen_1: Optional[Decimal] = Field(default=0, ge=0, le=100, decimal_places=2)
    cantidad_minima_1: Optional[int] = Field(default=10, ge=1)
    descuento_volumen_2: Optional[Decimal] = Field(default=0, ge=0, le=100, decimal_places=2)
    cantidad_minima_2: Optional[int] = Field(default=50, ge=1)
    descuento_volumen_3: Optional[Decimal] = Field(default=0, ge=0, le=100, decimal_places=2)
    cantidad_minima_3: Optional[int] = Field(default=100, ge=1)
    activo: bool = True

    @validator('precio')
    def validate_precio(cls, v):
        if v <= 0:
            raise ValueError('Precio debe ser mayor que cero')
        return v

class PrecioClienteCreate(PrecioClienteBase):
    pass

class PrecioClienteUpdate(BaseModel):
    precio: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    descuento_volumen_1: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    cantidad_minima_1: Optional[int] = Field(None, ge=1)
    descuento_volumen_2: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    cantidad_minima_2: Optional[int] = Field(None, ge=1)
    descuento_volumen_3: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    cantidad_minima_3: Optional[int] = Field(None, ge=1)
    activo: Optional[bool] = None

class PrecioCliente(PrecioClienteBase):
    id: int
    created_at: datetime
    producto: Optional[Producto] = None
    tipo_cliente: Optional[TipoCliente] = None

    class Config:
        from_attributes = True

# =============================================
# PRODUCTOS CON PRECIOS (VISTA COMPLETA)
# =============================================

class ProductoPrecio(BaseModel):
    producto_id: int
    codigo: str
    producto_nombre: str
    descripcion: Optional[str]
    categoria: str
    unidad_medida: str
    unidad_abrev: str
    tipo_cliente_id: int
    tipo_cliente: str
    precio: Decimal
    descuento_volumen_1: Optional[Decimal]
    cantidad_minima_1: Optional[int]
    descuento_volumen_2: Optional[Decimal]
    cantidad_minima_2: Optional[int]
    descuento_volumen_3: Optional[Decimal]
    cantidad_minima_3: Optional[int]
    stock_actual: int
    stock_minimo: int
    estado_stock: EstadoStock

    class Config:
        from_attributes = True

# =============================================
# CÁLCULOS DE PRECIOS
# =============================================

class CalculoPrecio(BaseModel):
    producto_id: int
    tipo_cliente_id: int
    cantidad: int = Field(..., gt=0)

    @validator('cantidad')
    def validate_cantidad(cls, v):
        if v <= 0:
            raise ValueError('Cantidad debe ser mayor que cero')
        return v

class ResultadoPrecio(BaseModel):
    producto_id: int
    producto_nombre: str
    cantidad: int
    precio_unitario: Decimal
    descuento_aplicado: Decimal
    precio_final_unitario: Decimal
    subtotal: Decimal
    descuento_total: Decimal
    total: Decimal
    descuento_por_volumen: bool
    nivel_descuento: Optional[int] = None
    ahorro: Decimal = Field(default=0)

class CalculoMultiplePrecios(BaseModel):
    items: List[CalculoPrecio]
    tipo_cliente_id: int

class ResultadoMultiplePrecio(BaseModel):
    items: List[ResultadoPrecio]
    subtotal_general: Decimal
    descuento_general: Decimal
    total_general: Decimal
    ahorro_total: Decimal

# =============================================
# CATÁLOGO Y BÚSQUEDAS
# =============================================

class FiltrosProductos(BaseModel):
    categoria_id: Optional[int] = None
    tipo_cliente_id: Optional[int] = None
    buscar: Optional[str] = Field(None, min_length=2)
    stock_bajo: Optional[bool] = None
    precio_min: Optional[Decimal] = Field(None, ge=0)
    precio_max: Optional[Decimal] = Field(None, ge=0)
    activo: Optional[bool] = True
    codigo: Optional[str] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=50, ge=1, le=200)

class CatalogoProducto(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: Optional[str]
    categoria: str
    unidad_medida: str
    precio: Decimal  # Precio para el tipo de cliente específico
    stock_disponible: bool
    imagen_url: Optional[str] = None

class ProductoDetalle(BaseModel):
    producto: Producto
    precios_por_tipo: List[PrecioCliente]
    stock_info: dict
    historial_ventas: Optional[dict] = None

# =============================================
# INVENTARIO Y STOCK
# =============================================

class MovimientoStock(BaseModel):
    producto_id: int
    tipo_movimiento: str  # entrada, salida, ajuste
    cantidad: int
    stock_anterior: int
    stock_nuevo: int
    motivo: str
    usuario_id: int
    usuario_tipo: str
    created_at: datetime

class AlertaStock(BaseModel):
    producto_id: int
    codigo: str
    nombre: str
    stock_actual: int
    stock_minimo: int
    categoria: str
    dias_sin_stock_estimados: Optional[int] = None
    prioridad: str  # alta, media, baja

class ActualizarStock(BaseModel):
    producto_id: int
    nueva_cantidad: int = Field(..., ge=0)
    motivo: str = Field(..., min_length=5)

class AjusteStockMasivo(BaseModel):
    ajustes: List[ActualizarStock]
    motivo_general: str

# =============================================
# REPORTES DE PRODUCTOS
# =============================================

class ReporteProducto(BaseModel):
    producto_id: int
    codigo: str
    nombre: str
    categoria: str
    total_vendido: int
    monto_vendido: Decimal
    stock_actual: int
    rotacion: Decimal  # veces que rota por período
    margen_promedio: Decimal

class ReporteCategoria(BaseModel):
    categoria_id: int
    categoria_nombre: str
    total_productos: int
    productos_activos: int
    total_ventas: Decimal
    productos_stock_bajo: int

class ReporteInventario(BaseModel):
    total_productos: int
    productos_activos: int
    productos_stock_bajo: int
    productos_sin_stock: int
    valor_inventario: Decimal
    productos_mas_vendidos: List[ReporteProducto]
    categorias_resumen: List[ReporteCategoria]
    fecha_reporte: datetime

# =============================================
# IMPORTACIÓN Y EXPORTACIÓN
# =============================================

class ImportarProducto(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    categoria_nombre: str
    unidad_medida_nombre: str
    precio_base: Decimal
    stock_inicial: int = Field(default=0)
    stock_minimo: int = Field(default=0)

class ResultadoImportacion(BaseModel):
    total_procesados: int
    productos_creados: int
    productos_actualizados: int
    errores: List[str]
    productos_con_error: List[str]

class ExportarProductos(BaseModel):
    formato: str = Field(default="excel")  # excel, csv, json
    categoria_ids: Optional[List[int]] = None
    incluir_precios: bool = True
    incluir_stock: bool = True
    solo_activos: bool = True

# =============================================
# CONFIGURACIÓN DE PRECIOS
# =============================================

class ConfiguracionPrecio(BaseModel):
    tipo_cliente_id: int
    margen_base: Decimal = Field(..., ge=0, le=100)  # Porcentaje sobre precio base
    descuento_volumen_habilitado: bool = True
    descuento_maximo: Decimal = Field(default=15, ge=0, le=50)

class AplicarCambioPrecios(BaseModel):
    tipo_cambio: str  # porcentaje, valor_fijo, margen
    valor_cambio: Decimal
    categoria_ids: Optional[List[int]] = None
    producto_ids: Optional[List[int]] = None
    tipo_cliente_ids: Optional[List[int]] = None
    motivo: str = Field(..., min_length=5)
    usuario_id: int   