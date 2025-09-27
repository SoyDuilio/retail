from .user_models import VendedorModel, EvaluadorModel, SupervisorModel, SesionActivaModel
from .client_models import ClienteModel, HistorialCreditoModel, SegmentoClienteModel, ContactoClienteModel, TipoClienteModel
from .product_models import ProductoModel, CategoriaModel, UnidadMedidaModel, PrecioClienteModel, MovimientoStockModel
#from .order_models import PedidoModel, PedidoItemModel  # COMENTAR
#from .message_models import MensajeModel, ConversacionVozModel  # COMENTAR


__all__ = [
    # User models
    "VendedorModel", "EvaluadorModel", "SupervisorModel", "SesionActivaModel",
    # Client models
    "ClienteModel", "HistorialCreditoModel", "SegmentoClienteModel", 
    "TipoClienteModel", "ContactoClienteModel", 
    # Product models  
    "ProductoModel", "CategoriaModel", "UnidadMedidaModel", "PrecioClienteModel",
    "MovimientoStockModel",
    # Order models
    "CalificacionModel",
    
]
   # Order models
#"PedidoModel", "PedidoItemModel",

# Message models
    #"MensajeModel", "ConversacionVozModel",