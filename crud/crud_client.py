from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from crud.base import CRUDBase
from app.models.client_models import ClienteModel
from app.schemas.client_schemas import ClienteCreate, ClienteUpdate

# Verificar si existe ContactoClienteModel
try:
    from app.models.contacto_cliente import ContactoClienteModel
    TIENE_CONTACTOS = True
except ImportError:
    TIENE_CONTACTOS = False

# ============================================================================
# CRUD CLIENTE
# ============================================================================

class CRUDCliente(CRUDBase[ClienteModel, ClienteCreate, ClienteUpdate]):
    """CRUD operations para Cliente"""
    
    def generar_codigo_cliente(self, db: Session, tipo_cliente_id: int) -> str:
        """
        Genera un código único para el cliente
        Formato: TC1-00001, TC2-00001, etc
        """
        ultimo_cliente = db.query(ClienteModel).filter(
            ClienteModel.tipo_cliente_id == tipo_cliente_id
        ).order_by(ClienteModel.id.desc()).first()
        
        if ultimo_cliente and ultimo_cliente.codigo_cliente:
            try:
                numero = int(ultimo_cliente.codigo_cliente.split('-')[1]) + 1
            except:
                numero = 1
        else:
            numero = 1
        
        return f"TC{tipo_cliente_id}-{numero:05d}"
    
    def create_with_user(
        self, 
        db: Session, 
        *, 
        obj_in: ClienteCreate, 
        usuario_id: int
    ) -> ClienteModel:
        """
        Crea un nuevo cliente con validación de RUC único
        """
        # Verificar si ya existe el RUC
        cliente_existente = db.query(ClienteModel).filter(
            ClienteModel.ruc == obj_in.ruc
        ).first()
        
        if cliente_existente:
            raise ValueError(f"Ya existe un cliente registrado con el RUC {obj_in.ruc}")
        
        # Generar código único
        codigo_cliente = self.generar_codigo_cliente(db, obj_in.tipo_cliente_id)
        
        # Crear el cliente
        db_obj = ClienteModel(
            codigo_cliente=codigo_cliente,
            nombre_comercial=obj_in.nombre_comercial,
            razon_social=obj_in.razon_social,
            ruc=obj_in.ruc,
            telefono=obj_in.telefono,
            email=obj_in.email,
            direccion_completa=obj_in.direccion_completa,
            referencia=obj_in.referencia,
            distrito=obj_in.distrito,
            provincia=obj_in.provincia,
            departamento=obj_in.departamento,
            codigo_postal=obj_in.codigo_postal,
            latitud=obj_in.latitud,
            longitud=obj_in.longitud,
            precision_gps=obj_in.precision_gps,
            tipo_cliente_id=obj_in.tipo_cliente_id,
            activo=True,
            verificado=False,
            es_moroso=False,
            deuda_actual=0,
            dias_mora=0
        )
        
        db.add(db_obj)
        db.flush()
        
        # Crear contacto principal si hay datos del titular
        if TIENE_CONTACTOS and obj_in.dni_titular and obj_in.nombres_titular:
            contacto_principal = ContactoClienteModel(
                cliente_id=db_obj.id,
                nombre=obj_in.nombres_titular,
                dni=obj_in.dni_titular,
                telefono=obj_in.telefono,
                email=obj_in.email,
                es_principal=True,
                cargo="Titular/Propietario"
            )
            db.add(contacto_principal)
        
        db.commit()
        db.refresh(db_obj)
        
        return db_obj
    
    def get_by_ruc(self, db: Session, *, ruc: str) -> Optional[ClienteModel]:
        """Obtiene un cliente por su RUC"""
        return db.query(ClienteModel).filter(ClienteModel.ruc == ruc).first()
    
    def get_by_codigo(self, db: Session, *, codigo: str) -> Optional[ClienteModel]:
        """Obtiene un cliente por su código"""
        return db.query(ClienteModel).filter(ClienteModel.codigo_cliente == codigo).first()
    
    def get_multi_filtered(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        activo: Optional[bool] = None,
        tipo_cliente_id: Optional[int] = None,
        buscar: Optional[str] = None
    ) -> List[ClienteModel]:
        """Obtiene lista de clientes con filtros"""
        query = db.query(ClienteModel)
        
        if activo is not None:
            query = query.filter(ClienteModel.activo == activo)
        
        if tipo_cliente_id:
            query = query.filter(ClienteModel.tipo_cliente_id == tipo_cliente_id)
        
        if buscar:
            search_pattern = f"%{buscar}%"
            query = query.filter(
                or_(
                    ClienteModel.nombre_comercial.ilike(search_pattern),
                    ClienteModel.razon_social.ilike(search_pattern),
                    ClienteModel.ruc.ilike(search_pattern),
                    ClienteModel.codigo_cliente.ilike(search_pattern)
                )
            )
        
        return query.order_by(ClienteModel.fecha_registro.desc()).offset(skip).limit(limit).all()
    
    def get_activos_simple(self, db: Session) -> List[ClienteModel]:
        """Obtiene lista simple de clientes activos para select/dropdown"""
        return db.query(ClienteModel).filter(
            ClienteModel.activo == True
        ).order_by(ClienteModel.nombre_comercial).all()
    
    def desactivar(self, db: Session, *, id: int) -> bool:
        """Desactiva un cliente (soft delete)"""
        obj = self.get(db, id=id)
        if not obj:
            return False
        
        obj.activo = False
        db.commit()
        return True
    
    def activar(self, db: Session, *, id: int) -> bool:
        """Activa un cliente desactivado"""
        obj = self.get(db, id=id)
        if not obj:
            return False
        
        obj.activo = True
        db.commit()
        return True


# ============================================================================
# HISTORIAL Y SEGMENTACIÓN (Placeholders)
# ============================================================================

class CRUDHistorialCliente(CRUDBase):
    """CRUD para historial de clientes - Por implementar"""
    pass


class CRUDSegmentacionCliente(CRUDBase):
    """CRUD para segmentación de clientes - Por implementar"""
    pass


# ============================================================================
# INSTANCIAS CRUD
# ============================================================================

crud_cliente = CRUDCliente(ClienteModel)
crud_historial_cliente = CRUDHistorialCliente(ClienteModel)  # Temporal
crud_segmentacion_cliente = CRUDSegmentacionCliente(ClienteModel)  # Temporal