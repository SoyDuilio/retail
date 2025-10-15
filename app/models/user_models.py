# app/models/user_models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, JSON, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.context import CryptContext
from .base import Base
# Remover la importación de werkzeug
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#Base = declarative_base()

# Función auxiliar para obtener la hora actual en UTC
def get_utc_now():
    return datetime.now(timezone.utc)

# =============================================
# MODELO VENDEDOR
# =============================================

class VendedorModel(Base):
    __tablename__ = "vendedores"
    
    # IDs y referencias
    vendedor_id = Column(Integer, primary_key=True, index=True)
    dni = Column(String(8), unique=True, index=True, nullable=False)
    codigo_vendedor = Column(String(10), unique=True, index=True, nullable=False)
    #pedidos = relationship("PedidoModel", back_populates="vendedor")
    
    # Información personal
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(150), nullable=False)
    telefono = Column(String(15), nullable=False)
    email = Column(String(150), unique=True, index=True)
    
    # Ubicación
    direccion = Column(Text)
    distrito = Column(String(100))
    provincia = Column(String(100))
    departamento = Column(String(100))
    
    # Credenciales y autenticación
    password_hash = Column(String(255), nullable=False)
    token_fcm = Column(String(255))  # Para notificaciones push
    
    # Estado y control
    activo = Column(Boolean, default=True)
    verificado = Column(Boolean, default=False)
    fecha_registro = Column(DateTime, default=get_utc_now)
    ultima_conexion = Column(DateTime)
    
    # Geolocalización
    latitud_actual = Column(Float)
    longitud_actual = Column(Float)
    precision_gps = Column(Float)
    ultima_ubicacion = Column(DateTime)
    
    # Configuraciones
    configuraciones = Column(JSON, default={})
    
    # Relaciones
    sesiones = relationship("SesionActivaModel", back_populates="vendedor", cascade="all, delete-orphan")
    # Relación inversa
    pedidos = relationship("PedidoModel", back_populates="vendedor")
    
    def set_password(self, password: str):
        """Establece la contraseña hasheada"""
        self.password_hash = pwd_context.hash(password)

    def check_password(self, password: str) -> bool:
        """Verifica la contraseña"""
        return pwd_context.verify(password, self.password_hash)

    
    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo"""
        return f"{self.nombre} {self.apellidos}"
    
    @property
    def esta_en_linea(self) -> bool:
        """Verifica si el vendedor está en línea"""
        if not self.ultima_conexion:
            return False
        tiempo_limite = get_utc_now() - timedelta(minutes=5)
        return self.ultima_conexion > tiempo_limite

# =============================================
# MODELO EVALUADOR
# =============================================

class EvaluadorModel(Base):
    __tablename__ = "evaluadores"
    
    evaluador_id = Column(Integer, primary_key=True, autoincrement=True)
    dni = Column(String(8), unique=True, nullable=False, index=True)
    codigo_evaluador = Column(String(10), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(150), nullable=False)
    telefono = Column(String(15))
    email = Column(String(150))
    direccion_trabajo = Column(String)
    
    # Zonas asignadas (departamento/provincia/distrito)
    distrito_asignado = Column(String(100))
    provincia_asignada = Column(String(100))
    departamento_asignado = Column(String(100))
    areas_evaluacion = Column(JSONB, default=list)  # Array de zonas/rutas
    
    # Autenticación
    password_hash = Column(String(255), nullable=False)
    token_fcm = Column(String(255))  # Para notificaciones push
    
    # Estado
    activo = Column(Boolean, default=True)
    verificado = Column(Boolean, default=False)
    limite_aprobacion = Column(DECIMAL(12, 2), default=5000.00)  # Nuevo campo
    
    # Tracking
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    ultima_conexion = Column(DateTime)
    
    # GPS
    latitud_actual = Column(Float)
    longitud_actual = Column(Float)
    precision_gps = Column(Float)
    ultima_ubicacion = Column(DateTime)
    
    # Configuraciones personalizadas
    configuraciones = Column(JSONB, default=dict)
    
    # Relaciones
    evaluaciones = relationship("EvaluacionPedidoModel", back_populates="evaluador")
    sesiones = relationship("SesionActivaModel", back_populates="evaluador")
    
    def set_password(self, password: str):
        """Hashea y guarda contraseña"""
        self.password_hash = pwd_context.hash(password)
    
    def check_password(self, password: str) -> bool:
        """Verifica contraseña"""
        return pwd_context.verify(password, self.password_hash)
    
    def puede_aprobar_monto(self, monto: float) -> bool:
        """Verifica si puede aprobar un monto específico"""
        return monto <= float(self.limite_aprobacion)
    
    def esta_en_zona(self, departamento: str, provincia: str = None, distrito: str = None) -> bool:
        """Verifica si una ubicación está en su zona asignada"""
        if self.departamento_asignado and self.departamento_asignado != departamento:
            return False
        if provincia and self.provincia_asignada and self.provincia_asignada != provincia:
            return False
        if distrito and self.distrito_asignado and self.distrito_asignado != distrito:
            return False
        return True

# =============================================
# MODELO SUPERVISOR
# =============================================

class SupervisorModel(Base):
    __tablename__ = "supervisores"
    
    # IDs y referencias
    supervisor_id = Column(Integer, primary_key=True, index=True)
    dni = Column(String(8), unique=True, index=True, nullable=False)
    codigo_supervisor = Column(String(10), unique=True, index=True, nullable=False)
    
    # Información personal
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(150), nullable=False)
    telefono = Column(String(15), nullable=False)
    email = Column(String(150), unique=True, index=True)
    
    # Información organizacional
    cargo = Column(String(100))
    nivel_acceso = Column(String(20), default="supervisor")  # supervisor, gerente, admin
    
    # Credenciales y autenticación
    password_hash = Column(String(255), nullable=False)
    token_fcm = Column(String(255))
    
    # Estado y control
    activo = Column(Boolean, default=True)
    verificado = Column(Boolean, default=False)
    fecha_registro = Column(DateTime, default=get_utc_now)
    ultima_conexion = Column(DateTime)
    
    # Permisos y configuraciones
    permisos = Column(JSON, default={})
    configuraciones = Column(JSON, default={})
    
    # Relaciones
    sesiones = relationship("SesionActivaModel", back_populates="supervisor", cascade="all, delete-orphan")
    
    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)

    def check_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)
    
    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellidos}"
    
    def tiene_permiso(self, permiso: str) -> bool:
        """Verifica si el supervisor tiene un permiso específico"""
        return self.permisos.get(permiso, False)

# =============================================
# MODELO SESIÓN ACTIVA
# =============================================

class SesionActivaModel(Base):
    __tablename__ = "sesiones_activas"
    
    # Identificadores
    sesion_id = Column(String(50), primary_key=True, index=True)  # UUID
    
    # Referencias a usuarios (solo uno será no nulo)
    vendedor_id = Column(Integer, ForeignKey("vendedores.vendedor_id"), nullable=True)
    evaluador_id = Column(Integer, ForeignKey("evaluadores.evaluador_id"), nullable=True) 
    supervisor_id = Column(Integer, ForeignKey("supervisores.supervisor_id"), nullable=True)
    
    # Información de sesión
    tipo_usuario = Column(String(20), nullable=False)  # vendedor, evaluador, supervisor
    token_acceso = Column(String(500), nullable=False)
    ip_origen = Column(String(45))
    user_agent = Column(Text)
    
    # Timestamps
    fecha_inicio = Column(DateTime, default=get_utc_now)
    fecha_expiracion = Column(DateTime, nullable=False)
    ultima_actividad = Column(DateTime, default=get_utc_now)
    
    # Estado
    activa = Column(Boolean, default=True)
    dispositivo_info = Column(JSON, default={})
    
    # Relaciones
    vendedor = relationship("VendedorModel", back_populates="sesiones")
    evaluador = relationship("EvaluadorModel", back_populates="sesiones")
    supervisor = relationship("SupervisorModel", back_populates="sesiones")

    @property
    def esta_expirada(self) -> bool:
        """Verifica si la sesión está expirada"""
        return get_utc_now() > self.fecha_expiracion
    
    def extender_expiracion(self, horas: int = 8):
        """Extiende la expiración de la sesión"""
        self.fecha_expiracion = get_utc_now() + timedelta(hours=horas)
        self.ultima_actividad = get_utc_now()

# =============================================
# MODELO CONFIGURACIÓN USUARIO
# =============================================

class ConfiguracionUsuarioModel(Base):
    __tablename__ = "configuraciones_usuario"
    
    configuracion_id = Column(Integer, primary_key=True, index=True)
    
    # Referencias (solo una será no nula)
    vendedor_id = Column(Integer, ForeignKey("vendedores.vendedor_id"), nullable=True)
    evaluador_id = Column(Integer, ForeignKey("evaluadores.evaluador_id"), nullable=True)
    supervisor_id = Column(Integer, ForeignKey("supervisores.supervisor_id"), nullable=True)
    
    # Configuraciones específicas
    clave_configuracion = Column(String(100), nullable=False)
    valor_configuracion = Column(Text, nullable=False)
    tipo_dato = Column(String(20), default="string")  # string, int, float, boolean, json
    
    # Metadatos
    descripcion = Column(Text)
    categoria = Column(String(50))  # ui, notificaciones, gps, etc.
    
    # Control de cambios
    fecha_creacion = Column(DateTime, default=get_utc_now)
    fecha_modificacion = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    def get_valor_tipado(self):
        """Retorna el valor en su tipo correcto"""
        if self.tipo_dato == "int":
            return int(self.valor_configuracion)
        elif self.tipo_dato == "float":
            return float(self.valor_configuracion)
        elif self.tipo_dato == "boolean":
            return self.valor_configuracion.lower() in ("true", "1", "yes")
        elif self.tipo_dato == "json":
            import json
            return json.loads(self.valor_configuracion)
        else:
            return self.valor_configuracion
        

# Agregar al final de user_models.py

# =============================================
# MODELO EVALUADOR  
# =============================================
"""
class EvaluadorModel(Base):
    __tablename__ = "evaluadores"
    
    # IDs y referencias
    evaluador_id = Column(Integer, primary_key=True, index=True)
    dni = Column(String(8), unique=True, index=True, nullable=False)
    codigo_evaluador = Column(String(10), unique=True, index=True, nullable=False)
    
    # Información personal
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(150), nullable=False)
    telefono = Column(String(15), nullable=False)
    email = Column(String(150), unique=True, index=True)
    
    # Credenciales y autenticación
    password_hash = Column(String(255), nullable=False)
    token_fcm = Column(String(255))
    
    # Estado y control
    activo = Column(Boolean, default=True)
    verificado = Column(Boolean, default=False)
    fecha_registro = Column(DateTime, default=get_utc_now)
    ultima_conexion = Column(DateTime)
    
    # Configuraciones
    configuraciones = Column(JSON, default={})
    
    # Relaciones
    sesiones = relationship("SesionActivaModel", back_populates="evaluador", cascade="all, delete-orphan")
    
    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)

    def check_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)
    
    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellidos}"

"""

# =============================================
# MODELO SUPERVISOR
# =============================================

"""
class SupervisorModel(Base):
    __tablename__ = "supervisores"
    
    # IDs y referencias
    supervisor_id = Column(Integer, primary_key=True, index=True)
    dni = Column(String(8), unique=True, index=True, nullable=False)
    codigo_supervisor = Column(String(10), unique=True, index=True, nullable=False)
    
    # Información personal
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(150), nullable=False)
    telefono = Column(String(15), nullable=False)
    email = Column(String(150), unique=True, index=True)
    cargo = Column(String(100))
    nivel_acceso = Column(String(20), default="supervisor")
    
    # Credenciales y autenticación
    password_hash = Column(String(255), nullable=False)
    token_fcm = Column(String(255))
    
    # Estado y control
    activo = Column(Boolean, default=True)
    verificado = Column(Boolean, default=False)
    fecha_registro = Column(DateTime, default=get_utc_now)
    ultima_conexion = Column(DateTime)
    
    # Permisos y configuraciones
    permisos = Column(JSON, default={})
    configuraciones = Column(JSON, default={})
    
    # Relaciones
    sesiones = relationship("SesionActivaModel", back_populates="supervisor", cascade="all, delete-orphan")
    
    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)

    def check_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)
    
    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellidos}"
    """