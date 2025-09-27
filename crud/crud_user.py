# app/crud/crud_user.py
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta, timezone

# Imports CORRECTOS para tu estructura
from app.models.user_models import VendedorModel, EvaluadorModel, SupervisorModel, SesionActivaModel
from app.schemas.user_schemas import VendedorCreate, VendedorUpdate, EvaluadorCreate, EvaluadorUpdate, SupervisorCreate, SupervisorUpdate
from crud.base import CRUDBase


# Función auxiliar para obtener la hora actual en UTC
def get_utc_now():
    return datetime.now(timezone.utc)

# =============================================
# CRUD VENDEDORES
# =============================================

class CRUDVendedor(CRUDBase[VendedorModel, VendedorCreate, VendedorUpdate]):
    
    def get_by_dni(self, db: Session, *, dni: str) -> Optional[VendedorModel]:
        """Obtiene vendedor por DNI"""
        return db.query(VendedorModel).filter(
            VendedorModel.dni == dni,
            VendedorModel.activo == True
        ).first()
    
    def get_by_codigo(self, db: Session, *, codigo: str) -> Optional[VendedorModel]:
        """Obtiene vendedor por código"""
        return db.query(VendedorModel).filter(
            VendedorModel.codigo_vendedor == codigo,
            VendedorModel.activo == True
        ).first()
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[VendedorModel]:
        """Obtiene vendedor por email"""
        return db.query(VendedorModel).filter(
            VendedorModel.email == email,
            VendedorModel.activo == True
        ).first()
    
    def get_active_vendedores(self, db: Session, skip: int = 0, limit: int = 100) -> List[VendedorModel]:
        """Obtiene vendedores activos"""
        return db.query(VendedorModel).filter(
            VendedorModel.activo == True
        ).offset(skip).limit(limit).all()
    
    def get_vendedores_online(self, db: Session) -> List[VendedorModel]:
        """Obtiene vendedores conectados en los últimos 5 minutos"""
        tiempo_limite = get_utc_now - timedelta(minutes=5)
        return db.query(VendedorModel).filter(
            VendedorModel.activo == True,
            VendedorModel.ultima_conexion >= tiempo_limite
        ).all()
    
    def update_location(
        self, 
        db: Session, 
        *, 
        vendedor_id: int, 
        latitud: float, 
        longitud: float,
        precision: Optional[float] = None
    ) -> Optional[VendedorModel]:
        """Actualiza la ubicación GPS del vendedor"""
        vendedor = self.get(db=db, id=vendedor_id)
        if not vendedor:
            return None
        
        update_data = {
            "latitud_actual": latitud,
            "longitud_actual": longitud,
            "precision_gps": precision,
            "ultima_ubicacion": get_utc_now
        }
        
        return self.update(db=db, db_obj=vendedor, obj_in=update_data)
    
    def authenticate(self, db: Session, *, identifier: str, password: str) -> Optional[VendedorModel]:
        """Autentica un vendedor por DNI, código o email"""
        vendedor = db.query(VendedorModel).filter(
            (VendedorModel.dni == identifier) |
            (VendedorModel.codigo_vendedor == identifier) |
            (VendedorModel.email == identifier),
            VendedorModel.activo == True
        ).first()
        
        if vendedor and vendedor.check_password(password):
            # Actualizar última conexión
            vendedor.ultima_conexion = get_utc_now
            db.commit()
            return vendedor
        return None
    
    def update_fcm_token(self, db: Session, *, vendedor_id: int, token: str) -> Optional[VendedorModel]:
        """Actualiza el token FCM para notificaciones push"""
        vendedor = self.get(db=db, id=vendedor_id)
        if vendedor:
            return self.update(db=db, db_obj=vendedor, obj_in={"token_fcm": token})
        return None

# =============================================
# CRUD EVALUADORES
# =============================================

class CRUDEvaluador(CRUDBase[EvaluadorModel, EvaluadorCreate, EvaluadorUpdate]):
    
    def get_by_dni(self, db: Session, *, dni: str) -> Optional[EvaluadorModel]:
        """Obtiene evaluador por DNI"""
        return db.query(EvaluadorModel).filter(
            EvaluadorModel.dni == dni,
            EvaluadorModel.activo == True
        ).first()
    
    def get_by_codigo(self, db: Session, *, codigo: str) -> Optional[EvaluadorModel]:
        """Obtiene evaluador por código"""
        return db.query(EvaluadorModel).filter(
            EvaluadorModel.codigo_evaluador == codigo,
            EvaluadorModel.activo == True
        ).first()
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[EvaluadorModel]:
        """Obtiene evaluador por email"""
        return db.query(EvaluadorModel).filter(
            EvaluadorModel.email == email,
            EvaluadorModel.activo == True
        ).first()
    
    def get_by_area(self, db: Session, *, distrito: str) -> List[EvaluadorModel]:
        """Obtiene evaluadores asignados a un distrito"""
        return db.query(EvaluadorModel).filter(
            EvaluadorModel.distrito_asignado.ilike(f"%{distrito}%"),
            EvaluadorModel.activo == True
        ).all()
    
    def authenticate(self, db: Session, *, identifier: str, password: str) -> Optional[EvaluadorModel]:
        """Autentica un evaluador"""
        evaluador = db.query(EvaluadorModel).filter(
            (EvaluadorModel.dni == identifier) |
            (EvaluadorModel.codigo_evaluador == identifier) |
            (EvaluadorModel.email == identifier),
            EvaluadorModel.activo == True
        ).first()
        
        if evaluador and evaluador.check_password(password):
            evaluador.ultima_conexion = get_utc_now
            db.commit()
            return evaluador
        return None
    
    def update_location(
        self, 
        db: Session, 
        *, 
        evaluador_id: int, 
        latitud: float, 
        longitud: float,
        precision: Optional[float] = None
    ) -> Optional[EvaluadorModel]:
        """Actualiza la ubicación del evaluador"""
        evaluador = self.get(db=db, id=evaluador_id)
        if not evaluador:
            return None
        
        update_data = {
            "latitud_actual": latitud,
            "longitud_actual": longitud,
            "precision_gps": precision,
            "ultima_ubicacion": get_utc_now
        }
        
        return self.update(db=db, db_obj=evaluador, obj_in=update_data)

# =============================================
# CRUD SUPERVISORES
# =============================================

class CRUDSupervisor(CRUDBase[SupervisorModel, SupervisorCreate, SupervisorUpdate]):
    
    def get_by_dni(self, db: Session, *, dni: str) -> Optional[SupervisorModel]:
        """Obtiene supervisor por DNI"""
        return db.query(SupervisorModel).filter(
            SupervisorModel.dni == dni,
            SupervisorModel.activo == True
        ).first()
    
    def get_by_codigo(self, db: Session, *, codigo: str) -> Optional[SupervisorModel]:
        """Obtiene supervisor por código"""
        return db.query(SupervisorModel).filter(
            SupervisorModel.codigo_supervisor == codigo,
            SupervisorModel.activo == True
        ).first()
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[SupervisorModel]:
        """Obtiene supervisor por email"""
        return db.query(SupervisorModel).filter(
            SupervisorModel.email == email,
            SupervisorModel.activo == True
        ).first()
    
    def get_by_nivel_acceso(self, db: Session, *, nivel: str) -> List[SupervisorModel]:
        """Obtiene supervisores por nivel de acceso"""
        return db.query(SupervisorModel).filter(
            SupervisorModel.nivel_acceso == nivel,
            SupervisorModel.activo == True
        ).all()
    
    def authenticate(self, db: Session, *, identifier: str, password: str) -> Optional[SupervisorModel]:
        """Autentica un supervisor"""
        supervisor = db.query(SupervisorModel).filter(
            (SupervisorModel.dni == identifier) |
            (SupervisorModel.codigo_supervisor == identifier) |
            (SupervisorModel.email == identifier),
            SupervisorModel.activo == True
        ).first()
        
        if supervisor and supervisor.check_password(password):
            supervisor.ultima_conexion = get_utc_now
            db.commit()
            return supervisor
        return None
    
    def update_permissions(
        self, 
        db: Session, 
        *, 
        supervisor_id: int, 
        permisos: Dict[str, bool]
    ) -> Optional[SupervisorModel]:
        """Actualiza permisos del supervisor"""
        supervisor = self.get(db=db, id=supervisor_id)
        if supervisor:
            current_perms = supervisor.permisos or {}
            current_perms.update(permisos)
            return self.update(db=db, db_obj=supervisor, obj_in={"permisos": current_perms})
        return None

# =============================================
# CRUD SESIONES ACTIVAS
# =============================================

class CRUDSesionActiva(CRUDBase[SesionActivaModel, dict, dict]):
    
    def get_by_session_id(self, db: Session, *, session_id: str) -> Optional[SesionActivaModel]:
        """Obtiene sesión por ID de sesión"""
        return db.query(SesionActivaModel).filter(
            SesionActivaModel.sesion_id == session_id,
            SesionActivaModel.activa == True
        ).first()
    
    def get_user_sessions(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        tipo_usuario: str
    ) -> List[SesionActivaModel]:
        """Obtiene sesiones activas de un usuario"""
        if tipo_usuario == "vendedor":
            return db.query(SesionActivaModel).filter(
                SesionActivaModel.vendedor_id == user_id,
                SesionActivaModel.activa == True
            ).all()
        elif tipo_usuario == "evaluador":
            return db.query(SesionActivaModel).filter(
                SesionActivaModel.evaluador_id == user_id,
                SesionActivaModel.activa == True
            ).all()
        elif tipo_usuario == "supervisor":
            return db.query(SesionActivaModel).filter(
                SesionActivaModel.supervisor_id == user_id,
                SesionActivaModel.activa == True
            ).all()
        return []
    
    def close_user_sessions(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        tipo_usuario: str
    ) -> int:
        """Cierra todas las sesiones de un usuario"""
        sessions = self.get_user_sessions(db=db, user_id=user_id, tipo_usuario=tipo_usuario)
        count = 0
        for session in sessions:
            session.activa = False
            count += 1
        db.commit()
        return count
    
    def clean_expired_sessions(self, db: Session) -> int:
        """Limpia sesiones expiradas"""
        expired_sessions = db.query(SesionActivaModel).filter(
            SesionActivaModel.fecha_expiracion < get_utc_now,
            SesionActivaModel.activa == True
        ).all()
        
        count = len(expired_sessions)
        for session in expired_sessions:
            session.activa = False
        
        db.commit()
        return count
    
    def extend_session(
        self, 
        db: Session, 
        *, 
        session_id: str, 
        hours: int = 8
    ) -> Optional[SesionActivaModel]:
        """Extiende la duración de una sesión"""
        session = self.get_by_session_id(db=db, session_id=session_id)
        if session:
            session.extender_expiracion(hours)
            db.commit()
            return session
        return None

# =============================================
# UTILIDADES GENERALES
# =============================================

def get_user_by_identifier(
    db: Session, 
    *, 
    identifier: str, 
    tipo_usuario: str
) -> Optional[Union[VendedorModel, EvaluadorModel, SupervisorModel]]:
    """Busca un usuario por identificador (DNI, código o email) y tipo"""
    if tipo_usuario == "vendedor":
        return db.query(VendedorModel).filter(
            (VendedorModel.dni == identifier) |
            (VendedorModel.codigo_vendedor == identifier) |
            (VendedorModel.email == identifier),
            VendedorModel.activo == True
        ).first()
    elif tipo_usuario == "evaluador":
        return db.query(EvaluadorModel).filter(
            (EvaluadorModel.dni == identifier) |
            (EvaluadorModel.codigo_evaluador == identifier) |
            (EvaluadorModel.email == identifier),
            EvaluadorModel.activo == True
        ).first()
    elif tipo_usuario == "supervisor":
        return db.query(SupervisorModel).filter(
            (SupervisorModel.dni == identifier) |
            (SupervisorModel.codigo_supervisor == identifier) |
            (SupervisorModel.email == identifier),
            SupervisorModel.activo == True
        ).first()
    return None

def count_active_users_by_type(db: Session) -> Dict[str, int]:
    """Cuenta usuarios activos por tipo"""
    return {
        "vendedores": db.query(VendedorModel).filter(VendedorModel.activo == True).count(),
        "evaluadores": db.query(EvaluadorModel).filter(EvaluadorModel.activo == True).count(),
        "supervisores": db.query(SupervisorModel).filter(SupervisorModel.activo == True).count(),
    }

# =============================================
# INSTANCIAS DE CRUD
# =============================================

crud_vendedor = CRUDVendedor(VendedorModel)
crud_evaluador = CRUDEvaluador(EvaluadorModel)
crud_supervisor = CRUDSupervisor(SupervisorModel)
crud_sesion_activa = CRUDSesionActiva(SesionActivaModel)