# en services/pedido_service.py

from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from app import models, schemas, crud

def generate_numero_pedido(db: Session) -> str:
    """Genera un número de pedido único y secuencial para el día."""
    today = datetime.utcnow().date()
    # Esta es una implementación simple, se puede mejorar para evitar concurrencia
    count_today = crud.pedido.count_by_date(db, date=today)
    return f"PED-{today.strftime('%Y%m%d')}-{count_today + 1:04d}"


def create_new_pedido(
    db: Session, *, pedido_in: schemas.PedidoCreate, vendedor: models.VendedorModel
) -> models.PedidoModel:
    """
    Servicio para orquestar la creación completa de un nuevo pedido.
    """
    # 1. --- VALIDACIONES PREVIAS ---
    cliente = crud.cliente.get(db, id=pedido_in.cliente_id)
    if not cliente or not cliente.activo:
        raise ValueError(f"Cliente con ID {pedido_in.cliente_id} no encontrado o está inactivo.")

    if not vendedor.activo:
        raise ValueError("El usuario vendedor no se encuentra activo.")

    if not cliente.tipo_cliente_id:
        raise ValueError(f"El cliente '{cliente.razon_social}' no tiene un tipo de cliente asignado, no se pueden calcular precios.")

    # 2. --- PROCESAMIENTO DE ITEMS Y CÁLCULO DE PRECIOS ---
    items_db_list = []
    subtotal_calculado = Decimal(0)
    descuento_total_calculado = Decimal(0)
    total_calculado = Decimal(0)

    for item_in in pedido_in.items:
        producto = crud.producto.get(db, id=item_in.producto_id)
        if not producto or not producto.activo:
            raise ValueError(f"Producto con ID {item_in.producto_id} no encontrado o inactivo.")
        
        # Lógica de Stock (configurable)
        # if not configuracion.permite_pedido_sin_stock and producto.stock_actual < item_in.cantidad:
        #     raise ValueError(f"Stock insuficiente para '{producto.nombre}'. Disponible: {producto.stock_actual}")

        # --- LÓGICA DE PRECIOS (EL CORAZÓN) ---
        tipo_cliente_para_precio_id = item_in.override_tipo_cliente_id or cliente.tipo_cliente_id
        
        precio_info = crud.precio.get_for_product_and_client_type(
            db, producto_id=producto.id, tipo_cliente_id=tipo_cliente_para_precio_id
        )

        if not precio_info:
            raise ValueError(f"No se encontró un precio definido para el producto '{producto.nombre}' y el tipo de cliente seleccionado.")
        
        # Aquí iría tu lógica de descuentos por volumen si lo deseas, usando precio_info
        precio_unitario_final = precio_info.precio
        
        # Crear la instancia del item y calcular sus totales
        item_db = models.PedidoItemModel(
            producto_id=item_in.producto_id,
            cantidad=item_in.cantidad,
            precio_unitario=precio_unitario_final,
            # Tu modelo PedidoItemModel tiene un método para esto. ¡Usémoslo!
        )
        item_db.calcular_totales() # Asume que este método calcula subtotal y total del item.

        items_db_list.append(item_db)
        total_calculado += item_db.total
        subtotal_calculado += item_db.subtotal
        descuento_total_calculado += item_db.descuento_monto

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
        latitud_pedido=pedido_in.latitud_pedido,
        longitud_pedido=pedido_in.longitud_pedido,
        observaciones=pedido_in.observaciones,
        items=items_db_list, # SQLAlchemy asigna los items al pedido
        subtotal=subtotal_calculado,
        descuento_total=descuento_total_calculado,
        total=total_calculado
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