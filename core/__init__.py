# app/core/__init__.py
"""
Módulo core - Configuración y autenticación
"""

from .config import settings
from .auth import (
    hash_password, 
    verify_password, 
    create_access_token, 
    decode_access_token,
    get_current_user,
    get_current_vendedor,
    get_current_evaluador,
    get_current_supervisor
)

__all__ = [
    "settings",
    "hash_password",
    "verify_password", 
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "get_current_vendedor",
    "get_current_evaluador",
    "get_current_supervisor"
]