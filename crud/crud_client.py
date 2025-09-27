# app/crud/crud_client.py
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.models.client_models import ClienteModel, HistorialCreditoModel, SegmentoClienteModel
from app.schemas.client_schemas import ClienteCreate, ClienteUpdate #, HistorialClienteCreate, SegmentacionClienteCreate
from app.schemas.common_schemas import TipoCliente, Coordenadas
from crud.base import CRUDBase

# =============================================
# CRUD CLIENTES
# =============================================

class CRUDCliente(CRUDBase[ClienteModel, ClienteCreate, ClienteUpdate]):
    
    def get_by_codigo(self, db: Session, *, codigo: str) -> Optional[ClienteModel]:
        """Obtiene cliente por código único"""
        return db.query(ClienteModel).filter(
            ClienteModel.codigo_cliente == codigo,
            ClienteModel.activo == True
        ).first()
    
    def get_by_ruc(self, db: Session, *, ruc: str) -> Optional[ClienteModel]:
        """Obtiene cliente por RUC"""
        return db.query(ClienteModel).filter(
            ClienteModel.ruc == ruc,
            ClienteModel.activo == True
        ).first()
    
    def get_by_tipo(self, db: Session, *, tipo: TipoCliente, skip: int = 0, limit: int = 100) -> List[ClienteModel]:
        """Obtiene clientes por tipo"""
        return db.query(ClienteModel).filter(
            ClienteModel.tipo_cliente == tipo,
            ClienteModel.activo == True
        ).offset(skip).limit(limit).all()
    
    def search_by_name(self, db: Session, *, nombre: str, skip: int = 0, limit: int = 100) -> List[ClienteModel]:
        """Busca clientes por nombre o razón social"""
        return db.query(ClienteModel).filter(
            (ClienteModel.nombre_comercial.ilike(f"%{nombre}%")) |
            (ClienteModel.razon_social.ilike(f"%{nombre}%")),
            ClienteModel.activo == True
        ).offset(skip).limit(limit).all()
    
    def get_by_ubicacion(
        self, 
        db: Session, 
        *, 
        distrito: Optional[str] = None,
        provincia: Optional[str] = None,
        departamento: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[ClienteModel]:
        """Obtiene clientes por ubicación geográfica"""
        query = db.query(ClienteModel).filter(ClienteModel.activo == True)
        
        if distrito:
            query = query.filter(ClienteModel.distrito.ilike(f"%{distrito}%"))
        if provincia:
            query = query.filter(ClienteModel.provincia.ilike(f"%{provincia}%"))
        if departamento:
            query = query.filter(ClienteModel.departamento.ilike(f"%{departamento}%"))
        
        return query.offset(skip).limit(limit).all()
    
    def get_clientes_cerca(
        self,
        db: Session,
        *,
        latitud: float,
        longitud: float,
        radio_km: float = 5.0,
        limit: int = 20
    ) -> List[ClienteModel]:
        """Obtiene clientes cercanos a una coordenada (usando fórmula de Haversine aproximada)"""
        from sqlalchemy import func, and_
        
        # Aproximación simple para distancia (no exacta pero funcional)
        # Para precisión mayor se requeriría PostGIS
        lat_diff = 0.009 * radio_km  # Aproximadamente 1 km = 0.009 grados
        lon_diff = 0.009 * radio_km
        
        return db.query(ClienteModel).filter(
            and_(
                ClienteModel.activo == True,
                ClienteModel.latitud.between(latitud - lat_diff, latitud + lat_diff),
                ClienteModel.longitud.between(longitud - lon_diff, longitud + lon_diff),
                ClienteModel.latitud.isnot(None),
                ClienteModel.longitud.isnot(None)
            )
        ).limit(limit).all()
    
    def get_with_historial(self, db: Session, *, cliente_id: int) -> Optional[ClienteModel]:
        """Obtiene cliente con su historial completo"""
        from sqlalchemy.orm import joinedload
        
        return db.query(ClienteModel).options(
            joinedload(ClienteModel.historial)
        ).filter(
            ClienteModel.cliente_id == cliente_id,
            ClienteModel.activo == True
        ).first()
    
    def get_top_clientes(
        self, 
        db: Session, 
        *, 
        limite: int = 10,
        por_volumen: bool = True
    ) -> List[Dict[str, Any]]:
        """Obtiene los mejores clientes por volumen de compras o frecuencia"""
        from sqlalchemy import func, desc
        from app.models.order_models import PedidoModel, ItemPedidoModel
        
        if por_volumen:
            # Top por volumen de ventas
            query = db.query(
                ClienteModel.cliente_id,
                ClienteModel.nombre_comercial,
                func.sum(ItemPedidoModel.subtotal).label('total_compras'),
                func.count(PedidoModel.pedido_id).label('total_pedidos')
            ).join(
                PedidoModel, ClienteModel.cliente_id == PedidoModel.cliente_id
            ).join(
                ItemPedidoModel, PedidoModel.pedido_id == ItemPedidoModel.pedido_id
            ).filter(
                ClienteModel.activo == True,
                PedidoModel.estado != 'cancelado'
            ).group_by(
                ClienteModel.cliente_id,
                ClienteModel.nombre_comercial
            ).order_by(
                desc('total_compras')
            ).limit(limite)
        else:
            # Top por frecuencia de pedidos
            query = db.query(
                ClienteModel.cliente_id,
                ClienteModel.nombre_comercial,
                func.count(PedidoModel.pedido_id).label('total_pedidos'),
                func.sum(ItemPedidoModel.subtotal).label('total_compras')
            ).join(
                PedidoModel, ClienteModel.cliente_id == PedidoModel.cliente_id
            ).join(
                ItemPedidoModel, PedidoModel.pedido_id == ItemPedidoModel.pedido_id
            ).filter(
                ClienteModel.activo == True,
                PedidoModel.estado != 'cancelado'
            ).group_by(
                ClienteModel.cliente_id,
                ClienteModel.nombre_comercial
            ).order_by(
                desc('total_pedidos')
            ).limit(limite)
        
        results = query.all()
        return [
            {
                "cliente_id": r.cliente_id,
                "nombre_comercial": r.nombre_comercial,
                "total_compras": float(r.total_compras or 0),
                "total_pedidos": r.total_pedidos
            }
            for r in results
        ]
    
    def actualizar_coordenadas(
        self,
        db: Session,
        *,
        cliente_id: int,
        coordenadas: Coordenadas
    ) -> Optional[ClienteModel]:
        """Actualiza las coordenadas GPS de un cliente"""
        cliente = self.get(db=db, id=cliente_id)
        if not cliente:
            return None
        
        update_data = {
            "latitud": coordenadas.latitud,
            "longitud": coordenadas.longitud,
            "precision_gps": coordenadas.precision,
            "fecha_modificacion": datetime.utcnow()
        }
        
        return self.update(db=db, db_obj=cliente, obj_in=update_data)

# =============================================
# CRUD HISTORIAL CLIENTE
# =============================================

#class CRUDHistorialCliente(CRUDBase[HistorialCreditoModel, HistorialClienteCreate, dict]):
class CRUDHistorialCliente(CRUDBase[HistorialCreditoModel, dict, dict]):
    
    def create_evento(
        self,
        db: Session,
        *,
        cliente_id: int,
        tipo_evento: str,
        descripcion: str,
        vendedor_id: Optional[int] = None,
        datos_adicionales: Optional[Dict[str, Any]] = None
    ) -> HistorialCreditoModel:
        """Crea un nuevo evento en el historial del cliente"""
        
        evento_data = {
            "cliente_id": cliente_id,
            "tipo_evento": tipo_evento,
            "descripcion": descripcion,
            "vendedor_id": vendedor_id,
            "datos_adicionales": datos_adicionales or {},
            "fecha_evento": datetime.utcnow()
        }
        
        historial = HistorialCreditoModel(**evento_data)
        db.add(historial)
        db.commit()
        db.refresh(historial)
        
        return historial
    
    def get_historial_cliente(
        self,
        db: Session,
        *,
        cliente_id: int,
        tipo_evento: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[HistorialCreditoModel]:
        """Obtiene el historial de un cliente"""
        query = db.query(HistorialCreditoModel).filter(
            HistorialCreditoModel.cliente_id == cliente_id
        )
        
        if tipo_evento:
            query = query.filter(HistorialCreditoModel.tipo_evento == tipo_evento)
        
        return query.order_by(
            HistorialCreditoModel.fecha_evento.desc()
        ).offset(skip).limit(limit).all()
    
    def get_eventos_por_vendedor(
        self,
        db: Session,
        *,
        vendedor_id: int,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[HistorialCreditoModel]:
        """Obtiene eventos de un vendedor en un período"""
        query = db.query(HistorialCreditoModel).filter(
            HistorialCreditoModel.vendedor_id == vendedor_id
        )
        
        if fecha_desde:
            query = query.filter(HistorialCreditoModel.fecha_evento >= fecha_desde)
        if fecha_hasta:
            query = query.filter(HistorialCreditoModel.fecha_evento <= fecha_hasta)
        
        return query.order_by(
            HistorialCreditoModel.fecha_evento.desc()
        ).offset(skip).limit(limit).all()

# =============================================
# CRUD SEGMENTACIÓN CLIENTE
# =============================================

#class CRUDSegmentacionCliente(CRUDBase[SegmentoClienteModel, SegmentacionClienteCreate, dict]):
class CRUDSegmentacionCliente(CRUDBase[SegmentoClienteModel, dict, dict]):
    
    def get_by_cliente(self, db: Session, *, cliente_id: int) -> Optional[SegmentoClienteModel]:
        """Obtiene la segmentación actual de un cliente"""
        return db.query(SegmentoClienteModel).filter(
            SegmentoClienteModel.cliente_id == cliente_id
        ).order_by(SegmentoClienteModel.fecha_segmentacion.desc()).first()
    
    def actualizar_segmentacion(
        self,
        db: Session,
        *,
        cliente_id: int,
        segmento: str,
        score_crediticio: Optional[float] = None,
        valor_promedio_pedido: Optional[float] = None,
        frecuencia_compra: Optional[int] = None,
        metadatos: Optional[Dict[str, Any]] = None
    ) -> SegmentoClienteModel:
        """Actualiza o crea la segmentación de un cliente"""
        
        # Verificar si ya existe segmentación
        segmentacion_existente = self.get_by_cliente(db=db, cliente_id=cliente_id)
        
        if segmentacion_existente:
            # Actualizar existente
            update_data = {
                "segmento": segmento,
                "fecha_segmentacion": datetime.utcnow()
            }
            
            if score_crediticio is not None:
                update_data["score_crediticio"] = score_crediticio
            if valor_promedio_pedido is not None:
                update_data["valor_promedio_pedido"] = valor_promedio_pedido
            if frecuencia_compra is not None:
                update_data["frecuencia_compra"] = frecuencia_compra
            if metadatos is not None:
                update_data["metadatos_segmentacion"] = metadatos
            
            return self.update(db=db, db_obj=segmentacion_existente, obj_in=update_data)
        else:
            # Crear nueva segmentación
            nueva_segmentacion = SegmentoClienteModel(
                cliente_id=cliente_id,
                segmento=segmento,
                score_crediticio=score_crediticio,
                valor_promedio_pedido=valor_promedio_pedido,
                frecuencia_compra=frecuencia_compra,
                metadatos_segmentacion=metadatos or {},
                fecha_segmentacion=datetime.utcnow()
            )
            
            db.add(nueva_segmentacion)
            db.commit()
            db.refresh(nueva_segmentacion)
            
            return nueva_segmentacion
    
    def get_clientes_por_segmento(
        self,
        db: Session,
        *,
        segmento: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Obtiene clientes de un segmento específico"""
        from sqlalchemy.orm import joinedload
        
        query = db.query(SegmentoClienteModel).options(
            joinedload(SegmentoClienteModel.cliente)
        ).filter(
            SegmentoClienteModel.segmento == segmento
        ).order_by(
            SegmentoClienteModel.fecha_segmentacion.desc()
        ).offset(skip).limit(limit)
        
        results = query.all()
        
        return [
            {
                "cliente_id": seg.cliente_id,
                "nombre_comercial": seg.cliente.nombre_comercial if seg.cliente else "N/A",
                "segmento": seg.segmento,
                "score_crediticio": seg.score_crediticio,
                "valor_promedio_pedido": seg.valor_promedio_pedido,
                "frecuencia_compra": seg.frecuencia_compra,
                "fecha_segmentacion": seg.fecha_segmentacion
            }
            for seg in results
        ]
    
    def calcular_segmentacion_automatica(
        self,
        db: Session,
        *,
        cliente_id: int
    ) -> Optional[SegmentoClienteModel]:
        """Calcula automáticamente la segmentación basada en historial de compras"""
        from sqlalchemy import func
        from app.models.order_models import PedidoModel, ItemPedidoModel
        
        # Obtener estadísticas del cliente
        stats = db.query(
            func.count(PedidoModel.pedido_id).label('total_pedidos'),
            func.avg(PedidoModel.total).label('promedio_pedido'),
            func.sum(PedidoModel.total).label('total_gastado'),
            func.max(PedidoModel.fecha_pedido).label('ultima_compra')
        ).filter(
            PedidoModel.cliente_id == cliente_id,
            PedidoModel.estado.in_(['entregado', 'confirmado'])
        ).first()
        
        if not stats or stats.total_pedidos == 0:
            return None
        
        # Lógica de segmentación simple
        total_pedidos = stats.total_pedidos
        promedio_pedido = float(stats.promedio_pedido or 0)
        total_gastado = float(stats.total_gastado or 0)
        
        # Calcular frecuencia (pedidos por mes)
        dias_desde_primera_compra = (datetime.utcnow() - stats.ultima_compra).days
        meses_activo = max(1, dias_desde_primera_compra / 30)
        frecuencia_mensual = total_pedidos / meses_activo
        
        # Determinar segmento
        if total_gastado >= 5000 and promedio_pedido >= 200:
            segmento = "VIP"
            score = 90
        elif total_gastado >= 2000 and frecuencia_mensual >= 2:
            segmento = "Premium"
            score = 75
        elif total_pedidos >= 5 and frecuencia_mensual >= 1:
            segmento = "Regular"
            score = 60
        elif total_pedidos >= 2:
            segmento = "Ocasional"
            score = 40
        else:
            segmento = "Nuevo"
            score = 25
        
        # Crear/actualizar segmentación
        return self.actualizar_segmentacion(
            db=db,
            cliente_id=cliente_id,
            segmento=segmento,
            score_crediticio=score,
            valor_promedio_pedido=promedio_pedido,
            frecuencia_compra=int(frecuencia_mensual * 30),  # días entre compras
            metadatos={
                "total_pedidos": total_pedidos,
                "total_gastado": total_gastado,
                "calculo_automatico": True,
                "fecha_calculo": datetime.utcnow().isoformat()
            }
        )

# =============================================
# INSTANCIAS DE CRUD
# =============================================

crud_cliente = CRUDCliente(ClienteModel)
crud_historial_cliente = CRUDHistorialCliente(HistorialCreditoModel)
crud_segmentacion_cliente = CRUDSegmentacionCliente(SegmentoClienteModel)