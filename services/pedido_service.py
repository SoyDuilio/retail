from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app import models, schemas, crud
from services.pricing_service import PricingService


def generate_numero_pedido(db: Session) -> str:
    """Genera un número de pedido único y secuencial."""
    today = datetime.utcnow().date()
    count_today = crud.pedido.count_by_date(db, date=today)
    return f"PED-{today.strftime('%Y%m%d')}-{count_today + 1:04d}"


def create_new_pedido(
    db: Session, 
    *, 
    pedido_in: schemas.PedidoCreate, 
    vendedor: models.VendedorModel
) -> models.PedidoModel:
    """
    Servicio para orquestar la creación completa de un nuevo pedido.
    Ahora incluye lógica de precios CONTADO/CRÉDITO y plazos.
    """
    
    # Inicializar servicio de precios
    pricing_service = PricingService(db)
    
    # 1. --- VALIDACIONES PREVIAS ---
    cliente = crud.cliente.get(db, id=pedido_in.cliente_id)
    if not cliente or not cliente.activo:
        raise ValueError(f"Cliente con ID {pedido_in.cliente_id} no encontrado o está inactivo.")

    if not vendedor.activo:
        raise ValueError("El usuario vendedor no se encuentra activo.")

    if not cliente.tipo_cliente_id:
        raise ValueError(
            f"El cliente '{cliente.razon_social}' no tiene un tipo de cliente asignado, "
            "no se pueden calcular precios."
        )
    
    # ✅ NUEVO: Validar tipo_pago
    if pedido_in.tipo_pago not in ['CONTADO', 'CREDITO']:
        raise ValueError(f"Tipo de pago inválido: {pedido_in.tipo_pago}. Debe ser CONTADO o CREDITO.")
    
    # ✅ NUEVO: Validar plazo_dias
    plazo_dias = getattr(pedido_in, 'plazo_dias', 0) or 0
    if plazo_dias < 0 or plazo_dias > 60:
        raise ValueError(f"Plazo de días inválido: {plazo_dias}. Debe estar entre 0 y 60.")

    # 2. --- PROCESAMIENTO DE ITEMS Y CÁLCULO DE PRECIOS ---
    items_db_list = []
    subtotal_calculado = Decimal('0.00')
    descuento_total_calculado = Decimal('0.00')
    total_calculado = Decimal('0.00')
    
    # ✅ NUEVO: Descuento total por pago contado
    descuento_contado_total = Decimal('0.00')

    for item_in in pedido_in.items:
        producto = crud.producto.get(db, id=item_in.producto_id)
        if not producto or not producto.activo:
            raise ValueError(
                f"Producto con ID {item_in.producto_id} no encontrado o inactivo."
            )
        
        # --- NUEVA LÓGICA DE PRECIOS CON PRICING SERVICE ---
        tipo_cliente_para_precio_id = (
            getattr(item_in, 'override_tipo_cliente_id', None) or 
            cliente.tipo_cliente_id
        )
        
        # Determinar tipo de pago para cálculo de precio
        tipo_pago_calculo = pedido_in.tipo_pago.lower()  # 'contado' o 'credito'
        
        # Obtener precio usando el servicio
        precio_info = pricing_service.obtener_precio_producto(
            producto_id=producto.id,
            tipo_cliente_id=tipo_cliente_para_precio_id,
            tipo_pago=tipo_pago_calculo,
            cantidad=item_in.cantidad
        )
        
        if not precio_info:
            raise ValueError(
                f"No se encontró un precio definido para el producto '{producto.nombre}' "
                f"y el tipo de cliente/pago seleccionado."
            )
        
        precio_unitario_final = precio_info['precio_final']
        descuento_item = precio_info['descuento_aplicado'] * item_in.cantidad
        
        # Crear instancia del item
        item_db = models.PedidoItemModel(
            producto_id=item_in.producto_id,
            unidad_medida_venta=getattr(item_in, 'unidad_medida_venta', 'unidad'),
            cantidad=item_in.cantidad,
            precio_unitario_venta=precio_unitario_final,
            subtotal=precio_unitario_final * item_in.cantidad
        )
        
        items_db_list.append(item_db)
        
        # Acumular totales
        subtotal_calculado += item_db.subtotal
        descuento_total_calculado += descuento_item
        
        # Si es contado, acumular descuento
        if tipo_pago_calculo == 'contado':
            descuento_contado_total += descuento_item

    # Total final
    total_calculado = subtotal_calculado - descuento_total_calculado

    # 3. --- CREACIÓN DEL PEDIDO PRINCIPAL ---
    now = datetime.now()
    
    pedido_db = models.PedidoModel(
        numero_pedido=generate_numero_pedido(db),
        fecha=now.date(),
        hora=now.time(),
        vendedor_id=vendedor.vendedor_id,
        cliente_id=cliente.id,
        tipo_venta=pedido_in.tipo_venta.value,
        tipo_pago=pedido_in.tipo_pago.value,
        plazo_dias=plazo_dias,  # ✅ NUEVO
        latitud_pedido=pedido_in.latitud_pedido,
        longitud_pedido=pedido_in.longitud_pedido,
        observaciones=pedido_in.observaciones,
        items=items_db_list,
        subtotal=subtotal_calculado,
        descuento_total=descuento_total_calculado,
        descuento_contado_aplicado=descuento_contado_total,  # ✅ NUEVO
        total=total_calculado,
        estado="pendiente_aprobacion"  # Estado inicial
    )

    # 4. --- PERSISTENCIA Y ACCIONES POST-CREACIÓN ---
    db.add(pedido_db)
    db.commit()
    db.refresh(pedido_db)

    # --- Acciones Asíncronas (Idealmente en tareas de fondo) ---
    # crud.auditoria.create(...)
    # notificaciones.enviar_notificacion_nuevo_pedido(db, pedido_id=pedido_db.id)
    # crud.producto.actualizar_stock_batch(...)

    return pedido_db


def calcular_preview_pedido(
    db: Session,
    cliente_id: int,
    tipo_pago: str,
    items: list
) -> dict:
    """
    Calcula un preview del pedido mostrando ambos precios (CONTADO/CRÉDITO)
    para que el vendedor pueda comparar antes de crear el pedido.
    
    Returns:
        {
            'items': [...],
            'total_credito': Decimal,
            'total_contado': Decimal,
            'ahorro_contado': Decimal,
            'porcentaje_ahorro': Decimal
        }
    """
    
    pricing_service = PricingService(db)
    
    # Validar cliente
    cliente = crud.cliente.get(db, id=cliente_id)
    if not cliente or not cliente.activo:
        raise ValueError(f"Cliente inválido")
    
    if not cliente.tipo_cliente_id:
        raise ValueError("Cliente sin tipo asignado")
    
    items_preview = []
    total_credito = Decimal('0.00')
    total_contado = Decimal('0.00')
    
    for item in items:
        producto_id = item.get('producto_id')
        cantidad = item.get('cantidad', 1)
        
        # Obtener ambos precios
        precios = pricing_service.calcular_ambos_precios(
            producto_id=producto_id,
            tipo_cliente_id=cliente.tipo_cliente_id,
            cantidad=cantidad
        )
        
        if not precios:
            continue
        
        items_preview.append({
            'producto_id': producto_id,
            'cantidad': cantidad,
            'precio_credito': precios['precio_credito'],
            'precio_contado': precios['precio_contado'],
            'ahorro': precios['ahorro_contado']
        })
        
        total_credito += precios['precio_credito']['subtotal']
        total_contado += precios['precio_contado']['subtotal']
    
    ahorro = total_credito - total_contado
    porcentaje = (ahorro / total_credito * 100) if total_credito > 0 else Decimal('0.00')
    
    return {
        'items': items_preview,
        'total_credito': total_credito,
        'total_contado': total_contado,
        'ahorro_contado': ahorro,
        'porcentaje_ahorro': round(porcentaje, 2)
    }