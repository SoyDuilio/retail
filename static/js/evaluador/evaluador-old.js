// Variables globales
let evaluadorData = null;
let token = localStorage.getItem('auth_token');
let pedidosPendientes = [];
let pedidoSeleccionado = null;
let limiteAprobacion = 5000;
let websocket = null;

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    inicializarDashboard();
    conectarWebSocket();
    configurarEventListeners();
});

// Inicialización del dashboard
async function inicializarDashboard() {
    try {
        await cargarDatosEvaluador();
        await cargarLimiteAprobacion();
        await cargarPedidosPendientes();
        iniciarActualizacionPeriodica();
    } catch (error) {
        console.error('Error inicializando dashboard:', error);
        mostrarError('Error cargando el dashboard');
    }
}

// Cargar datos del evaluador
async function cargarDatosEvaluador() {
    try {
        const response = await fetch('/api/evaluador/perfil', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Error cargando perfil');
        
        const data = await response.json();
        if (data.success) {
            evaluadorData = data.data;
            document.getElementById('evaluadorNombre').textContent = evaluadorData.nombre_completo;
        }
    } catch (error) {
        console.error('Error cargando datos del evaluador:', error);
    }
}

// Cargar límite de aprobación
async function cargarLimiteAprobacion() {
    try {
        const response = await fetch('/api/evaluador/limite-aprobacion', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Error cargando límite');
        
        const data = await response.json();
        if (data.success) {
            limiteAprobacion = data.data.limite;
            document.getElementById('limiteAprobacion').textContent = `S/ ${limiteAprobacion.toLocaleString()}`;
        }
    } catch (error) {
        console.error('Error cargando límite:', error);
    }
}

// Cargar pedidos pendientes
async function cargarPedidosPendientes() {
    try {
        const filtro = document.getElementById('filtroEstado').value;
        const response = await fetch(`/api/evaluador/pedidos-pendientes?estado=${filtro}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Error cargando pedidos');
        
        const data = await response.json();
        if (data.success) {
            const nuevos = data.data.filter(p => !pedidosPendientes.find(existing => existing.id === p.id));
            
            if (nuevos.length > 0) {
                reproducirSonidoNotificacion();
            }
            
            pedidosPendientes = data.data;
            actualizarContadores();
            renderizarPedidos();
        }
    } catch (error) {
        console.error('Error cargando pedidos:', error);
        mostrarError('Error cargando pedidos pendientes');
    }
}

// Conectar WebSocket
function conectarWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/evaluador/${evaluadorData?.evaluador_id || 1}`;
    
    websocket = new WebSocket(wsUrl);
    
    websocket.onopen = function() {
        console.log('WebSocket conectado');
    };
    
    websocket.onmessage = function(event) {
        const message = JSON.parse(event.data);
        manejarMensajeWebSocket(message);
    };
    
    websocket.onclose = function() {
        console.log('WebSocket desconectado. Reintentando...');
        setTimeout(conectarWebSocket, 5000);
    };
    
    websocket.onerror = function(error) {
        console.error('Error WebSocket:', error);
    };
}

// Manejar mensajes de WebSocket
function manejarMensajeWebSocket(message) {
    switch (message.type) {
        case 'nuevo_pedido':
            agregarNuevoPedido(message.data);
            reproducirSonidoNotificacion();
            break;
        case 'pedido_actualizado':
            actualizarPedido(message.data);
            break;
        case 'pedido_eliminado':
            eliminarPedido(message.data.pedido_id);
            break;
    }
}

// Renderizar pedidos
function renderizarPedidos() {
    const container = document.getElementById('colaPedidos');
    container.innerHTML = '';
    
    if (pedidosPendientes.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-12">
                <div class="text-gray-400 text-lg mb-2">
                    <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                </div>
                <h3 class="text-lg font-semibold text-gray-300 mb-2">No hay pedidos pendientes</h3>
                <p class="text-gray-400">Todos los pedidos han sido evaluados</p>
            </div>
        `;
        return;
    }
    
    // Ordenar por prioridad y antigüedad
    const pedidosOrdenados = [...pedidosPendientes].sort((a, b) => {
        // Primero por prioridad
        const prioridadA = calcularPrioridad(a);
        const prioridadB = calcularPrioridad(b);
        if (prioridadA !== prioridadB) return prioridadB - prioridadA;
        
        // Luego por antigüedad
        return new Date(a.created_at) - new Date(b.created_at);
    });
    
    pedidosOrdenados.forEach(pedido => {
        const tarjeta = crearTarjetaPedido(pedido);
        container.appendChild(tarjeta);
    });
}

// Crear tarjeta de pedido
function crearTarjetaPedido(pedido) {
    const div = document.createElement('div');
    div.className = `pedido-card ${getPriorityClass(pedido)} cursor-pointer`;
    div.dataset.pedidoId = pedido.id;
    
    const tiempoEspera = calcularTiempoEspera(pedido.created_at);
    const prioridad = calcularPrioridad(pedido);
    
    div.innerHTML = `
        <div class="card-front">
            <div class="estado-badge estado-${pedido.estado}">
                ${pedido.estado.replace('_', ' ')}
            </div>
            <div class="tiempo-espera ${getTiempoClass(tiempoEspera)}">
                ${formatearTiempo(tiempoEspera)}
            </div>
            
            <div class="cliente-info">
                <div class="cliente-nombre">${pedido.cliente.nombre_comercial || pedido.cliente.razon_social}</div>
                <div class="cliente-detalles">
                    RUC: ${pedido.cliente.ruc}<br>
                    Vendedor: ${pedido.vendedor.nombre}
                </div>
            </div>
            
            <div class="monto-pedido ${getMontoClass(pedido.total)}">
                S/ ${parseFloat(pedido.total).toLocaleString()}
            </div>
            
            <div class="text-xs text-gray-400 text-center">
                #${pedido.numero_pedido}<br>
                ${formatearFecha(pedido.created_at)}
            </div>
            
            <div class="urgencia-indicator ${getUrgenciaClass(prioridad)}"></div>
        </div>
        
        <div class="card-back">
            <div class="space-y-3">
                <div>
                    <div class="text-sm font-semibold text-gray-300 mb-1">Productos (${pedido.items?.length || 0})</div>
                    <div class="text-xs text-gray-400 max-h-16 overflow-y-auto">
                        ${(pedido.items || []).map(item => 
                            `${item.cantidad}x ${item.producto_nombre}`
                        ).join('<br>')}
                    </div>
                </div>
                
                <div class="text-xs">
                    <div class="flex justify-between">
                        <span class="text-gray-400">Modalidad:</span>
                        <span>${pedido.modalidad_pago || 'N/A'}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Plazo:</span>
                        <span>${pedido.plazo_pago || 'N/A'}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Crédito Usado:</span>
                        <span>S/ ${(pedido.cliente.credito_usado || 0).toLocaleString()}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Límite:</span>
                        <span>S/ ${(pedido.cliente.limite_credito || 0).toLocaleString()}</span>
                    </div>
                </div>
                
                <div class="text-center">
                    <button class="bg-blue-600 hover:bg-blue-700 px-4 py-1 rounded text-xs evaluar-btn">
                        Evaluar Pedido
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Event listeners
    div.addEventListener('click', function(e) {
        if (!e.target.classList.contains('evaluar-btn')) {
            voltearTarjeta(div);
        }
    });
    
    div.querySelector('.evaluar-btn')?.addEventListener('click', function(e) {
        e.stopPropagation();
        abrirModalEvaluacion(pedido);
    });
    
    return div;
}

// Funciones de utilidad
function calcularTiempoEspera(fechaCreacion) {
    const ahora = new Date();
    const creacion = new Date(fechaCreacion);
    return Math.floor((ahora - creacion) / (1000 * 60)); // minutos
}

function calcularPrioridad(pedido) {
    const tiempoEspera = calcularTiempoEspera(pedido.created_at);
    const monto = parseFloat(pedido.total);
    
    let prioridad = 0;
    
    // Por tiempo de espera
    if (tiempoEspera > 120) prioridad += 3; // Más de 2 horas
    else if (tiempoEspera > 60) prioridad += 2; // Más de 1 hora
    else if (tiempoEspera > 30) prioridad += 1; // Más de 30 min
    
    // Por monto
    if (monto > limiteAprobacion * 2) prioridad += 3;
    else if (monto > limiteAprobacion) prioridad += 2;
    else if (monto > limiteAprobacion * 0.5) prioridad += 1;
    
    return prioridad;
}

function getPriorityClass(pedido) {
    const prioridad = calcularPrioridad(pedido);
    if (prioridad >= 4) return 'priority-high';
    if (prioridad >= 2) return 'priority-medium';
    return 'priority-low';
}

function getTiempoClass(minutos) {
    if (minutos > 120) return 'tiempo-critico';
    if (minutos > 60) return 'tiempo-alto';
    return 'tiempo-normal';
}

function getMontoClass(monto) {
    const m = parseFloat(monto);
    if (m > limiteAprobacion * 2) return 'monto-critico';
    if (m > limiteAprobacion) return 'monto-alto';
    return '';
}

function getUrgenciaClass(prioridad) {
    if (prioridad >= 4) return 'urgencia-alta';
    if (prioridad >= 2) return 'urgencia-media';
    return 'urgencia-baja';
}

function formatearTiempo(minutos) {
    if (minutos < 60) return `${minutos}m`;
    const horas = Math.floor(minutos / 60);
    const mins = minutos % 60;
    return `${horas}h ${mins}m`;
}

function formatearFecha(fecha) {
    return new Date(fecha).toLocaleDateString('es-PE', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Voltear tarjeta
function voltearTarjeta(tarjeta) {
    tarjeta.classList.toggle('flipped');
}

// Abrir modal de evaluación
async function abrirModalEvaluacion(pedido) {
    pedidoSeleccionado = pedido;
    
    // Cargar datos del pedido
    await cargarDatosPedido(pedido);
    
    // Mostrar modal
    document.getElementById('modalEvaluacion').classList.remove('hidden');
    document.getElementById('modalEvaluacion').classList.add('flex');
    
    // Establecer monto por defecto
    document.getElementById('montoAprobar').value = pedido.total;
}

// Cargar datos completos del pedido
async function cargarDatosPedido(pedido) {
    try {
        // Cargar detalles del pedido
        const response = await fetch(`/api/evaluador/pedido/${pedido.id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Error cargando pedido');
        
        const data = await response.json();
        if (data.success) {
            const pedidoCompleto = data.data;
            mostrarDatosPedido(pedidoCompleto);
            
            // Cargar historial del cliente
            await cargarHistorialCliente(pedidoCompleto.cliente.id);
        }
    } catch (error) {
        console.error('Error cargando datos del pedido:', error);
        mostrarError('Error cargando datos del pedido');
    }
}

// Mostrar datos del pedido en el modal
function mostrarDatosPedido(pedido) {
    // Información del cliente
    document.getElementById('clienteRuc').textContent = pedido.cliente.ruc;
    document.getElementById('clienteRazon').textContent = pedido.cliente.razon_social;
    document.getElementById('clienteDireccion').textContent = pedido.cliente.direccion;
    document.getElementById('clienteTelefono').textContent = pedido.cliente.telefono || 'N/A';
    document.getElementById('clienteTipo').textContent = pedido.cliente.tipo_cliente?.nombre || 'N/A';
    
    // Información del pedido
    document.getElementById('pedidoNumero').textContent = pedido.numero_pedido;
    document.getElementById('pedidoVendedor').textContent = pedido.vendedor.nombre_completo;
    document.getElementById('pedidoFecha').textContent = formatearFecha(pedido.created_at);
    document.getElementById('pedidoModalidad').textContent = pedido.modalidad_pago;
    document.getElementById('pedidoTotal').textContent = `S/ ${parseFloat(pedido.total).toLocaleString()}`;
    
    // Tabla de productos
    const tbody = document.getElementById('tablaProductos');
    tbody.innerHTML = '';
    
    pedido.items.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="text-left">${item.producto_nombre}</td>
            <td class="text-right">${item.cantidad}</td>
            <td class="text-right">S/ ${parseFloat(item.precio_unitario).toFixed(2)}</td>
            <td class="text-right">S/ ${parseFloat(item.subtotal).toFixed(2)}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Cargar historial del cliente
async function cargarHistorialCliente(clienteId) {
    try {
        const response = await fetch(`/api/evaluador/historial-cliente/${clienteId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Error cargando historial');
        
        const data = await response.json();
        if (data.success) {
            const historial = data.data;
            mostrarHistorialCliente(historial);
        }
    } catch (error) {
        console.error('Error cargando historial:', error);
    }
}

// Mostrar historial del cliente
function mostrarHistorialCliente(historial) {
    document.getElementById('limiteCredito').textContent = `S/ ${historial.limite_credito.toLocaleString()}`;
    document.getElementById('creditoUsado').textContent = `S/ ${historial.credito_usado.toLocaleString()}`;
    document.getElementById('creditoDisponible').textContent = `S/ ${historial.credito_disponible.toLocaleString()}`;
    document.getElementById('ultimasCompras').textContent = historial.compras_ultimos_30_dias;
    document.getElementById('promedioPago').textContent = `${historial.promedio_dias_pago} días`;
}

// Configurar event listeners
function configurarEventListeners() {
    // Botón actualizar
    document.getElementById('btnRefresh').addEventListener('click', cargarPedidosPendientes);
    
    // Filtro de estado
    document.getElementById('filtroEstado').addEventListener('change', cargarPedidosPendientes);
    
    // Modal
    document.getElementById('btnCerrarModal').addEventListener('click', cerrarModal);
    
    // Botones de evaluación
    document.getElementById('btnAprobar').addEventListener('click', aprobarPedido);
    document.getElementById('btnRechazar').addEventListener('click', rechazarPedido);
    document.getElementById('btnEscalar').addEventListener('click', escalarPedido);
    
    // Cerrar modal con ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') cerrarModal();
    });
    
    // Logout
    document.getElementById('btnLogout').addEventListener('click', function() {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
    });
}

// Acciones de evaluación
async function aprobarPedido() {
    const monto = parseFloat(document.getElementById('montoAprobar').value);
    const observaciones = document.getElementById('observaciones').value;
    
    if (!monto || monto <= 0) {
        mostrarError('Ingrese un monto válido');
        return;
    }
    
    if (monto > limiteAprobacion) {
        if (!confirm(`El monto (S/ ${monto.toLocaleString()}) excede su límite de aprobación (S/ ${limiteAprobacion.toLocaleString()}). ¿Desea escalarlo a supervisor?`)) {
            return;
        }
        await escalarPedido();
        return;
    }
    
    await evaluarPedido('aprobado', monto, observaciones);
}

async function rechazarPedido() {
    const observaciones = document.getElementById('observaciones').value;
    
    if (!observaciones.trim()) {
        mostrarError('Debe proporcionar un motivo para el rechazo');
        return;
    }
    
    await evaluarPedido('rechazado', 0, observaciones);
}

async function escalarPedido() {
    const observaciones = document.getElementById('observaciones').value || 'Escalado por monto superior al límite';
    
    await evaluarPedido('escalado', 0, observaciones);
}

// Evaluar pedido
async function evaluarPedido(decision, monto, observaciones) {
    try {
        const response = await fetch('/api/evaluador/evaluar-pedido', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                pedido_id: pedidoSeleccionado.id,
                decision: decision,
                monto_aprobado: monto,
                observaciones: observaciones
            })
        });
        
        if (!response.ok) throw new Error('Error evaluando pedido');
        
        const data = await response.json();
        if (data.success) {
            mostrarExito(`Pedido ${decision} exitosamente`);
            cerrarModal();
            await cargarPedidosPendientes();
        } else {
            mostrarError(data.message);
        }
    } catch (error) {
        console.error('Error evaluando pedido:', error);
        mostrarError('Error procesando la evaluación');
    }
}

// Utilidades
function cerrarModal() {
    document.getElementById('modalEvaluacion').classList.add('hidden');
    document.getElementById('modalEvaluacion').classList.remove('flex');
    
    // Limpiar formulario
    document.getElementById('montoAprobar').value = '';
    document.getElementById('observaciones').value = '';
    pedidoSeleccionado = null;
}

function actualizarContadores() {
    document.getElementById('pedidosPendientes').textContent = pedidosPendientes.length;
    
    // Calcular evaluados hoy (esto vendría del backend)
    // Por ahora usar un valor simulado
    document.getElementById('evaluadosHoy').textContent = '12';
}

function agregarNuevoPedido(pedido) {
    pedidosPendientes.unshift(pedido);
    actualizarContadores();
    renderizarPedidos();
}

function actualizarPedido(pedidoActualizado) {
    const index = pedidosPendientes.findIndex(p => p.id === pedidoActualizado.id);
    if (index !== -1) {
        pedidosPendientes[index] = pedidoActualizado;
        renderizarPedidos();
    }
}

function eliminarPedido(pedidoId) {
    pedidosPendientes = pedidosPendientes.filter(p => p.id !== pedidoId);
    actualizarContadores();
    renderizarPedidos();
}

function reproducirSonidoNotificacion() {
    const audio = document.getElementById('newOrderSound');
    if (audio) {
        audio.currentTime = 0;
        audio.play().catch(e => console.log('No se pudo reproducir el sonido:', e));
    }
}

function iniciarActualizacionPeriodica() {
    // Actualizar cada 30 segundos
    setInterval(cargarPedidosPendientes, 30000);
}

function mostrarError(mensaje) {
    // Implementar sistema de notificaciones toast
    console.error(mensaje);
    alert(`Error: ${mensaje}`);
}

function mostrarExito(mensaje) {
    // Implementar sistema de notificaciones toast
    console.log(mensaje);
    alert(mensaje);
}