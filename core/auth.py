# core/auth.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Union
from jose import jwt
import uuid
import secrets
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_models import VendedorModel, EvaluadorModel, SupervisorModel, SesionActivaModel
from app.schemas.common_schemas import TipoUsuario
from core.config import settings


# Función auxiliar para obtener la hora actual en UTC
def get_utc_now():
    return datetime.now(timezone.utc)

# =============================================
# CONFIGURACIÓN DE SEGURIDAD
# =============================================

# Configuración para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración de JWT
JWT_SECRET_KEY = settings.SECRET_KEY
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_HOURS = settings.ACCESS_TOKEN_EXPIRE_HOURS

# Esquema de seguridad HTTP Bearer
security = HTTPBearer(auto_error=False)

# =============================================
# UTILIDADES DE CONTRASEÑAS
# =============================================

def hash_password(password: str) -> str:
    """Hashea una contraseña usando bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash"""
    return pwd_context.verify(plain_password, hashed_password)

def generate_password() -> str:
    """Genera una contraseña temporal segura"""
    return secrets.token_urlsafe(12)

# =============================================
# JWT TOKENS
# =============================================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT de acceso"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=JWT_ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4())  # JWT ID único
    })
    
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodifica y valida un token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido", 
            headers={"WWW-Authenticate": "Bearer"}
        )

# =============================================
# AUTENTICACIÓN DE USUARIOS
# =============================================

def authenticate_user(
    db: Session, 
    identifier: str,  # puede ser DNI, código o email
    password: str,
    tipo_usuario: TipoUsuario
) -> Optional[Union[VendedorModel, EvaluadorModel, SupervisorModel]]:
    """Autentica un usuario según su tipo"""
    
    user = None
    
    try:
        if tipo_usuario == TipoUsuario.VENDEDOR:
            # Buscar por DNI, código o email
            user = db.query(VendedorModel).filter(
                (VendedorModel.dni == identifier) |
                (VendedorModel.codigo_vendedor == identifier) |
                (VendedorModel.email == identifier)
            ).filter(VendedorModel.activo == True).first()
            
        elif tipo_usuario == TipoUsuario.EVALUADOR:
            user = db.query(EvaluadorModel).filter(
                (EvaluadorModel.dni == identifier) |
                (EvaluadorModel.codigo_evaluador == identifier) |
                (EvaluadorModel.email == identifier)
            ).filter(EvaluadorModel.activo == True).first()
            
        elif tipo_usuario == TipoUsuario.SUPERVISOR:
            user = db.query(SupervisorModel).filter(
                (SupervisorModel.dni == identifier) |
                (SupervisorModel.codigo_supervisor == identifier) |
                (SupervisorModel.email == identifier)
            ).filter(SupervisorModel.activo == True).first()
            
        # Verificar contraseña
        if user and verify_password(password, user.password_hash):
            # Actualizar última conexión
            user.ultima_conexion = datetime.now(timezone.utc)
            db.commit()
            return user
            
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en autenticación: {str(e)}"
        )
    
    return None

# =============================================
# GESTIÓN DE SESIONES
# =============================================

def create_user_session(
    db: Session,
    user: Union[VendedorModel, EvaluadorModel, SupervisorModel],
    tipo_usuario: TipoUsuario,
    request: Request
) -> SesionActivaModel:
    """Crea una nueva sesión activa para el usuario"""
    
    try:
        # Generar ID de sesión único
        session_id = str(uuid.uuid4())
        
        # Obtener nombre completo según el tipo de usuario
        if tipo_usuario == TipoUsuario.VENDEDOR:
            nombre_completo = f"{user.nombre} {user.apellidos}"  # ✅ CORREGIDO
            user_id = user.vendedor_id
            user_code = user.codigo_vendedor
        elif tipo_usuario == TipoUsuario.EVALUADOR:
            nombre_completo = f"{user.nombre} {user.apellidos}"  # ✅ CORREGIDO
            user_id = user.evaluador_id
            user_code = user.codigo_evaluador
        else:  # SUPERVISOR
            nombre_completo = f"{user.nombre} {user.apellidos}"  # ✅ CORREGIDO
            user_id = user.supervisor_id
            user_code = user.codigo_supervisor
        
        print(f"🟦 Creando sesión para: {nombre_completo} ({tipo_usuario.value})")
        
        # Crear token de acceso
        token_data = {
            "session_id": session_id,
            "user_id": user_id,
            "tipo_usuario": tipo_usuario.value,
            "user_code": user_code,
            "nombre": nombre_completo
        }
        
        access_token = create_access_token(data=token_data)
        
        # Información del dispositivo/cliente
        device_info = {
            "user_agent": str(request.headers.get("user-agent", "")),
            "ip": request.client.host if request.client else "unknown",
            "platform": request.headers.get("sec-ch-ua-platform", "unknown")
        }
        
        # Cerrar sesiones anteriores del mismo usuario
        old_sessions = db.query(SesionActivaModel).filter(
            getattr(SesionActivaModel, f"{tipo_usuario.value}_id") == user_id,
            SesionActivaModel.activa == True
        ).all()
        
        for old_session in old_sessions:
            old_session.activa = False
        
        # Crear nueva sesión
        nueva_sesion = SesionActivaModel(
            sesion_id=session_id,
            tipo_usuario=tipo_usuario.value,
            token_acceso=access_token,
            ip_origen=device_info["ip"],
            user_agent=device_info["user_agent"],
            fecha_expiracion=datetime.now(timezone.utc) + timedelta(hours=JWT_ACCESS_TOKEN_EXPIRE_HOURS),
            dispositivo_info=device_info,
            activa=True
        )
        
        # Asignar a usuario correspondiente
        if tipo_usuario == TipoUsuario.VENDEDOR:
            nueva_sesion.vendedor_id = user.vendedor_id
        elif tipo_usuario == TipoUsuario.EVALUADOR:
            nueva_sesion.evaluador_id = user.evaluador_id
        elif tipo_usuario == TipoUsuario.SUPERVISOR:
            nueva_sesion.supervisor_id = user.supervisor_id
        
        db.add(nueva_sesion)
        db.commit()
        db.refresh(nueva_sesion)
        
        print(f"🟦 Sesión creada exitosamente: {session_id}")
        return nueva_sesion
        
    except Exception as e:
        db.rollback()
        print(f"🔴 ERROR en create_user_session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando sesión: {str(e)}"
        )

def get_session_by_token(db: Session, token: str) -> Optional[SesionActivaModel]:
    """Obtiene una sesión activa por su token"""
    try:
        # Decodificar token para obtener session_id
        payload = decode_access_token(token)
        session_id = payload.get("session_id")
        
        if not session_id:
            return None
            
        # Buscar sesión activa
        session = db.query(SesionActivaModel).filter(
            SesionActivaModel.sesion_id == session_id,
            SesionActivaModel.activa == True
        ).first()
        
        if session and not session.esta_expirada:
            # Actualizar última actividad
            session.ultima_actividad = datetime.now(timezone.utc)
            db.commit()
            return session
            
        # Si la sesión existe pero está expirada, marcarla como inactiva
        if session and session.esta_expirada:
            session.activa = False
            db.commit()
            
        return None
        
    except Exception:
        return None

def close_user_session(db: Session, session_id: str) -> bool:
    """Cierra una sesión específica"""
    try:
        session = db.query(SesionActivaModel).filter(
            SesionActivaModel.sesion_id == session_id,
            SesionActivaModel.activa == True
        ).first()
        
        if session:
            session.activa = False
            db.commit()
            return True
            
        return False
        
    except Exception:
        db.rollback()
        return False

# =============================================
# DEPENDENCIAS DE AUTENTICACIÓN
# =============================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Dependency para obtener usuario actual autenticado"""
    
    print(f"=== DEBUG get_current_user ===")
    print(f"credentials: {credentials}")
    print(f"token: {credentials.credentials[:50] if credentials else 'NO TOKEN'}...")
    
    if not credentials:
        print("❌ No hay credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorización requerido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # OPCIÓN 1: Solo decodificar el JWT sin verificar sesiones
    try:
        payload = decode_access_token(credentials.credentials)
        print(f"Payload decodificado: {payload}")
        
        # Adaptar los nombres de campos de tu JWT
        user_data = {
            "user_id": payload.get("id"),  # Tu JWT usa "id" 
            "tipo_usuario": payload.get("tipo"),  # Tu JWT usa "tipo"
            "nombre": payload.get("nombre"),
            "dni": payload.get("dni"),
            "session_id": payload.get("jti")  # JWT ID como session_id
        }
        
        print(f"✅ User data adaptado: {user_data}")
        print(f"==============================")
        
        return user_data
        
    except Exception as e:
        print(f"❌ Error decodificando token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_vendedor(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> VendedorModel:
    """Dependency para obtener vendedor actual"""
    
    print(f"=== DEBUG get_current_vendedor ===")
    print(f"current_user: {current_user}")
    print(f"tipo_usuario: {current_user.get('tipo_usuario')}")
    print(f"user_id: {current_user.get('user_id')}")
    
    if current_user["tipo_usuario"] != "vendedor":  # Cambiar a string si no usas enum
        print(f"❌ Tipo de usuario incorrecto: {current_user['tipo_usuario']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso solo permitido para vendedores"
        )
    
    # Buscar vendedor por user_id
    vendedor = db.query(VendedorModel).filter(
        VendedorModel.vendedor_id == current_user["user_id"],  # Campo correcto
        VendedorModel.activo == True
    ).first()
    
    print(f"Consulta SQL: SELECT * FROM vendedores WHERE vendedor_id = {current_user['user_id']} AND activo = True")
    print(f"Vendedor encontrado: {vendedor}")
    
    if not vendedor:
        print("❌ Vendedor no encontrado en la base de datos")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendedor no encontrado"
        )
    
    print(f"✅ Vendedor: ID={vendedor.vendedor_id}, Nombre={vendedor.nombre}")
    print(f"===================================")
    
    return vendedor

async def get_current_evaluador(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> EvaluadorModel:
    """Dependency para obtener evaluador actual"""
    
    if current_user["tipo_usuario"] != "evaluador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso solo permitido para evaluadores"
        )
    
    evaluador = db.query(EvaluadorModel).filter(
        EvaluadorModel.evaluador_id == current_user["user_id"],
        EvaluadorModel.activo == True
    ).first()
    
    if not evaluador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluador no encontrado"
        )
    
    return evaluador

async def get_current_supervisor(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SupervisorModel:
    """Dependency para obtener supervisor actual"""
    
    if current_user["tipo_usuario"] != TipoUsuario.SUPERVISOR.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso solo permitido para supervisores"
        )
    
    supervisor = db.query(SupervisorModel).filter(
        SupervisorModel.supervisor_id == current_user["user_id"],
        SupervisorModel.activo == True
    ).first()
    
    if not supervisor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supervisor no encontrado"
        )
    
    return supervisor

# =============================================
# DEPENDENCIAS CON PERMISOS
# =============================================

def require_permission(permission: str):
    """Decorator para requerir permisos específicos (solo supervisores)"""
    def dependency(supervisor: SupervisorModel = Depends(get_current_supervisor)):
        if not supervisor.tiene_permiso(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso '{permission}' requerido"
            )
        return supervisor
    return dependency

def require_user_types(*allowed_types: TipoUsuario):
    """Dependency que permite acceso solo a tipos de usuario específicos"""
    async def dependency(current_user: Dict[str, Any] = Depends(get_current_user)):
        if current_user["tipo_usuario"] not in [t.value for t in allowed_types]:
            types_str = ", ".join([t.value for t in allowed_types])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso restringido. Tipos permitidos: {types_str}"
            )
        return current_user
    return dependency

# =============================================
# UTILIDADES DE SEGURIDAD
# =============================================

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Valida la fortaleza de una contraseña"""
    import re
    
    result = {
        "valid": True,
        "score": 0,
        "issues": []
    }
    
    # Longitud mínima
    if len(password) < 8:
        result["issues"].append("Debe tener al menos 8 caracteres")
        result["valid"] = False
    else:
        result["score"] += 1
    
    # Contiene mayúsculas
    if re.search(r'[A-Z]', password):
        result["score"] += 1
    else:
        result["issues"].append("Debe contener al menos una mayúscula")
    
    # Contiene minúsculas
    if re.search(r'[a-z]', password):
        result["score"] += 1
    else:
        result["issues"].append("Debe contener al menos una minúscula")
    
    # Contiene números
    if re.search(r'\d', password):
        result["score"] += 1
    else:
        result["issues"].append("Debe contener al menos un número")
    
    # Contiene caracteres especiales
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result["score"] += 1
    
    # Validación final
    if len(result["issues"]) > 0:
        result["valid"] = False
    
    return result

def generate_session_id() -> str:
    """Genera un ID de sesión único"""
    return str(uuid.uuid4())

def clean_expired_sessions(db: Session) -> int:
    """Limpia sesiones expiradas de la base de datos"""
    try:
        expired_sessions = db.query(SesionActivaModel).filter(
            SesionActivaModel.fecha_expiracion < datetime.now(timezone.utc),
            SesionActivaModel.activa == True
        ).all()
        
        count = len(expired_sessions)
        
        for session in expired_sessions:
            session.activa = False
        
        db.commit()
        return count
        
    except Exception:
        db.rollback()
        return 0


def verify_token(token: str) -> bool:
    """Verifica si un token es válido"""
    try:
        decode_access_token(token)
        return True
    except:
        return False