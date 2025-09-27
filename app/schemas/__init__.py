# app/schemas/__init__.py - VERSION MINIMAL
"""
Esquemas Pydantic para la API - Solo imports seguros
"""

# Solo importar de common_schemas que sabemos que existe
from .common_schemas import (
    # Enums
    RolUsuario, TipoUsuario, EstadoPedido, TipoMensaje, CategoriaProducto,
    UnidadMedida, TipoCliente, EstadoEvaluacion, EstadoMensaje, TipoNotificacion,
    EstadoStock,
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

# Solo importar user_schemas básicos
try:
    from .user_schemas import (
        VendedorCreate, VendedorUpdate,
        EvaluadorCreate, EvaluadorUpdate, 
        SupervisorCreate, SupervisorUpdate
    )
except ImportError:
    # Si no existen, crear placeholders vacíos
    pass

# Comentar imports problemáticos por ahora
# from .client_schemas import (
#     ClienteCreate, ClienteUpdate, ClienteResponse,
#     HistorialClienteCreate, HistorialClienteResponse,
#     SegmentacionClienteCreate, SegmentacionClienteResponse
# )

# from .product_schemas import (
#     ProductoCreate, ProductoUpdate, ProductoResponse,
#     CategoriaCreate, CategoriaUpdate, CategoriaResponse,
#     PrecioCreate, PrecioUpdate, PrecioResponse
# )

# from .order_schemas import (
#     PedidoUpdate, PedidoResponse,
#     ItemPedidoCreate, ItemPedidoResponse,
#     CalificacionCreate, CalificacionResponse
# )

# from .message_schemas import (
#     MensajeCreate, MensajeUpdate, MensajeResponse,
#     AudioTranscripcionCreate, AudioTranscripcionResponse
# )

# Exportar solo lo que funciona
__all__ = [
    # Common schemas - Enums
    "RolUsuario", "TipoUsuario", "EstadoPedido", "TipoMensaje", "CategoriaProducto",
    "UnidadMedida", "TipoCliente", "EstadoEvaluacion", "EstadoMensaje", "TipoNotificacion",
    "EstadoStock",
    
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
    
    # User schemas básicos (si existen)
    "VendedorCreate", "VendedorUpdate", 
    "EvaluadorCreate", "EvaluadorUpdate",
    "SupervisorCreate", "SupervisorUpdate"
]