# crud/base.py
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

# Definir tipos genéricos para cualquier modelo SQLAlchemy
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


# Función auxiliar para obtener la hora actual en UTC
def get_utc_now():
    return datetime.now(timezone.utc)

# =============================================
# CLASE CRUD BASE GENÉRICA
# =============================================

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Clase base para operaciones CRUD genéricas"""
    
    def __init__(self, model: Type[ModelType]):
        """
        Inicializa el CRUD con un modelo específico
        
        Args:
            model: El modelo SQLAlchemy para este CRUD
        """
        self.model = model

    # =============================================
    # OPERACIONES DE LECTURA
    # =============================================

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Obtiene un registro por su ID"""
        return db.query(self.model).filter(getattr(self.model, self._get_primary_key()) == id).first()

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """Obtiene múltiples registros con filtros opcionales"""
        query = db.query(self.model)
        
        # Aplicar filtros
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    if isinstance(value, list):
                        query = query.filter(getattr(self.model, key).in_(value))
                    else:
                        query = query.filter(getattr(self.model, key) == value)
        
        # Aplicar ordenamiento
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        
        return query.offset(skip).limit(limit).all()

    def count(self, db: Session, *, filters: Optional[Dict[str, Any]] = None) -> int:
        """Cuenta registros con filtros opcionales"""
        query = db.query(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    if isinstance(value, list):
                        query = query.filter(getattr(self.model, key).in_(value))
                    else:
                        query = query.filter(getattr(self.model, key) == value)
        
        return query.count()

    def exists(self, db: Session, id: Any) -> bool:
        """Verifica si existe un registro con el ID dado"""
        return db.query(self.model).filter(getattr(self.model, self._get_primary_key()) == id).first() is not None

    # =============================================
    # OPERACIONES DE CREACIÓN
    # =============================================

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Crea un nuevo registro"""
        try:
            obj_in_data = jsonable_encoder(obj_in)
            
            # Agregar timestamps si el modelo los tiene
            if hasattr(self.model, 'fecha_creacion'):
                obj_in_data['fecha_creacion'] = get_utc_now
            if hasattr(self.model, 'fecha_modificacion'):
                obj_in_data['fecha_modificacion'] = get_utc_now
            
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
            
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Error de integridad: {str(e)}")
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error creando registro: {str(e)}")

    def create_multi(self, db: Session, *, obj_list: List[CreateSchemaType]) -> List[ModelType]:
        """Crea múltiples registros en una transacción"""
        try:
            created_objects = []
            
            for obj_in in obj_list:
                obj_in_data = jsonable_encoder(obj_in)
                
                # Agregar timestamps si el modelo los tiene
                if hasattr(self.model, 'fecha_creacion'):
                    obj_in_data['fecha_creacion'] = get_utc_now
                if hasattr(self.model, 'fecha_modificacion'):
                    obj_in_data['fecha_modificacion'] = get_utc_now
                
                db_obj = self.model(**obj_in_data)
                db.add(db_obj)
                created_objects.append(db_obj)
            
            db.commit()
            
            # Refresh todos los objetos
            for obj in created_objects:
                db.refresh(obj)
                
            return created_objects
            
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Error de integridad en creación múltiple: {str(e)}")
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error creando registros múltiples: {str(e)}")

    # =============================================
    # OPERACIONES DE ACTUALIZACIÓN
    # =============================================

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Actualiza un registro existente"""
        try:
            obj_data = jsonable_encoder(db_obj)
            
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)
            
            # Agregar timestamp de modificación si el modelo lo tiene
            if hasattr(self.model, 'fecha_modificacion'):
                update_data['fecha_modificacion'] = get_utc_now
            
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
            
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Error de integridad en actualización: {str(e)}")
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error actualizando registro: {str(e)}")

    def update_by_id(
        self,
        db: Session,
        *,
        id: Any,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> Optional[ModelType]:
        """Actualiza un registro por su ID"""
        db_obj = self.get(db=db, id=id)
        if not db_obj:
            return None
        return self.update(db=db, db_obj=db_obj, obj_in=obj_in)

    # =============================================
    # OPERACIONES DE ELIMINACIÓN
    # =============================================

    def remove(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """Elimina un registro por su ID"""
        try:
            obj = self.get(db=db, id=id)
            if obj:
                db.delete(obj)
                db.commit()
                return obj
            return None
            
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error eliminando registro: {str(e)}")

    def soft_delete(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """Eliminación suave (marca como inactivo si el campo existe)"""
        db_obj = self.get(db=db, id=id)
        if not db_obj:
            return None
        
        if hasattr(db_obj, 'activo'):
            return self.update(db=db, db_obj=db_obj, obj_in={"activo": False})
        else:
            # Si no tiene campo 'activo', hacer eliminación física
            return self.remove(db=db, id=id)

    # =============================================
    # MÉTODOS DE BÚSQUEDA ESPECIALIZADA
    # =============================================

    def search(
        self,
        db: Session,
        *,
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Búsqueda de texto en campos específicos"""
        query = db.query(self.model)
        
        # Crear condiciones de búsqueda
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                field_obj = getattr(self.model, field)
                search_conditions.append(field_obj.ilike(f"%{search_term}%"))
        
        if search_conditions:
            from sqlalchemy import or_
            query = query.filter(or_(*search_conditions))
        
        return query.offset(skip).limit(limit).all()

    def get_active(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Obtiene solo registros activos (si el modelo tiene campo 'activo')"""
        if hasattr(self.model, 'activo'):
            return self.get_multi(db=db, skip=skip, limit=limit, filters={"activo": True})
        else:
            return self.get_multi(db=db, skip=skip, limit=limit)

    # =============================================
    # MÉTODOS AUXILIARES
    # =============================================

    def _get_primary_key(self) -> str:
        """Obtiene el nombre de la columna de clave primaria"""
        primary_key_columns = [key.name for key in self.model.__table__.primary_key]
        if primary_key_columns:
            return primary_key_columns[0]
        raise ValueError(f"No se encontró clave primaria para el modelo {self.model.__name__}")

    def get_model_fields(self) -> List[str]:
        """Obtiene la lista de campos del modelo"""
        return [column.name for column in self.model.__table__.columns]

    # =============================================
    # MÉTODOS DE ESTADÍSTICAS
    # =============================================

    def get_stats(self, db: Session) -> Dict[str, Any]:
        """Obtiene estadísticas básicas del modelo"""
        total = self.count(db)
        stats = {"total": total}
        
        # Si tiene campo 'activo', contar activos/inactivos
        if hasattr(self.model, 'activo'):
            activos = self.count(db, filters={"activo": True})
            inactivos = total - activos
            stats.update({
                "activos": activos,
                "inactivos": inactivos,
                "porcentaje_activos": round((activos / total * 100) if total > 0 else 0, 2)
            })
        
        return stats