# app/models/product_models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from .base import Base

# Función auxiliar para obtener la hora actual en UTC
def get_utc_now():
    return datetime.now(timezone.utc)

# =============================================
# TIPOS DE CLIENTE
# =============================================


# =============================================
# CATEGORÍAS DE PRODUCTOS
# =============================================

class CategoriaModel(Base):
    __tablename__ = "categorias"
    
    categoria_id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    activa = Column(Boolean, default=True, index=True)
    fecha_creacion = Column(DateTime, default=get_utc_now)
    
    # Relaciones
    productos = relationship("ProductoModel", back_populates="categoria")
    
    @property
    def total_productos(self):
        return len([p for p in self.productos if p.activo])
    
    def __repr__(self):
        return f"<Categoria {self.nombre}>"

# =============================================
# UNIDADES DE MEDIDA
# =============================================

class UnidadMedidaModel(Base):
    __tablename__ = "unidades_medida"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(20), unique=True, nullable=False)
    abreviatura = Column(String(5), nullable=False)
    activo = Column(Boolean, default=True)
    
    # Relaciones
    #productos = relationship("ProductoModel", back_populates="unidad_medida")
    
    def __repr__(self):
        return f"<UnidadMedida {self.nombre} ({self.abreviatura})>"

# =============================================
# PRODUCTOS PRINCIPALES
# =============================================

class ProductoModel(Base):
    __tablename__ = "productos"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo_producto = Column(String(20), unique=True, nullable=False, index=True)
    nombre = Column(String(200), nullable=False, index=True)
    descripcion = Column(Text)
    categoria_id = Column(Integer, ForeignKey("categorias.categoria_id"), index=True)
    #unidad_medida = Column(String(50))
    precio_unitario = Column(DECIMAL(10, 2), nullable=False, default=0)
    precio_mayorista = Column(DECIMAL(10, 2))
    precio_distribuidor = Column(DECIMAL(10, 2))
    #stock_actual = Column(Integer, default=0, index=True)
    #stock_minimo = Column(Integer, default=0)
    activo = Column(Boolean, default=True, index=True)
    #created_at = Column(DateTime, default=get_utc_now)
    #updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relaciones
    categoria = relationship("CategoriaModel", back_populates="productos")
    #unidad_medida = relationship("UnidadMedidaModel", back_populates="productos")
    precios = relationship("PrecioClienteModel", back_populates="producto", cascade="all, delete-orphan")
    items_pedido = relationship("PedidoItemModel", back_populates="producto")
    movimientos_stock = relationship("MovimientoStockModel", back_populates="producto")
    
    @property
    def estado_stock(self):
        """Calcular estado del stock"""
        if self.stock_actual <= 0:
            return "SIN_STOCK"
        elif self.stock_actual <= self.stock_minimo:
            return "STOCK_BAJO"
        elif self.stock_actual <= self.stock_minimo * 1.5:
            return "STOCK_MEDIO"
        else:
            return "STOCK_ALTO"
    
    @property
    def stock_disponible(self):
        """¿Tiene stock disponible?"""
        return self.stock_actual > 0
    
    def get_precio_para_cliente(self, tipo_cliente_id: int):
        """Obtener precio específico para un tipo de cliente"""
        precio = next((p for p in self.precios if p.tipo_cliente_id == tipo_cliente_id and p.activo), None)
        return precio.precio if precio else self.precio_base
    
    def calcular_descuento_volumen(self, tipo_cliente_id: int, cantidad: int):
        """Calcular descuento por volumen"""
        precio_cliente = next((p for p in self.precios if p.tipo_cliente_id == tipo_cliente_id and p.activo), None)
        
        if not precio_cliente:
            return 0, 0  # descuento, nivel
        
        # Evaluar descuentos de mayor a menor
        if cantidad >= precio_cliente.cantidad_minima_3:
            return precio_cliente.descuento_volumen_3 or 0, 3
        elif cantidad >= precio_cliente.cantidad_minima_2:
            return precio_cliente.descuento_volumen_2 or 0, 2
        elif cantidad >= precio_cliente.cantidad_minima_1:
            return precio_cliente.descuento_volumen_1 or 0, 1
        
        return 0, 0
    
    def __repr__(self):
        return f"<Producto {self.codigo} - {self.nombre}>"

# =============================================
# PRECIOS POR TIPO DE CLIENTE
# =============================================

class PrecioClienteModel(Base):
    __tablename__ = "precios_cliente"
    
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    tipo_cliente_id = Column(Integer, ForeignKey("tipos_cliente.id"), nullable=False)
    precio = Column(DECIMAL(10, 2), nullable=False)
    descuento_volumen_1 = Column(DECIMAL(5, 2), default=0)
    cantidad_minima_1 = Column(Integer, default=10)
    descuento_volumen_2 = Column(DECIMAL(5, 2), default=0)
    cantidad_minima_2 = Column(Integer, default=50)
    descuento_volumen_3 = Column(DECIMAL(5, 2), default=0)
    cantidad_minima_3 = Column(Integer, default=100)
    activo = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=get_utc_now)
    
    # Constraint para evitar duplicados
    __table_args__ = (UniqueConstraint('producto_id', 'tipo_cliente_id', name='_producto_tipo_cliente_uc'),)
    
    # Relaciones
    producto = relationship("ProductoModel", back_populates="precios")
    tipo_cliente = relationship("app.models.client_models.TipoClienteModel", back_populates="precios")
    
    def calcular_precio_final(self, cantidad: int):
        """Calcular precio final con descuento por volumen"""
        descuento_pct = 0
        nivel_descuento = 0
        
        # Determinar descuento aplicable
        if cantidad >= self.cantidad_minima_3 and self.descuento_volumen_3:
            descuento_pct = float(self.descuento_volumen_3)
            nivel_descuento = 3
        elif cantidad >= self.cantidad_minima_2 and self.descuento_volumen_2:
            descuento_pct = float(self.descuento_volumen_2)
            nivel_descuento = 2
        elif cantidad >= self.cantidad_minima_1 and self.descuento_volumen_1:
            descuento_pct = float(self.descuento_volumen_1)
            nivel_descuento = 1
        
        precio_base = float(self.precio)
        descuento_unitario = precio_base * (descuento_pct / 100)
        precio_final_unitario = precio_base - descuento_unitario
        
        subtotal = precio_base * cantidad
        descuento_total = descuento_unitario * cantidad
        total = precio_final_unitario * cantidad
        
        return {
            "precio_unitario": precio_base,
            "descuento_aplicado": descuento_pct,
            "precio_final_unitario": precio_final_unitario,
            "subtotal": subtotal,
            "descuento_total": descuento_total,
            "total": total,
            "descuento_por_volumen": descuento_pct > 0,
            "nivel_descuento": nivel_descuento,
            "ahorro": descuento_total
        }
    
    def __repr__(self):
        return f"<PrecioCliente {self.producto.codigo if self.producto else 'N/A'} - {self.tipo_cliente.nombre if self.tipo_cliente else 'N/A'}: ${self.precio}>"

# =============================================
# MOVIMIENTOS DE STOCK
# =============================================

class MovimientoStockModel(Base):
    __tablename__ = "movimientos_stock"
    
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False, index=True)
    tipo_movimiento = Column(String(20), nullable=False, index=True)  # entrada, salida, ajuste, venta
    cantidad = Column(Integer, nullable=False)
    stock_anterior = Column(Integer, nullable=False)
    stock_nuevo = Column(Integer, nullable=False)
    motivo = Column(String(200), nullable=False)
    referencia_id = Column(String(100))  # ID del pedido, ajuste, etc.
    usuario_id = Column(Integer, nullable=False)
    usuario_tipo = Column(String(20), nullable=False)  # vendedor, supervisor, sistema
    created_at = Column(DateTime, default=get_utc_now, index=True)
    
    # Relaciones
    producto = relationship("ProductoModel", back_populates="movimientos_stock")
    
    def __repr__(self):
        return f"<MovimientoStock {self.tipo_movimiento}: {self.cantidad} - {self.producto.codigo if self.producto else 'N/A'}>"

# =============================================
# ALERTAS DE STOCK
# =============================================

class AlertaStockModel(Base):
    __tablename__ = "alertas_stock"
    
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False, index=True)
    tipo_alerta = Column(String(20), nullable=False)  # stock_bajo, sin_stock, stock_negativo
    stock_actual = Column(Integer, nullable=False)
    stock_minimo = Column(Integer, nullable=False)
    prioridad = Column(String(10), default="media", index=True)  # alta, media, baja
    activa = Column(Boolean, default=True, index=True)
    fecha_resolucion = Column(DateTime)
    resuelto_por = Column(Integer)
    created_at = Column(DateTime, default=get_utc_now, index=True)
    
    # Relaciones
    producto = relationship("ProductoModel")
    
    @property
    def dias_activa(self):
        """Días que lleva activa la alerta"""
        if self.fecha_resolucion:
            return (self.fecha_resolucion - self.created_at).days
        return (get_utc_now() - self.created_at).days
    
    def resolver(self, usuario_id: int):
        """Marcar alerta como resuelta"""
        self.activa = False
        self.fecha_resolucion = get_utc_now()
        self.resuelto_por = usuario_id
    
    def __repr__(self):
        return f"<AlertaStock {self.tipo_alerta} - {self.producto.codigo if self.producto else 'N/A'}>"

# =============================================
# FUNCIONES DE UTILIDAD
# =============================================

def crear_precio_cliente(db, producto_id: int, tipo_cliente_id: int, precio_base: float, margen_pct: float = 0):
    """Crear precio para tipo de cliente con margen"""
    precio_final = precio_base * (1 + margen_pct / 100)
    
    precio_cliente = PrecioClienteModel(
        producto_id=producto_id,
        tipo_cliente_id=tipo_cliente_id,
        precio=precio_final,
        # Descuentos por volumen estándar
        descuento_volumen_1=2.0,
        cantidad_minima_1=10,
        descuento_volumen_2=5.0,
        cantidad_minima_2=50,
        descuento_volumen_3=8.0,
        cantidad_minima_3=100
    )
    
    db.add(precio_cliente)
    return precio_cliente

def actualizar_stock(db, producto_id: int, nueva_cantidad: int, motivo: str, usuario_id: int, usuario_tipo: str = "sistema"):
    """Actualizar stock de producto con movimiento registrado"""
    producto = db.query(ProductoModel).filter(ProductoModel.id == producto_id).first()
    if not producto:
        raise ValueError("Producto no encontrado")
    
    stock_anterior = producto.stock_actual
    producto.stock_actual = nueva_cantidad
    
    # Registrar movimiento
    tipo_mov = "ajuste" if nueva_cantidad != stock_anterior else "consulta"
    cantidad_mov = nueva_cantidad - stock_anterior
    
    movimiento = MovimientoStockModel(
        producto_id=producto_id,
        tipo_movimiento=tipo_mov,
        cantidad=abs(cantidad_mov),
        stock_anterior=stock_anterior,
        stock_nuevo=nueva_cantidad,
        motivo=motivo,
        usuario_id=usuario_id,
        usuario_tipo=usuario_tipo
    )
    
    db.add(movimiento)
    
    # Verificar si necesita alerta
    verificar_alertas_stock(db, producto)
    
    return producto

def verificar_alertas_stock(db, producto: ProductoModel):
    """Verificar y crear alertas de stock si es necesario"""
    # Cerrar alertas previas si el stock se normalizó
    if producto.stock_actual > producto.stock_minimo:
        alertas_activas = db.query(AlertaStockModel).filter(
            AlertaStockModel.producto_id == producto.id,
            AlertaStockModel.activa == True
        ).all()
        
        for alerta in alertas_activas:
            alerta.resolver(usuario_id=0)  # Sistema
        
        return
    
    # Crear nueva alerta si no existe una activa
    alerta_existente = db.query(AlertaStockModel).filter(
        AlertaStockModel.producto_id == producto.id,
        AlertaStockModel.activa == True
    ).first()
    
    if alerta_existente:
        return  # Ya existe alerta activa
    
    # Determinar tipo y prioridad de alerta
    if producto.stock_actual <= 0:
        tipo_alerta = "sin_stock"
        prioridad = "alta"
    elif producto.stock_actual <= producto.stock_minimo:
        tipo_alerta = "stock_bajo"
        prioridad = "media" if producto.stock_actual >= producto.stock_minimo * 0.5 else "alta"
    else:
        return  # No necesita alerta
    
    nueva_alerta = AlertaStockModel(
        producto_id=producto.id,
        tipo_alerta=tipo_alerta,
        stock_actual=producto.stock_actual,
        stock_minimo=producto.stock_minimo,
        prioridad=prioridad
    )
    
    db.add(nueva_alerta)

def obtener_productos_con_precios(db, tipo_cliente_id: int, categoria_id: int = None, activos_solo: bool = True):
    """Obtener productos con sus precios para un tipo de cliente específico"""
    query = db.query(
        ProductoModel.id,
        ProductoModel.codigo,
        ProductoModel.nombre,
        ProductoModel.descripcion,
        CategoriaModel.nombre.label('categoria'),
        UnidadMedidaModel.nombre.label('unidad_medida'),
        UnidadMedidaModel.abreviatura.label('unidad_abrev'),
        PrecioClienteModel.precio,
        PrecioClienteModel.descuento_volumen_1,
        PrecioClienteModel.cantidad_minima_1,
        PrecioClienteModel.descuento_volumen_2,
        PrecioClienteModel.cantidad_minima_2,
        PrecioClienteModel.descuento_volumen_3,
        PrecioClienteModel.cantidad_minima_3,
        ProductoModel.stock_actual,
        ProductoModel.stock_minimo
    ).join(
        CategoriaModel, ProductoModel.categoria_id == CategoriaModel.id
    ).join(
        UnidadMedidaModel, ProductoModel.unidad_medida_id == UnidadMedidaModel.id
    ).join(
        PrecioClienteModel, ProductoModel.id == PrecioClienteModel.producto_id
    ).filter(
        PrecioClienteModel.tipo_cliente_id == tipo_cliente_id,
        PrecioClienteModel.activo == True
    )
    
    if activos_solo:
        query = query.filter(ProductoModel.activo == True)
    
    if categoria_id:
        query = query.filter(ProductoModel.categoria_id == categoria_id)
    
    return query.all()

def generar_reporte_inventario(db):
    """Generar reporte completo de inventario"""
    from sqlalchemy import func
    
    # Estadísticas generales
    total_productos = db.query(ProductoModel).filter(ProductoModel.activo == True).count()
    productos_stock_bajo = db.query(ProductoModel).filter(
        ProductoModel.activo == True,
        ProductoModel.stock_actual <= ProductoModel.stock_minimo
    ).count()
    
    productos_sin_stock = db.query(ProductoModel).filter(
        ProductoModel.activo == True,
        ProductoModel.stock_actual <= 0
    ).count()
    
    # Valor del inventario
    valor_inventario = db.query(
        func.sum(ProductoModel.precio_base * ProductoModel.stock_actual)
    ).filter(ProductoModel.activo == True).scalar() or 0
    
    # Productos más vendidos (necesitaría tabla de ventas)
    # Por ahora retornamos estructura básica
    
    return {
        "total_productos": total_productos,
        "productos_stock_bajo": productos_stock_bajo,
        "productos_sin_stock": productos_sin_stock,
        "valor_inventario": float(valor_inventario),
        "fecha_reporte": get_utc_now()
    }