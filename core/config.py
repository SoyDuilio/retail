# core/config.py
import os
from typing import List, Optional, Union
from typing import Union, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

# =============================================
# CONFIGURACIÓN PRINCIPAL
# =============================================

class Settings(BaseSettings):
    """Configuración principal del sistema de distribución"""
    
    # =============================================
    # INFORMACIÓN DEL PROYECTO
    # =============================================
    PROJECT_NAME: str = "Sistema de Distribución - Ventas de Campo"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Sistema completo para distribución con geolocalización y ventas de campo"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # =============================================
    # BASE DE DATOS
    # =============================================
    DATABASE_URL: str = Field(
        default="postgresql://postgres:duilia@localhost:5432/pedidos?client_encoding=utf8",
        env="DATABASE_URL"
    )

    # Configuraciones de pool de conexiones
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
    DATABASE_POOL_RECYCLE: int = Field(default=1800, env="DATABASE_POOL_RECYCLE")  # 30 minutos
    
    # =============================================
    # SEGURIDAD Y AUTENTICACIÓN
    # =============================================
    SECRET_KEY: str = Field(
        default="tu_clave_secreta_muy_segura_cambiar_en_produccion_2024",
        env="SECRET_KEY"
    )
    
    # JWT Configuration
    ACCESS_TOKEN_EXPIRE_HOURS: int = Field(default=8, env="ACCESS_TOKEN_EXPIRE_HOURS")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, env="REFRESH_TOKEN_EXPIRE_DAYS")
    JWT_ALGORITHM: str = "HS256"
    
    # Configuraciones de password
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False
    
    # =============================================
    # CORS Y SEGURIDAD WEB
    # =============================================
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080", "https://localhost:3000"],
        env="BACKEND_CORS_ORIGINS"
    )
    
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    
    @field_validator("BACKEND_CORS_ORIGINS", mode='before')
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # =============================================
    # WEBSOCKETS
    # =============================================
    WEBSOCKET_PING_INTERVAL: int = Field(default=30, env="WEBSOCKET_PING_INTERVAL")
    WEBSOCKET_PING_TIMEOUT: int = Field(default=10, env="WEBSOCKET_PING_TIMEOUT") 
    WEBSOCKET_MAX_CONNECTIONS: int = Field(default=1000, env="WEBSOCKET_MAX_CONNECTIONS")
    
    # =============================================
    # GEOLOCALIZACIÓN
    # =============================================
    GPS_PRECISION_METERS: int = Field(default=100, env="GPS_PRECISION_METERS")
    GPS_UPDATE_INTERVAL_SECONDS: int = Field(default=60, env="GPS_UPDATE_INTERVAL_SECONDS")
    GPS_TRACKING_ENABLED: bool = Field(default=True, env="GPS_TRACKING_ENABLED")
    
    # Radio de búsqueda por defecto (km)
    DEFAULT_SEARCH_RADIUS_KM: float = Field(default=5.0, env="DEFAULT_SEARCH_RADIUS_KM")
    
    # =============================================
    # ARCHIVOS Y MULTIMEDIA
    # =============================================
    UPLOAD_DIRECTORY: str = Field(default="uploads", env="UPLOAD_DIRECTORY")
    MAX_FILE_SIZE_MB: int = Field(default=10, env="MAX_FILE_SIZE_MB")
    ALLOWED_FILE_EXTENSIONS: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".pdf", ".mp3", ".wav", ".m4a"],
        env="ALLOWED_FILE_EXTENSIONS"
    )
    
    # Configuración de imágenes
    IMAGE_QUALITY: int = Field(default=85, env="IMAGE_QUALITY")
    THUMBNAIL_SIZE: tuple = (150, 150)
    
    # =============================================
    # NOTIFICACIONES PUSH
    # =============================================
    FCM_SERVER_KEY: Optional[str] = Field(default=None, env="FCM_SERVER_KEY")
    FCM_ENABLED: bool = Field(default=False, env="FCM_ENABLED")
    
    # =============================================
    # REDIS (CACHE Y SESIONES)
    # =============================================
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    REDIS_ENABLED: bool = Field(default=False, env="REDIS_ENABLED")
    CACHE_TTL_SECONDS: int = Field(default=300, env="CACHE_TTL_SECONDS")  # 5 minutos
    
    # =============================================
    # EMAIL (OPCIONAL)
    # =============================================
    SMTP_SERVER: Optional[str] = Field(default=None, env="SMTP_SERVER")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(default=True, env="SMTP_USE_TLS")
    
    EMAIL_FROM: Optional[str] = Field(default=None, env="EMAIL_FROM")
    EMAIL_ENABLED: bool = Field(default=False, env="EMAIL_ENABLED")
    
    # =============================================
    # LOGGING
    # =============================================
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # =============================================
    # API Y LÍMITES
    # =============================================
    API_V1_STR: str = "/api/v1"
    API_RATE_LIMIT: str = Field(default="100/minute", env="API_RATE_LIMIT")
    
    # Paginación por defecto
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # =============================================
    # CONFIGURACIONES DE NEGOCIO
    # =============================================
    
    # Configuraciones de pedidos
    PEDIDO_TIMEOUT_HOURS: int = Field(default=24, env="PEDIDO_TIMEOUT_HOURS")
    PEDIDO_MIN_AMOUNT: float = Field(default=10.0, env="PEDIDO_MIN_AMOUNT")
    PEDIDO_MAX_AMOUNT: float = Field(default=5000.0, env="PEDIDO_MAX_AMOUNT")
    
    # Configuraciones de vendedores
    VENDEDOR_MAX_CLIENTS_PER_DAY: int = Field(default=20, env="VENDEDOR_MAX_CLIENTS_PER_DAY")
    VENDEDOR_WORKING_HOURS_START: int = Field(default=8, env="VENDEDOR_WORKING_HOURS_START")
    VENDEDOR_WORKING_HOURS_END: int = Field(default=18, env="VENDEDOR_WORKING_HOURS_END")
    
    # Configuraciones de evaluadores
    EVALUADOR_MAX_EVALUATIONS_PER_DAY: int = Field(default=15, env="EVALUADOR_MAX_EVALUATIONS_PER_DAY")
    EVALUACION_TIMEOUT_MINUTES: int = Field(default=30, env="EVALUACION_TIMEOUT_MINUTES")
    
    # =============================================
    # CONFIGURACIONES DE DESARROLLO
    # =============================================
    TESTING: bool = Field(default=False, env="TESTING")
    
    # Base de datos de pruebas
    TEST_DATABASE_URL: Optional[str] = Field(default=None, env="TEST_DATABASE_URL")
    
    # Datos de prueba
    CREATE_SAMPLE_DATA: bool = Field(default=False, env="CREATE_SAMPLE_DATA")
    SAMPLE_USERS_COUNT: int = Field(default=10, env="SAMPLE_USERS_COUNT")
    
    # =============================================
    # CONFIGURACIONES DE PRODUCCIÓN
    # =============================================
    
    # SSL/HTTPS
    USE_HTTPS: bool = Field(default=False, env="USE_HTTPS")
    SSL_CERT_PATH: Optional[str] = Field(default=None, env="SSL_CERT_PATH")
    SSL_KEY_PATH: Optional[str] = Field(default=None, env="SSL_KEY_PATH")
    
    # Configuraciones del servidor
    SERVER_HOST: str = Field(default="0.0.0.0", env="SERVER_HOST")
    SERVER_PORT: int = Field(default=8000, env="SERVER_PORT")
    SERVER_WORKERS: int = Field(default=1, env="SERVER_WORKERS")
    
    # Monitoreo
    ENABLE_METRICS: bool = Field(default=False, env="ENABLE_METRICS")
    METRICS_PATH: str = Field(default="/metrics", env="METRICS_PATH")
    
    # =============================================
    # VALIDACIONES PERSONALIZADAS
    # =============================================
    
    @field_validator("SECRET_KEY", mode='before')
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY debe tener al menos 32 caracteres")
        return v
    
    @field_validator("DATABASE_URL", mode='before')
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError("DATABASE_URL debe ser una URL de PostgreSQL válida")
        return v
    
    @field_validator("LOG_LEVEL", mode='before')
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL debe ser uno de: {', '.join(valid_levels)}")
        return v.upper()
    
    # =============================================
    # PROPIEDADES CALCULADAS
    # =============================================
    
    @property
    def database_url_sync(self) -> str:
        """URL síncrona de la base de datos"""
        return self.DATABASE_URL.replace("+asyncpg", "").replace("+psycopg2", "")
    
    @property
    def max_file_size_bytes(self) -> int:
        """Tamaño máximo de archivo en bytes"""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    @property
    def is_development(self) -> bool:
        """Verifica si está en modo desarrollo"""
        return self.DEBUG or self.TESTING
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Lista de orígenes CORS permitidos"""
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        return self.BACKEND_CORS_ORIGINS
    
    # =============================================
    # CONFIGURACIÓN DE CLASE
    # =============================================
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

# =============================================
# INSTANCIA GLOBAL DE CONFIGURACIÓN
# =============================================

settings = Settings()

# =============================================
# CONFIGURACIONES ESPECÍFICAS POR AMBIENTE
# =============================================

def get_settings() -> Settings:
    """Obtiene la configuración actual"""
    return settings

def is_testing() -> bool:
    """Verifica si está en modo testing"""
    return settings.TESTING

def is_development() -> bool:
    """Verifica si está en modo desarrollo"""
    return settings.DEBUG

def is_production() -> bool:
    """Verifica si está en modo producción"""
    return not (settings.DEBUG or settings.TESTING)

# =============================================
# CONFIGURACIONES ESPECÍFICAS DE LOGGING
# =============================================

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": settings.LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": settings.LOG_LEVEL,
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["console"],
            "level": settings.LOG_LEVEL,
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "sqlalchemy": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# Agregar handler de archivo si está configurado
if settings.LOG_FILE:
    LOGGING_CONFIG["handlers"]["file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": settings.LOG_FILE,
        "formatter": "detailed",
        "level": settings.LOG_LEVEL,
        "maxBytes": 10485760,  # 10MB
        "backupCount": 5,
    }
    
    # Agregar el handler de archivo a todos los loggers
    for logger_config in LOGGING_CONFIG["loggers"].values():
        if "file" not in logger_config["handlers"]:
            logger_config["handlers"].append("file")

# =============================================
# FUNCIONES DE UTILIDAD PARA CONFIGURACIÓN
# =============================================

def get_database_url(async_driver: bool = False) -> str:
    """Obtiene la URL de base de datos apropiada"""
    if async_driver:
        return settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    else:
        return settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")

def get_cors_origins() -> List[str]:
    """Obtiene la lista de orígenes CORS"""
    return settings.cors_origins_list

def validate_environment() -> Dict[str, bool]:
    """Valida la configuración del entorno"""
    validations = {
        "database_accessible": False,
        "secret_key_secure": len(settings.SECRET_KEY) >= 32,
        "cors_configured": len(settings.BACKEND_CORS_ORIGINS) > 0,
        "logging_configured": True,
        "uploads_directory_exists": False,
    }
    
    # Verificar que el directorio de uploads existe o se puede crear
    try:
        import os
        if not os.path.exists(settings.UPLOAD_DIRECTORY):
            os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
        validations["uploads_directory_exists"] = True
    except Exception:
        pass
    
    # Verificar conexión a base de datos (solo en desarrollo)
    if settings.DEBUG:
        try:
            import psycopg2
            conn = psycopg2.connect(settings.database_url_sync)
            conn.close()
            validations["database_accessible"] = True
        except Exception:
            pass
    
    return validations

def get_app_info() -> Dict[str, Any]:
    """Obtiene información de la aplicación"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "environment": "development" if settings.DEBUG else "testing" if settings.TESTING else "production",
        "api_version": settings.API_V1_STR,
        "debug": settings.DEBUG,
        "testing": settings.TESTING,
    }