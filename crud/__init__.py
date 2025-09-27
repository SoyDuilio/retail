# app/crud/__init__.py
"""
Operaciones CRUD
"""

from .base import CRUDBase
from .crud_user import (
    CRUDVendedor, CRUDEvaluador, CRUDSupervisor, CRUDSesionActiva,
    crud_vendedor, crud_evaluador, crud_supervisor, crud_sesion_activa,
    get_user_by_identifier, count_active_users_by_type
)
from .crud_client import (
    CRUDCliente, CRUDHistorialCliente, CRUDSegmentacionCliente,
    crud_cliente, crud_historial_cliente, crud_segmentacion_cliente
)

__all__ = [
    # Base CRUD
    "CRUDBase",
    # User CRUD classes
    "CRUDVendedor", "CRUDEvaluador", "CRUDSupervisor", "CRUDSesionActiva",
    # User CRUD instances
    "crud_vendedor", "crud_evaluador", "crud_supervisor", "crud_sesion_activa",
    # Client CRUD classes
    "CRUDCliente", "CRUDHistorialCliente", "CRUDSegmentacionCliente",
    # Client CRUD instances  
    "crud_cliente", "crud_historial_cliente", "crud_segmentacion_cliente",
    # Utility functions
    "get_user_by_identifier", "count_active_users_by_type"
]