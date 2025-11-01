"""
Servicio para cálculo de precios según tipo de cliente y condición de pago
"""

from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional
from datetime import date

# ✅ Imports corregidos
from app.models.pricing_models_db import ConfiguracionDescuento
from app.models.product_models import PrecioClienteModel

class PricingService:
    """Servicio para gestión de precios"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def obtener_precio_producto(
        self,
        producto_id: int,
        tipo_cliente_id: int,
        tipo_pago: str = "credito",
        cantidad: int = 1
    ) -> Optional[dict]:
        """
        Obtiene el precio final de un producto según tipo de cliente y condición de pago
        """
        
        # 1. Intentar obtener precio explícito
        precio_explicito = self.db.query(PrecioClienteModel).filter(  # ✅ Cambio aquí
            PrecioClienteModel.producto_id == producto_id,
            PrecioClienteModel.tipo_cliente_id == tipo_cliente_id,
            PrecioClienteModel.tipo_pago == tipo_pago,
            PrecioClienteModel.activo == True
        ).first()
        
        if precio_explicito:
            precio_final = Decimal(str(precio_explicito.precio))
            return {
                'precio_base': precio_final,
                'precio_final': precio_final,
                'descuento_aplicado': Decimal('0.00'),
                'tipo_descuento': None,
                'valor_descuento': None,
                'subtotal': round(precio_final * cantidad, 2),
                'es_precio_explicito': True
            }
        
        # 2. Buscar precio base (crédito)
        precio_base_obj = self.db.query(PrecioClienteModel).filter(  # ✅ Cambio aquí
            PrecioClienteModel.producto_id == producto_id,
            PrecioClienteModel.tipo_cliente_id == tipo_cliente_id,
            PrecioClienteModel.tipo_pago == 'credito',
            PrecioClienteModel.activo == True
        ).first()
        
        if not precio_base_obj:
            return None
        
        precio_base = Decimal(str(precio_base_obj.precio))
        
        # 3. Si es crédito, retornar precio base
        if tipo_pago == 'credito':
            return {
                'precio_base': precio_base,
                'precio_final': precio_base,
                'descuento_aplicado': Decimal('0.00'),
                'tipo_descuento': None,
                'valor_descuento': None,
                'subtotal': round(precio_final * cantidad, 2),
                'es_precio_explicito': False
            }
        
        # 4. Si es contado, aplicar descuento de configuración
        config = self.db.query(ConfiguracionDescuento).filter(
            ConfiguracionDescuento.tipo_pago == 'contado',
            ConfiguracionDescuento.activo == True
        ).order_by(ConfiguracionDescuento.id.desc()).first()
        
        if not config:
            return {
                'precio_base': precio_base,
                'precio_final': precio_base,
                'descuento_aplicado': Decimal('0.00'),
                'tipo_descuento': None,
                'valor_descuento': None,
                'subtotal': round(precio_final * cantidad, 2),
                'es_precio_explicito': False
            }
        
        # Verificar vigencia
        hoy = date.today()
        if config.fecha_inicio and hoy < config.fecha_inicio:
            return {
                'precio_base': precio_base,
                'precio_final': precio_base,
                'descuento_aplicado': Decimal('0.00'),
                'tipo_descuento': None,
                'valor_descuento': None,
                'subtotal': round(precio_final * cantidad, 2),
                'es_precio_explicito': False
            }
        
        if config.fecha_fin and hoy > config.fecha_fin:
            return {
                'precio_base': precio_base,
                'precio_final': precio_base,
                'descuento_aplicado': Decimal('0.00'),
                'tipo_descuento': None,
                'valor_descuento': None,
                'subtotal': round(precio_final * cantidad, 2),
                'es_precio_explicito': False
            }
        
        # Calcular descuento
        descuento_monto = Decimal('0.00')
        
        if config.tipo_descuento == 'porcentaje':
            descuento_monto = precio_base * (Decimal(str(config.valor_descuento)) / Decimal('100'))
        else:
            descuento_monto = Decimal(str(config.valor_descuento))
        
        precio_final = precio_base - descuento_monto
        
        if precio_final < 0:
            precio_final = Decimal('0.00')
        
        return {
            'precio_base': precio_base,
            'precio_final': precio_final,
            'descuento_aplicado': descuento_monto,
            'tipo_descuento': config.tipo_descuento,
            'valor_descuento': Decimal(str(config.valor_descuento)),
            'subtotal': round(precio_final * cantidad, 2),
            'es_precio_explicito': False
        }
    
    def calcular_ambos_precios(
        self,
        producto_id: int,
        tipo_cliente_id: int,
        cantidad: int = 1
    ) -> Optional[dict]:
        """Calcula tanto precio CONTADO como CRÉDITO"""
        
        precio_credito = self.obtener_precio_producto(
            producto_id, tipo_cliente_id, 'credito', cantidad
        )
        
        precio_contado = self.obtener_precio_producto(
            producto_id, tipo_cliente_id, 'contado', cantidad
        )
        
        if not precio_credito or not precio_contado:
            return None
        
        ahorro = precio_credito['subtotal'] - precio_contado['subtotal']
        
        porcentaje_ahorro = Decimal('0.00')
        if precio_credito['subtotal'] > 0:
            porcentaje_ahorro = (ahorro / precio_credito['subtotal']) * Decimal('100')
        
        return {
            'precio_credito': precio_credito,
            'precio_contado': precio_contado,
            'ahorro_contado': ahorro,
            'porcentaje_ahorro': round(porcentaje_ahorro, 2)
        }