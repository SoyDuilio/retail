// Variables globales
let supervisorData = null;
let token = localStorage.getItem('auth_token');
let pedidosEscalados = [];
let politicasCredito = {};
let limitesEvaluadores = [];
let plazosCredito = [];
let currentTab = 'pedidos';
let websocket = null;

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    inicializarDashboard();
    configurarEventListeners();
    conectarWebSocket();
});

// Inicialización del dashboard
async function inicializarDashboard() {
    try {
        await cargarDatosSupervisor();
        await cargarPedidosEscalados();
        await cargarPoliticasCredito();
        await cargarMetricas();
        iniciarActualizacionPeriodica();
    } catch (error) {
        console.error('Error inicializando dashboard:', error);
        mostrarError('Error cargando el dashboard');
    }
}

// Cargar datos del supervisor
async function cargarDatosSupervisor() {
    try {
        const response = await fetch('/api/supervisor/perfil', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Error cargando perfil');
        
        const data = await response.json();
        if (data.success) {
            supervisorData = data.data;
            document.getElementById('supervisorNombre').textContent = supervisorData.nombre_completo;
        }
    } catch (error) {
        console.error('Error cargando datos del supervisor:', error);
    }
}

// Cargar pedidos escalados
async function cargarPedidosEscalados() {
    try {
        const prioridad = document.getElementById('filtroPrioridad')?.value || 'todas';
        const response = await fetch(`/api/supervisor/pedidos-escalados?prioridad=${prioridad}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Error cargando pedidos escalados');
        
        const data = await response.json();
        if (data.success) {
            const nuevos = data.data.filter(p => !pedidosEscalados.find(existing => existing.id === p.id));
            
            if (nuevos.length > 0) {
                reproducirSonidoNotificacion();
            }
            
            pedidosEscalados = data.data;
            actualizarContadoresHeader();
            renderizarPedidosEscalados();
        }
    } catch (error) {
        console.error('Error cargando pedidos escalados:', error);
        mostrarError('Error cargando pedidos escalados');
    }
}

// Renderizar pedidos escalados
function renderizarPedidosEscalados() {
    const container = document.getElementById('colaPedidosEscalados');
    container.innerHTML = '';
    
    if (pedidosEscalados.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-12">
                <div class="text-gray-400 text-lg mb-2">
                    <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                    </svg>
                </div>
                <h3 class="text-lg font-semibold text-gray-300 mb-2">No hay pedidos escalados</h3>
                <p class="text-gray-400">Todos los pedidos han sido procesados</p>
            </div>
        `;
        return;
    }
    
    // Ordenar por prioridad y urgencia
    const pedidosOrdenados = [...pedidosEscalados].sort((a, b) => {
        const urgenciaA = calcularUrgencia(a);
        const urgenciaB = calcularUrgencia(b);
        if (urgenciaA !== urgenciaB) return urgenciaB - urgenciaA;
        
        return new Date(a.fecha_escalacion) - new Date(b.fecha_escalacion);
    });
    
    pedidosOrdenados.forEach(pedido => {
        const tarjeta = crearTarjetaPedidoEscalado(pedido);
        container.appendChild(tarjeta);
    });
}

// Crear tarjeta de pedido escalado
function crearTarjetaPedidoEscalado(pedido) {
    const div = document.createElement('div');
    const urgencia = calcularUrgencia(pedido);
    const tiempoEscalacion = calcularTiempoEscalacion(pedido.fecha_escalacion);
    
    div.className = `pedido-escalado-card ${urgencia >= 3 ? 'urgente' : ''}`;
    div.dataset.pedidoId = pedido.id;
    
    div.innerHTML = `
        <div class="escalacion-badge">Escalado</div>
        <div class="escalacion-motivo">${pedido.motivo_escalacion || 'Monto alto'}</div>
        
        <div class="mt-8">
            <div class="font-bold text-lg text-white mb-2">
                ${pedido.cliente.nombre_comercial || pedido.cliente.razon_social}
            </div>
            <div class="text-sm text-gray-300 mb-3">
                RUC: ${pedido.cliente.ruc}<br>
                #${pedido.numero_pedido}
            </div>
            
            <div class="evaluador-info">
                <div class="evaluador-nombre">Evaluador: ${pedido.evaluador.nombre_completo}</div>
                <div class="evaluador-comentario">"${pedido.comentario_evaluador || 'Sin comentarios'}"</div>
            </div>
            
            <div class="text-2xl font-bold text-yellow-400 text-center my-3">
                S/ ${parseFloat(pedido.total).toLocaleString()}
            </div>
            
            <div class="text-xs text-gray-300 text-center">
                Escalado: ${formatearTiempo(tiempoEscalacion)} atrás<br>
                ${formatearFecha(pedido.fecha_escalacion)}
            </div>
        </div>
    `;
    
    div.addEventListener('click', () => abrirModalEvaluacionSupervisor(pedido));
    
    return div;
}

// Conectar WebSocket
function conectarWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/supervisor/${supervisorData?.supervisor_id || 1}`;
    
    websocket = new WebSocket(wsUrl);
    
    websocket.onopen = function() {
        console.log('WebSocket Supervisor conectado');
    };
    
    websocket.onmessage = function(event) {
        const message = JSON.parse(event.data);
        manejarMensajeWebSocket(message);
    };
    
    websocket.onclose = function() {
        console.log('WebSocket desconectado. Reintentando...');
        setTimeout(conectarWebSocket, 5000);
    };
}

// Manejar mensajes WebSocket
function manejarMensajeWebSocket(message) {
    switch (message.type) {
        case 'pedido_escalado':
            agregarPedidoEscalado(message.data);
            reproducirSonidoNotificacion();
            break;
        case 'pedido_resuelto':
            eliminarPedidoEscalado(message.data.pedido_id);
            break;
    }
}

// Cargar políticas de crédito
async function cargarPoliticasCredito() {
    try {
        const response = await fetch('/api/supervisor/politicas-credito', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Error cargando políticas');
        
        const data = await response.json();
        if (data.success) {
            politicasCredito = data.data;
            limitesEvaluadores = data.data.limites_evaluadores || [];
            plazosCredito = data.data.plazos_credito || [];
            
            renderizarPoliticasCredito();
        }
    } catch (error) {
        console.error('Error cargando políticas:', error);
    }
}

// Renderizar políticas de crédito
function renderizarPoliticasCredito() {
    renderizarLimitesCredito();
    renderizarLimitesEvaluadores();
    renderizarPlazosCredito();
}

// Renderizar límites de crédito por tipo de cliente
function renderizarLimitesCredito() {
    const container = document.getElementById('limitesCredito');
    container.innerHTML = '';
    
    const tiposCliente = politicasCredito.tipos_cliente || [];
    
    tiposCliente.forEach(tipo => {
        const div = document.createElement('div');
        div.className = 'politica-card';
        div.innerHTML = `
            <div class="flex justify-between items-center mb-3">
                <h4 class="font-semibold text-white">${tipo.nombre}</h4>
                <button class="text-red-400 hover:text-red-300 text-sm" onclick="eliminarTipoCliente(${tipo.id})">
                    Eliminar
                </button>
            </div>
            <div class="grid grid-cols-2 gap-3">
                <div class="input-group">
                    <label>Límite Máximo</label>
                    <input type="number" value="${tipo.limite_maximo}" 
                           onchange="actualizarLimiteCredito(${tipo.id}, 'limite_maximo', this.value)"
                           step="100" min="0">
                </div>
                <div class="input-group">
                    <label>Límite por Defecto</label>
                    <input type="number" value="${tipo.limite_defecto}" 
                           onchange="actualizarLimiteCredito(${tipo.id}, 'limite_defecto', this.value)"
                           step="100" min="0">
                </div>
            </div>
            <div class="input-group">
                <label>Días de Gracia</label>
                <input type="number" value="${tipo.dias_gracia}" 
                       onchange="actualizarLimiteCredito(${tipo.id}, 'dias_gracia', this.value)"
                       step="1" min="0" max="30">
            </div>
        `;
        container.appendChild(div);
    });
}

// Renderizar límites de evaluadores
function renderizarLimitesEvaluadores() {
    const container = document.getElementById('limitesEvaluadores');
    container.innerHTML = '';
    
    limitesEvaluadores.forEach(evaluador => {
        const div = document.createElement('div');
        div.className = 'evaluador-limite-card';
        div.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <div class="evaluador-avatar">
                        ${evaluador.nombre.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <div class="font-semibold text-white text-sm">${evaluador.nombre_completo}</div>
                        <div class="text-gray-400 text-xs">Evaluador #${evaluador.codigo}</div>
                    </div>
                </div>
                <div class="text-right">
                    <input type="number" value="${evaluador.limite_aprobacion}" 
                           onchange="actualizarLimiteEvaluador(${evaluador.id}, this.value)"
                           class="w-24 bg-gray-600 px-2 py-1 rounded text-sm text-center"
                           step="1000" min="0">
                    <div class="text-xs text-gray-400 mt-1">Límite S/</div>
                </div>
            </div>
        `;
        container.appendChild(div);
    });
}

// Renderizar plazos de crédito
function renderizarPlazosCredito() {
    const container = document.getElementById('plazosCredito');
    container.innerHTML = '';
    
    plazosCredito.forEach(plazo => {
        const div = document.createElement('div');
        div.className = `plazo-card ${plazo.activo ? 'activo' : ''}`;
        div.onclick = () => togglePlazoCredito(plazo.id);
        div.innerHTML = `
            <div class="plazo-dias">${plazo.dias} días</div>
            <div class="plazo-descripcion">${plazo.descripcion}</div>
            <div class="text-xs mt-2 ${plazo.activo ? 'text-green-400' : 'text-gray-500'}">
                ${plazo.activo ? 'Activo' : 'Inactivo'}
            </div>
        `;
        container.appendChild(div);
    });
}

// Cargar métricas
async function cargarMetricas() {
    try {
        const periodo = document.getElementById('filtroTiempo')?.value || 'mes';
        const response = await fetch(`/api/supervisor/metricas?periodo=${periodo}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Error cargando métricas');
        
        const data = await response.json();
        if (data.success) {
            actualizarKPIs(data.data);
            actualizarGraficos(data.data);
            actualizarRankingVendedores(data.data.ranking_vendedores);
        }
    } catch (error) {
        console.error('Error cargando métricas:', error);
    }
}

// Actualizar KPIs
function actualizarKPIs(metricas) {
    document.getElementById('totalPedidos').textContent = metricas.total_pedidos || 0;
    document.getElementById('tasaAprobacion').textContent = `${metricas.tasa_aprobacion || 0}%`;
    document.getElementById('tiempoPromedio').textContent = `${metricas.tiempo_promedio || 0}m`;
    document.getElementById('montoTotal').textContent = `S/ ${(metricas.monto_total || 0).toLocaleString()}`;
}

// Configurar event listeners
function configurarEventListeners() {
    // Navegación de pestañas
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => cambiarTab(btn.dataset.tab));
    });
    
    // Botones de refresh
    document.getElementById('btnRefreshPedidos')?.addEventListener('click', cargarPedidosEscalados);
    
    // Filtros
    document.getElementById('filtroPrioridad')?.addEventListener('change', cargarPedidosEscalados);
    document.getElementById('filtroTiempo')?.addEventListener('change', cargarMetricas);
    
    // Guardar políticas
    document.getElementById('btnGuardarPoliticas')?.addEventListener('click', guardarPoliticas);
    
    // Agregar elementos
    document.getElementById('btnAgregarTipoCliente')?.addEventListener('click', mostrarFormularioTipoCliente);
    document.getElementById('btnAgregarPlazo')?.addEventListener('click', mostrarFormularioPlazo);
    
    // Exportar reporte
    document.getElementById('btnExportarReporte')?.addEventListener('click', exportarReporte);
    
    // Modal
    document.getElementById('btnCerrarModalSupervisor')?.addEventListener('click', cerrarModalSupervisor);
    
    // Logout
    document.getElementById('btnLogout').addEventListener('click', function() {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
    });
}

// Cambiar pestaña
function cambiarTab(tab) {
    // Actualizar botones
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    
    // Actualizar contenido
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`tab-${tab}`).classList.add('active');
    
    currentTab = tab;
    
    // Cargar datos específicos de la pestaña
    if (tab === 'politicas' && Object.keys(politicasCredito).length === 0) {
        cargarPoliticasCredito();
    } else if (tab === 'metricas') {
        cargarMetricas();
    }
}

// Funciones de utilidad
function calcularUrgencia(pedido) {
    const tiempoEscalacion = calcularTiempoEscalacion(pedido.fecha_escalacion);
    const monto = parseFloat(pedido.total);
    
    let urgencia = 0;
    
    // Por tiempo desde escalación
    if (tiempoEscalacion > 240) urgencia += 3; // Más de 4 horas
    else if (tiempoEscalacion > 120) urgencia += 2; // Más de 2 horas
    else if (tiempoEscalacion > 60) urgencia += 1; // Más de 1 hora
    
    // Por monto
    if (monto > 50000) urgencia += 3;
    else if (monto > 20000) urgencia += 2;
    else if (monto > 10000) urgencia += 1;
    
    return urgencia;
}

function calcularTiempoEscalacion(fechaEscalacion) {
    const ahora = new Date();
    const escalacion = new Date(fechaEscalacion);
    return Math.floor((ahora - escalacion) / (1000 * 60)); // minutos
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

function actualizarContadoresHeader() {
    const hoy = new Date().toDateString();
    const escaladosHoy = pedidosEscalados.filter(p => 
        new Date(p.fecha_escalacion).toDateString() === hoy
    ).length;
    
    document.getElementById('escaladosHoy').textContent = escaladosHoy;
    // Los otros contadores se actualizan desde las métricas
}

function reproducirSonidoNotificacion() {
    const audio = document.getElementById('newOrderSound');
    if (audio) {
        audio.currentTime = 0;
        audio.play().catch(e => console.log('No se pudo reproducir el sonido:', e));
    }
}

function iniciarActualizacionPeriodica() {
    // Actualizar cada 60 segundos
    setInterval(() => {
        if (currentTab === 'pedidos') {
            cargarPedidosEscalados();
        } else if (currentTab === 'metricas') {
            cargarMetricas();
        }
    }, 60000);
}

function mostrarError(mensaje) {
    console.error(mensaje);
    // Implementar sistema de notificaciones toast
    alert(`Error: ${mensaje}`);
}

function mostrarExito(mensaje) {
    console.log(mensaje);
    // Implementar sistema de notificaciones toast
    alert(mensaje);
}

// Funciones específicas del supervisor (placeholder para implementar)
function abrirModalEvaluacionSupervisor(pedido) {
    // Implementar modal específico del supervisor
    console.log('Abrir modal evaluación supervisor:', pedido);
}

function cerrarModalSupervisor() {
    // Implementar cierre del modal
    console.log('Cerrar modal supervisor');
}

function guardarPoliticas() {
    // Implementar guardado de políticas
    console.log('Guardar políticas');
}

function actualizarGraficos(data) {
    // Implementar gráficos con Chart.js
    console.log('Actualizar gráficos:', data);
}

function actualizarRankingVendedores(ranking) {
    // Implementar tabla de ranking
    console.log('Actualizar ranking:', ranking);
}

function exportarReporte() {
    // Implementar exportación de reportes
    console.log('Exportar reporte');
}