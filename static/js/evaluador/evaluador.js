// ==================== WEBSOCKET ====================
let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/evaluador/${evaluadorId}`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('✅ WebSocket conectado');
        reconnectAttempts = 0;
        mostrarNotificacion('Conectado - Recibirás notificaciones en tiempo real', 'success');
    };
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };
    
    ws.onerror = (error) => {
        console.error('❌ Error WebSocket:', error);
    };
    
    ws.onclose = () => {
        console.log('❌ WebSocket cerrado');
        
        // Intentar reconectar
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
            console.log(`Reintentando conexión en ${delay/1000}s...`);
            setTimeout(connectWebSocket, delay);
        } else {
            mostrarNotificacion('Conexión perdida. Recarga la página.', 'error');
        }
    };
}

function handleWebSocketMessage(message) {
    console.log('📨 Mensaje recibido:', message);
    
    switch(message.type) {
        case 'pedido_nuevo':
            handlePedidoNuevo(message.data);
            break;
        case 'pedido_actualizado':
            handlePedidoActualizado(message.data);
            break;
        case 'system_message':
            mostrarNotificacion(message.data.message, 'info');
            break;
        case 'emergency':
            mostrarNotificacion('🚨 ' + message.data.message, 'error');
            break;
    }
    
    // Reproducir sonido si está habilitado
    if (message.sound) {
        playNotificationSound();
    }
}

function handlePedidoNuevo(data) {
    // Notificación visual
    mostrarNotificacion(
        `🔔 Nuevo pedido: ${data.numero_pedido} - ${data.cliente} - S/ ${data.total}`,
        'info'
    );
    
    // Recargar lista de pedidos
    cargarPedidosPendientes();
    cargarEstadisticas();
    
    // Parpadear título de la página
    blinkPageTitle('¡Nuevo Pedido!');
}

function handlePedidoActualizado(data) {
    // Recargar lista
    cargarPedidosPendientes();
    cargarEstadisticas();
}

function playNotificationSound() {
    // Sonido simple con Web Audio API
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    } catch (e) {
        console.log('No se pudo reproducir sonido');
    }
}

function blinkPageTitle(message) {
    let original = document.title;
    let count = 0;
    const interval = setInterval(() => {
        document.title = count % 2 === 0 ? message : original;
        count++;
        if (count > 6) {
            clearInterval(interval);
            document.title = original;
        }
    }, 1000);
}
// Fin conexión WebSocket
// =======================

let filtrosActivos = {
    texto: '',
    estado: 'todos',
    monto: 'todos',
    vendedor: 'todos'
};

// ==================== CONFIGURACIÓN ====================
let token = localStorage.getItem('auth_token');
let evaluadorId = null;
let pedidosPendientes = [];
let pedidoSeleccionado = null;

// ==================== INICIALIZACIÓN ====================
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Iniciando dashboard evaluador...');
    
    if (!token) {
        console.error('❌ No hay token');
        window.location.href = '/login';
        return;
    }
    
    // Obtener ID del evaluador desde la URL
    const pathParts = window.location.pathname.split('/');
    evaluadorId = pathParts[pathParts.length - 1];
    
    // Conectar WebSocket
    connectWebSocket();
    
    await cargarEstadisticas();
    await cargarPedidosPendientes();
    
    // Auto-refresh cada 30 segundos
    setInterval(() => {
        cargarEstadisticas();
        cargarPedidosPendientes();
    }, 30000);
});

// ==================== ESTADÍSTICAS ====================
async function cargarEstadisticas() {
    try {
        const response = await fetch('/api/evaluador/estadisticas', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            document.querySelector('.stat-item:nth-child(1) .stat-number').textContent = result.data.pendientes;
            document.querySelector('.stat-item:nth-child(2) .stat-number').textContent = result.data.evaluados_hoy;
            document.querySelector('.stat-item:nth-child(3) .stat-number').textContent = result.data.tasa_aprobacion + '%';
        }
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
}

// ==================== PEDIDOS PENDIENTES ====================
async function cargarPedidosPendientes() {
    try {
        const response = await fetch('/api/evaluador/pedidos-pendientes', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            pedidosPendientes = result.data;
            aplicarFiltros(); // ✅ Aplica filtros guardados en lugar de mostrar todos
        }
    } catch (error) {
        console.error('Error cargando pedidos:', error);
        mostrarNotificacion('Error al cargar pedidos', 'error');
    }
}

// Nueva función que aplica filtros
function aplicarFiltros() {
    let pedidosFiltrados = [...pedidosPendientes];
    
    // Filtro por texto
    if (filtrosActivos.texto) {
        pedidosFiltrados = pedidosFiltrados.filter(p => 
            p.numero_pedido.toLowerCase().includes(filtrosActivos.texto) ||
            p.cliente_nombre.toLowerCase().includes(filtrosActivos.texto) ||
            p.cliente_ruc.includes(filtrosActivos.texto)
        );
    }
    
    // Filtro por prioridad
    if (filtrosActivos.estado !== 'todos') {
        pedidosFiltrados = pedidosFiltrados.filter(p => p.prioridad === filtrosActivos.estado);
    }
    
    // Filtro por monto
    if (filtrosActivos.monto !== 'todos') {
        pedidosFiltrados = pedidosFiltrados.filter(p => {
            if (filtrosActivos.monto === 'bajo') return p.total < 1000;
            if (filtrosActivos.monto === 'medio') return p.total >= 1000 && p.total <= 5000;
            if (filtrosActivos.monto === 'alto') return p.total > 5000;
            return true;
        });
    }
    
    mostrarPedidos(pedidosFiltrados);
}

function mostrarPedidos(pedidos) {
    const container = document.getElementById('pedidos-container');
    
    if (pedidos.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 60px 20px; color: rgba(255,255,255,0.8); grid-column: 1/-1;">
                <div style="font-size: 3em; margin-bottom: 20px;">✅</div>
                <h3 style="color: white;">No hay pedidos pendientes</h3>
                <p>Todos los pedidos han sido evaluados</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = pedidos.map(pedido => {
        // Calcular tiempo transcurrido
        const ahora = new Date();
        const fechaPedido = new Date(`${pedido.fecha}T${pedido.hora}`);
        const diffMs = ahora - fechaPedido;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        
        let tiempoTranscurrido = '';
        let badgeClass = 'normal';
        
        if (diffHours > 2) {
            tiempoTranscurrido = `${diffHours}h ${diffMins % 60}m`;
            badgeClass = 'critico';
        } else if (diffMins > 45) {
            tiempoTranscurrido = `${diffMins}m`;
            badgeClass = 'urgente';
        } else {
            tiempoTranscurrido = `${diffMins}m`;
            badgeClass = 'normal';
        }
        
        return `
            <div class="pedido-card ${pedido.prioridad}" data-id="${pedido.id}">
                <div class="pedido-header">
                    <div>
                        <div class="pedido-numero">#${pedido.numero_pedido}</div>
                        <div class="pedido-cliente">${pedido.cliente_nombre}</div>
                        <div class="pedido-vendedor">RUC: ${pedido.cliente_ruc}</div>
                        <div class="pedido-vendedor">Vendedor: ${pedido.vendedor_nombre}</div>
                    </div>
                    <div class="prioridad-badge ${badgeClass}">
                        ${tiempoTranscurrido}
                    </div>
                </div>
                
                <div class="pedido-monto">
                    <span class="monto-label">Monto Total</span>
                    <span class="monto-valor">S/ ${pedido.total.toFixed(2)}</span>
                </div>
                
                <div class="pedido-productos-preview" id="productos-preview-${pedido.id}">
                    <div style="padding: 15px 20px; color: #64748b; font-size: 0.9em;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span>📦 ${pedido.items_count} producto(s)</span>
                            <button class="btn-link" onclick="cargarProductosPedido(${pedido.id})">
                                Ver productos →
                            </button>
                        </div>
                    </div>
                </div>
                
                <div style="padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; background: #f8fafc; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
                    <div>
                        <span style="color: #64748b; font-size: 0.85em;">Crédito usado:</span>
                        <strong style="color: #334155; margin-left: 5px;">--</strong>
                    </div>
                    <div>
                        <span style="color: #64748b; font-size: 0.85em;">Días:</span>
                        <strong style="color: #334155; margin-left: 5px;">--</strong>
                    </div>
                </div>
                
                <div style="padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; background: #f8fafc;">
                    <div>
                        <span style="color: #64748b; font-size: 0.85em;">Límite:</span>
                        <strong style="color: #334155; margin-left: 5px;">S/ 5,000</strong>
                    </div>
                    <div>
                        <span style="color: #64748b; font-size: 0.85em;">Score:</span>
                        <strong style="color: #16a34a; margin-left: 5px;">72/100</strong>
                    </div>
                </div>
                
                <div class="validaciones-container">
                    <div class="validacion ${pedido.validaciones.vendedor_activo ? 'ok' : 'error'}">
                        ${pedido.validaciones.vendedor_activo ? '✓' : '✗'} Vendedor Activo
                    </div>
                    <div class="validacion ${pedido.validaciones.cliente_en_zona ? 'ok' : 'error'}">
                        ${pedido.validaciones.cliente_en_zona ? '✓' : '✗'} Cliente en Zona
                    </div>
                    <div class="validacion ${pedido.validaciones.monto_dentro_limite ? 'ok' : 'error'}">
                        ${pedido.validaciones.monto_dentro_limite ? '✓' : '✗'} Monto Permitido
                    </div>
                    <div class="validacion ${pedido.validaciones.cliente_no_moroso ? 'ok' : 'error'}">
                        ${pedido.validaciones.cliente_no_moroso ? '✓' : '✗'} Sin Mora
                    </div>
                </div>
                
                <div class="pedido-actions">
                    <button class="btn btn-secondary" onclick="verDetalle(${pedido.id})">
                        📋 Ver Detalle
                    </button>
                    <button class="btn btn-success" onclick="evaluarPedido(${pedido.id}, 'aprobado')">
                        ✅ Aprobar
                    </button>
                    <button class="btn btn-danger" onclick="evaluarPedido(${pedido.id}, 'rechazado')">
                        ❌ Rechazar
                    </button>
                </div>
            </div>
        `;
    }).join('');
}


// ==================== CARGAR PRODUCTOS DE UN PEDIDO ====================
async function cargarProductosPedido(pedidoId) {
    const previewDiv = document.getElementById(`productos-preview-${pedidoId}`);
    
    // Si ya están cargados, solo expandir/colapsar
    if (previewDiv.dataset.loaded === 'true') {
        if (previewDiv.dataset.expanded === 'true') {
            // Colapsar
            const items = previewDiv.querySelectorAll('.producto-item');
            items.forEach((item, idx) => {
                if (idx >= 2) item.style.display = 'none';
            });
            previewDiv.dataset.expanded = 'false';
            previewDiv.querySelector('.btn-link').textContent = `+ ${items.length - 2} producto(s) más`;
        } else {
            // Expandir
            const items = previewDiv.querySelectorAll('.producto-item');
            items.forEach(item => item.style.display = 'flex');
            previewDiv.dataset.expanded = 'true';
            previewDiv.querySelector('.btn-link').textContent = '− Ver menos';
        }
        return;
    }
    
    // Mostrar loading
    previewDiv.innerHTML = '<div style="padding: 15px 20px; text-align: center; color: #64748b; font-size: 0.85em;">Cargando productos...</div>';
    
    try {
        const response = await fetch(`/api/evaluador/pedido/${pedidoId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const result = await response.json();
        
        if (result.success && result.data.items) {
            const items = result.data.items;
            const mostrarTodos = items.length <= 3;
            const itemsOcultos = items.length - 2;
            
            previewDiv.innerHTML = `
                <div style="padding: 8px 15px;">
                    ${items.map((item, idx) => `
                        <div class="producto-item" style="display: ${!mostrarTodos && idx >= 2 ? 'none' : 'flex'};">
                            <span style="color: #334155; flex: 1;">
                                <strong>${Math.floor(item.cantidad)}x</strong> ${item.producto_nombre}
                            </span>
                        </div>
                    `).join('')}
                    
                    ${!mostrarTodos ? `
                        <div style="text-align: center; margin-top: 8px;">
                            <button class="btn-link" onclick="toggleProductos(${pedidoId})">
                                + ${itemsOcultos} producto(s) más
                            </button>
                        </div>
                    ` : ''}
                </div>
            `;
            
            previewDiv.dataset.loaded = 'true';
            previewDiv.dataset.expanded = 'false';
            
            // Actualizar info de crédito si está disponible
            if (result.data.cliente) {
                const card = document.querySelector(`[data-id="${pedidoId}"]`);
                if (card && result.data.cliente.deuda_actual !== undefined) {
                    const creditoUsado = result.data.cliente.deuda_actual || 0;
                    const diasMora = result.data.cliente.dias_mora || 0;
                    const tasaPago = result.data.cliente.tasa_pago || 0;
                    
                    // Actualizar valores de crédito
                    const infoRows = card.querySelectorAll('[style*="background: #f8fafc"]');
                    if (infoRows[0]) {
                        const strongs = infoRows[0].querySelectorAll('strong');
                        if (strongs[0]) strongs[0].textContent = `${Math.round(creditoUsado / 5000 * 100)}%`;
                        if (strongs[1]) strongs[1].textContent = diasMora;
                    }
                    if (infoRows[1]) {
                        const strongs = infoRows[1].querySelectorAll('strong');
                        if (strongs[1]) strongs[1].textContent = `${tasaPago}/100`;
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error cargando productos:', error);
        previewDiv.innerHTML = `
            <div style="padding: 15px 20px; color: #ef4444; font-size: 0.85em; text-align: center;">
                Error al cargar productos
                <button class="btn-link" onclick="cargarProductosPedido(${pedidoId})">Reintentar</button>
            </div>
        `;
    }
}

// Nueva función para expandir/colapsar productos
function toggleProductos(pedidoId) {
    const previewDiv = document.getElementById(`productos-preview-${pedidoId}`);
    const items = previewDiv.querySelectorAll('.producto-item');
    const btnLink = previewDiv.querySelector('.btn-link');
    const isExpanded = previewDiv.dataset.expanded === 'true';
    
    if (isExpanded) {
        // Colapsar - ocultar después del segundo
        items.forEach((item, idx) => {
            if (idx >= 2) item.style.display = 'none';
        });
        btnLink.textContent = `+ ${items.length - 2} producto(s) más`;
        previewDiv.dataset.expanded = 'false';
    } else {
        // Expandir - mostrar todos
        items.forEach(item => item.style.display = 'flex');
        btnLink.textContent = '− Ver menos';
        previewDiv.dataset.expanded = 'true';
    }
}


// ==================== VER DETALLE ====================
async function verDetalle(pedidoId) {
    try {
        const response = await fetch(`/api/evaluador/pedido/${pedidoId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            mostrarModalDetalle(result.data);
        }
    } catch (error) {
        console.error('Error obteniendo detalle:', error);
        mostrarNotificacion('Error al cargar detalle', 'error');
    }
}

function mostrarModalDetalle(data) {
    const modal = document.getElementById('modal-evaluacion');
    document.getElementById('modal-pedido-id').textContent = data.pedido.numero_pedido;
    
    // Actualizar información del modal con datos reales
    const scoreCredito = data.cliente.tasa_pago || 85;
    const utilizacionCredito = data.cliente.deuda_actual > 0 ? 
        Math.min((data.cliente.deuda_actual / 10000 * 100), 100) : 30;
    const historialPagos = data.cliente.tasa_pago || 98;
    
    // Actualizar cards de riesgo
    document.querySelector('.risk-card:nth-child(1) div:nth-child(2)').textContent = `${scoreCredito}/100`;
    document.querySelector('.risk-card:nth-child(2) div:nth-child(2)').textContent = `${Math.round(utilizacionCredito)}%`;
    document.querySelector('.risk-card:nth-child(3) div:nth-child(2)').textContent = `${historialPagos}%`;
    
    // Guardar referencia del pedido actual
    pedidoSeleccionado = data.pedido;
    
    modal.classList.add('show');
}

// ==================== EVALUAR PEDIDO ====================
async function evaluarPedido(pedidoId, resultado) {
    // ✅ Mostrar confirmación con notificación en lugar de confirm()
    if (resultado === 'rechazado') {
        const motivoRechazo = prompt('Motivo del rechazo:');
        if (!motivoRechazo) {
            mostrarNotificacion('Debes ingresar un motivo de rechazo', 'warning');
            return;
        }
        
        // Mostrar loading
        mostrarNotificacion('Procesando rechazo...', 'info');
        
        try {
            const response = await fetch('/api/evaluador/evaluar-pedido', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    pedido_id: pedidoId,
                    resultado: resultado,
                    motivo_rechazo: motivoRechazo,
                    observaciones: null
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                mostrarNotificacion('✅ Pedido rechazado exitosamente', 'success');
                
                // Recargar pedidos
                await cargarPedidosPendientes();
                await cargarEstadisticas();
            } else {
                mostrarNotificacion('❌ ' + (result.message || 'Error al rechazar pedido'), 'error');
            }
        } catch (error) {
            console.error('Error evaluando pedido:', error);
            mostrarNotificacion('❌ Error de conexión', 'error');
        }
    } else {
        // Aprobar sin pedir confirmación, solo notificar
        mostrarNotificacion('Procesando aprobación...', 'info');
        
        try {
            const response = await fetch('/api/evaluador/evaluar-pedido', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    pedido_id: pedidoId,
                    resultado: resultado,
                    motivo_rechazo: null,
                    observaciones: null
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                mostrarNotificacion('✅ Pedido aprobado exitosamente', 'success');
                
                // Recargar pedidos
                await cargarPedidosPendientes();
                await cargarEstadisticas();
            } else {
                mostrarNotificacion('❌ ' + (result.message || 'Error al aprobar pedido'), 'error');
            }
        } catch (error) {
            console.error('Error evaluando pedido:', error);
            mostrarNotificacion('❌ Error de conexión', 'error');
        }
    }
}

// ==================== MODAL ====================
function cerrarModal() {
    document.getElementById('modal-evaluacion').classList.remove('show');
    pedidoSeleccionado = null;
}

function guardarEvaluacion() {
    if (!pedidoSeleccionado) return;
    
    const decision = document.getElementById('decision-evaluacion').value;
    const comentarios = document.getElementById('comentarios').value;
    
    evaluarPedido(
        pedidoSeleccionado.id,
        decision === 'condicional' ? 'aprobado' : decision
    );
    
    cerrarModal();
}

// ==================== FILTROS ====================
function filtrarPedidos() {
    const searchText = document.querySelector('.search-input').value.toLowerCase();
    const estadoFilter = document.querySelectorAll('.filter-select')[0].value;
    const montoFilter = document.querySelectorAll('.filter-select')[1].value;
    const vendedorFilter = document.querySelectorAll('.filter-select')[2].value;
    
    // Guardar filtros
    filtrosActivos = {
        texto: searchText,
        estado: estadoFilter,
        monto: montoFilter,
        vendedor: vendedorFilter
    };
    
    aplicarFiltros();
}

// ==================== UTILIDADES ====================
function formatearFecha(fecha) {
    const date = new Date(fecha);
    return date.toLocaleDateString('es-PE', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function formatearTipoPago(tipo) {
    const tipos = {
        'CREDITO': '💳 Crédito',
        'CONTADO': '💵 Contado',
        'EFECTIVO_CASH': '💵 Efectivo',
        'EFECTIVO_YAPE': '📱 Yape',
        'EFECTIVO_PLIN': '📱 Plin'
    };
    return tipos[tipo] || tipo;
}

function mostrarNotificacion(mensaje, tipo = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = mensaje;
    notification.className = `notification ${tipo} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

function actualizarPedidos() {
    mostrarNotificacion('Actualizando...', 'info');
    cargarEstadisticas();
    cargarPedidosPendientes();
}

function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    window.location.href = '/login';
}

// Cerrar modal al hacer clic fuera
window.onclick = function(event) {
    const modal = document.getElementById('modal-evaluacion');
    if (event.target == modal) {
        cerrarModal();
    }
}