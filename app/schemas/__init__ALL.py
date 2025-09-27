# app/schemas/__init__.py - COMPLETO
"""
Esquemas Pydantic para la API
"""

from .common_schemas import (
    # Enums
    RolUsuario, TipoUsuario, EstadoPedido, TipoMensaje, CategoriaProducto,
    UnidadMedida, TipoCliente, EstadoEvaluacion, EstadoMensaje, TipoNotificacion,
    # Responses básicas
    BaseResponse, Response, DataResponse, ListResponse, PaginatedResponse, ErrorResponse,
    # Auth
    LoginRequest, LoginResponse, TokenInfo,
    # Filtros
    PaginationParams, DateRangeFilter, LocationFilter, SearchFilter, 
    FiltrosProductos, FiltrosPedidos,
    # Ubicación
    Coordenadas, Direccion,
    # Modelos de API
    Vendedor, Evaluador, Supervisor, Cliente, ProductoPrecio,
    # Creación
    PedidoCreate,
    # Cálculos y precios
    CalculoPrecio, ResultadoPrecio,
    # KDS
    KDSPedido,
    # Calificaciones
    CalificacionUpdate,
    # Dashboard
    DashboardMetricas, RankingVendedor,
    # Mensajes
    Mensaje, ConversacionVozCreate, TranscripcionCreate,
    # Configuración
    ConfiguracionItem,
    # Notificaciones
    NotificacionBase,
    # Archivos
    ArchivoBase,
    # Estadísticas
    EstadisticasBase,
    # Utilidades
    HealthCheck
)

from .user_schemas import (
    # Create schemas
    VendedorCreate, VendedorUpdate, 
    EvaluadorCreate, EvaluadorUpdate,
    SupervisorCreate, SupervisorUpdate,
    # Response schemas
    VendedorResponse, EvaluadorResponse, SupervisorResponse, SesionActivaResponse,
    # Stats schemas
    VendedorStats, EvaluadorStats, SupervisorStats,
    # Ubicación
    UbicacionUpdate, UbicacionResponse,
    # Password
    CambioPassword, ResetPassword,
    # Configuración
    ConfiguracionUsuario, ConfiguracionUpdate
)

from .client_schemas import (
    ClienteCreate, ClienteUpdate, ClienteResponse,
    HistorialClienteCreate, HistorialClienteResponse,
    SegmentacionClienteCreate, SegmentacionClienteResponse
)

from .product_schemas import (
    ProductoCreate, ProductoUpdate, ProductoResponse,
    CategoriaCreate, CategoriaUpdate, CategoriaResponse,
    PrecioCreate, PrecioUpdate, PrecioResponse
)

from .order_schemas import (
    PedidoUpdate, PedidoResponse,  # PedidoCreate ya está en common_schemas
    ItemPedidoCreate, ItemPedidoResponse,
    CalificacionCreate, CalificacionResponse
)

from .message_schemas import (
    MensajeCreate, MensajeUpdate, MensajeResponse,
    AudioTranscripcionCreate, AudioTranscripcionResponse
)

# Exportar todo
__all__ = [
    # Common schemas - Enums
    "RolUsuario", "TipoUsuario", "EstadoPedido", "TipoMensaje", "CategoriaProducto",
    "UnidadMedida", "TipoCliente", "EstadoEvaluacion", "EstadoMensaje", "TipoNotificacion",
    
    # Common schemas - Responses
    "BaseResponse", "Response", "DataResponse", "ListResponse", "PaginatedResponse", "ErrorResponse",
    
    # Common schemas - Auth
    "LoginRequest", "LoginResponse", "TokenInfo",
    
    # Common schemas - Filtros
    "PaginationParams", "DateRangeFilter", "LocationFilter", "SearchFilter", 
    "FiltrosProductos", "FiltrosPedidos",
    
    # Common schemas - Ubicación
    "Coordenadas", "Direccion",
    
    # Common schemas - Modelos de API
    "Vendedor", "Evaluador", "Supervisor", "Cliente", "ProductoPrecio",
    
    # Common schemas - Creación
    "PedidoCreate",
    
    # Common schemas - Cálculos
    "CalculoPrecio", "ResultadoPrecio",
    
    # Common schemas - KDS
    "KDSPedido",
    
    # Common schemas - Calificaciones
    "CalificacionUpdate",
    
    # Common schemas - Dashboard
    "DashboardMetricas", "RankingVendedor",
    
    # Common schemas - Mensajes
    "Mensaje", "ConversacionVozCreate", "TranscripcionCreate",
    
    # Common schemas - Configuración
    "ConfiguracionItem",
    
    # Common schemas - Notificaciones
    "NotificacionBase",
    
    # Common schemas - Archivos
    "ArchivoBase",
    
    # Common schemas - Estadísticas
    "EstadisticasBase",
    
    # Common schemas - Utilidades
    "HealthCheck",
    
    # User schemas - Create/Update
    "VendedorCreate", "VendedorUpdate", 
    "EvaluadorCreate", "EvaluadorUpdate",
    "SupervisorCreate", "SupervisorUpdate",
    
    # User schemas - Responses
    "VendedorResponse", "EvaluadorResponse", "SupervisorResponse", "SesionActivaResponse",
    
    # User schemas - Stats
    "VendedorStats", "EvaluadorStats", "SupervisorStats",
    
    # User schemas - Ubicación
    "UbicacionUpdate", "UbicacionResponse",
    
    # User schemas - Password
    "CambioPassword", "ResetPassword",
    
    # User schemas - Configuración
    "ConfiguracionUsuario", "ConfiguracionUpdate",
    
    # Client schemas
    "ClienteCreate", "ClienteUpdate", "ClienteResponse",
    "HistorialClienteCreate", "HistorialClienteResponse",
    "SegmentacionClienteCreate", "SegmentacionClienteResponse",
    
    # Product schemas
    "ProductoCreate", "ProductoUpdate", "ProductoResponse",
    "CategoriaCreate", "CategoriaUpdate", "CategoriaResponse",
    "PrecioCreate", "PrecioUpdate", "PrecioResponse",
    
    # Order schemas
    "PedidoUpdate", "PedidoResponse",
    "ItemPedidoCreate", "ItemPedidoResponse",
    "CalificacionCreate", "CalificacionResponse",
    
    # Message schemas
    "MensajeCreate", "MensajeUpdate", "MensajeResponse",
    "AudioTranscripcionCreate", "AudioTranscripcionResponse"
]