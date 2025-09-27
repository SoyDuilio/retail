// Variables globales
let token = localStorage.getItem('auth_token');
let currentTab = 'overview';
let dashboardData = {};
let charts = {};
let refreshInterval;

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    inicializarDashboard();
    configurarEventListeners();
    iniciarActualizacionPeriodica();
});

// Inicialización del dashboard
async function inicializarDashboard() {
    try {
        mostrarCargando();
        await cargarDatosGenerales();
        await cargarResumenEjecutivo();
        configurarGraficos();
        ocultarCargando();
    } catch (error) {
        console.error('Error inicializando dashboard:', error);
        mostrarError('Error cargando el dashboard ejecutivo');
    }
}

// Cargar datos generales del header
async function cargarDatosGenerales() {
    try {
        const response = await fetch('/api/ceo/datos-generales', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Error cargando datos generales');
        
        const data = await response.json();
        if (data.success) {
            const datos = data.data;
            document.getElementById('ventasHoy').textContent = `S/ ${datos.ventas_hoy.toLocaleString()}`;
            document.getElementById('pedidosActivos').textContent = datos.pedidos_activos;
            document.getElementById('vendedoresOnline').textContent = datos.vendedores_online;
        }
    } catch (error) {
        console.error('Error cargando datos generales:', error);
    }
}

// Cargar resumen ejecutivo
async function cargarResumenEjecutivo() {
    try {
        const response = await fetch('/api/ceo/resumen-ejecutivo', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Error cargando resumen ejecutivo');
        
        const data = await response.json();
        if (data.success) {
            dashboardData.overview = data.data;
            actualizarKPIsPrincipales(data.data);
            actualizarRankingVendedores(data.data.ranking_vendedores);
            actualizarAlertasEjecutivas(data.data.alertas);
        }
    } catch (error) {
        console.error('Error cargando resumen ejecutivo:', error);
    }
}

// Actualizar KPIs principales
function actualizarKPIsPrincipales(data) {
    document.getElementById('ingresosMes').textContent = `S/ ${data.ingresos_mes.toLocaleString()}`;
    document.getElementById('pedidosMes').textContent = data.pedidos_mes;
    document.getElementById('clientesActivos').textContent = data.clientes_activos;
    document.getElementById('conversion').textContent = `${data.tasa_conversion}%`;
    
    // Actualizar cambios porcentuales
    actualizarCambio('cambioIngresos', data.cambio_ingresos);
    actualizarCambio('cambioPedidos', data.cambio_pedidos);
    actualizarCambio('cambioClientes', data.cambio_clientes);
    actualizarCambio('cambioConversion', data.cambio_conversion);
}

function actualizarCambio(elementId, valor) {
    const elemento = document.getElementById(elementId);
    const clase = valor >= 0 ? 'positive' : 'negative';
    const signo = valor >= 0 ? '+' : '';
    
    elemento.textContent = `${signo}${valor}%`;
    elemento.className = `kpi-change ${clase}`;
}

// Actualizar ranking de vendedores
function actualizarRankingVendedores(ranking) {
    const container = document.getElementById('rankingVendedores');
    container.innerHTML = '';
    
    ranking.forEach((vendedor, index) => {
        const div = document.createElement('div');
        div.className = 'ranking-item';
        div.innerHTML = `
            <div class="ranking-position">${index + 1}</div>
            <div class="ranking-info">
                <div class="ranking-name">${vendedor.nombre_completo}</div>
                <div class="ranking-metric">${vendedor.pedidos_mes} pedidos este mes</div>
            </div>
            <div class="ranking-value">S/ ${vendedor.ventas_mes.toLocaleString()}</div>
        `;
        container.appendChild(div);
    });
}

// Actualizar alertas ejecutivas
function actualizarAlertasEjecutivas(alertas) {
    const container = document.getElementById('alertasEjecutivas');
    container.innerHTML = '';
    
    alertas.forEach(alerta => {
        const div = document.createElement('div');
        div.className = `alert-item ${alerta.tipo}`;
        div.innerHTML = `
            <div class="alert-title">${alerta.titulo}</div>
            <div class="alert-description">${alerta.descripcion}</div>
        `;
        container.appendChild(div);
    });
}

// Configurar gráficos
function configurarGraficos() {
    // Gráfico de ventas por período
    const ctxVentas = document.getElementById('chartVentasPeriodo');
    if (ctxVentas && dashboardData.overview?.ventas_periodo) {
        charts.ventasPeriodo = new Chart(ctxVentas, {
            type: 'line',
            data: {
                labels: dashboardData.overview.ventas_periodo.labels,
                datasets: [{
                    label: 'Ventas',
                    data: dashboardData.overview.ventas_periodo.valores,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(156, 163, 175, 0.1)' }
                    },
                    x: {
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(156, 163, 175, 0.1)' }
                    }
                }
            }
        });
    }
    
    // Gráfico de top productos
    const ctxProductos = document.getElementById('chartTopProductos');
    if (ctxProductos && dashboardData.overview?.top_productos) {
        charts.topProductos = new Chart(ctxProductos, {
            type: 'doughnut',
            data: {
                labels: dashboardData.overview.top_productos.labels,
                datasets: [{
                    data: dashboardData.overview.top_productos.valores,
                    backgroundColor: [
                        '#10b981', '#3b82f6', '#8b5cf6', '#f59e0b',
                        '#ef4444', '#06b6d4', '#84cc16', '#f97316'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#9ca3af' }
                    }
                }
            }
        });
    }
}

// Cargar datos de ventas
async function cargarAnalisisVentas() {
    try {
        const periodo = document.getElementById('periodoVentas')?.value || '30d';
        const response = await fetch(`/api/ceo/analisis-ventas?periodo=${periodo}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Error cargando análisis de ventas');
        
        const data = await response.json();
        if (data.success) {
            dashboardData.ventas = data.data;
            actualizarGraficosVentas(data.data);
            actualizarEstadisticasVentas(data.data);
        }
    } catch (error) {
        console.error('Error cargando análisis de ventas:', error);
    }
}

// Actualizar gráficos de ventas
function actualizarGraficosVentas(data) {
    // Tendencia de ventas
    const ctxTendencia = document.getElementById('chartTendenciaVentas');
    if (ctxTendencia) {
        if (charts.tendenciaVentas) charts.tendenciaVentas.destroy();
        
        charts.tendenciaVentas = new Chart(ctxTendencia, {
            type: 'bar',
            data: {
                labels: data.tendencia.labels,
                datasets: [{
                    label: 'Ventas',
                    data: data.tendencia.valores,
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: '#3b82f6',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(156, 163, 175, 0.1)' }
                    },
                    x: {
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(156, 163, 175, 0.1)' }
                    }
                }
            }
        });
    }
    
    // Ventas por categoría
    const ctxCategoria = document.getElementById('chartVentasCategoria');
    if (ctxCategoria) {
        if (charts.ventasCategoria) charts.ventasCategoria.destroy();
        
        charts.ventasCategoria = new Chart(ctxCategoria, {
            type: 'pie',
            data: {
                labels: data.categorias.labels,
                datasets: [{
                    data: data.categorias.valores,
                    backgroundColor: [
                        '#10b981', '#3b82f6', '#8b5cf6', '#f59e0b',
                        '#ef4444', '#06b6d4', '#84cc16'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#9ca3af' }
                    }
                }
            }
        });
    }
}

// Actualizar estadísticas de ventas
function actualizarEstadisticasVentas(data) {
    document.getElementById('ticketPromedio').textContent = `S/ ${data.ticket_promedio.toLocaleString()}`;
    document.getElementById('frecuenciaCompra').textContent = `${data.frecuencia_compra} días`;
    document.getElementById('valorClientePromedio').textContent = `S/ ${data.valor_cliente_promedio.toLocaleString()}`;
}

// Cargar gestión de personal
async function cargarGestionPersonal() {
    try {
        const response = await fetch('/api/ceo/gestion-personal', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Error cargando gestión de personal');
        
        const data = await response.json();
        if (data.success) {
            dashboardData.personal = data.data;
            actualizarListaVendedores(data.data.vendedores);
            actualizarListaEvaluadores(data.data.evaluadores);
            actualizarGraficoDesempeno(data.data.desempeno);
        }
    } catch (error) {
        console.error('Error cargando gestión de personal:', error);
    }
}

// Actualizar lista de vendedores
function actualizarListaVendedores(vendedores) {
    const container = document.getElementById('listaVendedores');
    container.innerHTML = '';
    
    vendedores.forEach(vendedor => {
        const div = document.createElement('div');
        div.className = 'personal-item';
        div.innerHTML = `
            <div class="personal-avatar">${vendedor.nombre.charAt(0)}</div>
            <div class="personal-info">
                <div class="personal-name">${vendedor.nombre_completo}</div>
                <div class="personal-role">Vendedor - ${vendedor.codigo_vendedor}</div>
            </div>
            <div class="personal-status ${vendedor.online ? 'status-online' : 'status-offline'}">
                ${vendedor.online ? 'Online' : 'Offline'}
            </div>
        `;
        container.appendChild(div);
    });
}

// Actualizar lista de evaluadores
function actualizarListaEvaluadores(evaluadores) {
    const container = document.getElementById('listaEvaluadores');
    container.innerHTML = '';
    
    evaluadores.forEach(evaluador => {
        const div = document.createElement('div');
        div.className = 'personal-item';
        div.innerHTML = `
            <div class="personal-avatar">${evaluador.nombre.charAt(0)}</div>
            <div class="personal-info">
                <div class="personal-name">${evaluador.nombre_completo}</div>
                <div class="personal-role">Evaluador - ${evaluador.codigo_evaluador}</div>
            </div>
            <div class="personal-status ${evaluador.online ? 'status-online' : 'status-offline'}">
                ${evaluador.online ? 'Online' : 'Offline'}
            </div>
        `;
        container.appendChild(div);
    });
}

// Cargar productos y stock
async function cargarProductosStock() {
    try {
        const response = await fetch('/api/ceo/productos-stock', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Error cargando productos y stock');
        
        const data = await response.json();
        if (data.success) {
            dashboardData.productos = data.data;
            actualizarAlertasStock(data.data.alertas);
            actualizarTablaProductos(data.data.productos);
        }
    } catch (error) {
        console.error('Error cargando productos y stock:', error);
    }
}

// Actualizar alertas de stock
function actualizarAlertasStock(alertas) {
    document.getElementById('stockCritico').textContent = alertas.critico;
    document.getElementById('stockBajo').textContent = alertas.bajo;
    document.getElementById('stockOptimo').textContent = alertas.optimo;
    document.getElementById('totalProductos').textContent = alertas.total;
}

// Actualizar tabla de productos
function actualizarTablaProductos(productos) {
    const tbody = document.getElementById('tablaProductos');
    tbody.innerHTML = '';
    
    productos.forEach(producto => {
        const tr = document.createElement('tr');
        const estadoClass = getEstadoStockClass(producto.estado_stock);
        
        tr.innerHTML = `
            <td>
                <div>
                    <div class="font-semibold">${producto.nombre}</div>
                    <div class="text-sm text-gray-400">${producto.codigo_producto}</div>
                </div>
            </td>
            <td>${producto.stock_actual}</td>
            <td>${producto.stock_minimo}</td>
            <td>S/ ${parseFloat(producto.precio_unitario).toFixed(2)}</td>
            <td>
                <span class="px-2 py-1 rounded-full text-xs ${estadoClass}">
                    ${producto.estado_stock}
                </span>
            </td>
            <td>
                <button class="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-xs mr-2" 
                        onclick="editarProducto(${producto.id})">
                    Editar
                </button>
                <button class="bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-xs" 
                        onclick="ajustarStock(${producto.id})">
                    Stock
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function getEstadoStockClass(estado) {
    switch (estado) {
        case 'CRITICO': return 'bg-red-100 text-red-800';
        case 'BAJO': return 'bg-yellow-100 text-yellow-800';
        case 'OPTIMO': return 'bg-green-100 text-green-800';
        default: return 'bg-gray-100 text-gray-800';
    }
}

// Cargar gestión de créditos
async function cargarGestionCreditos() {
    try {
        const response = await fetch('/api/ceo/gestion-creditos', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Error cargando gestión de créditos');
        
        const data = await response.json();
        if (data.success) {
            dashboardData.creditos = data.data;
            actualizarMetricasCredito(data.data);
            actualizarGraficosCredito(data.data);
        }
    } catch (error) {
        console.error('Error cargando gestión de créditos:', error);
    }
}

// Actualizar métricas de crédito
function actualizarMetricasCredito(data) {
    document.getElementById('creditoTotal').textContent = `S/ ${data.credito_total.toLocaleString()}`;
    document.getElementById('creditoUsado').textContent = `S/ ${data.credito_usado.toLocaleString()}`;
    document.getElementById('creditoVencido').textContent = `S/ ${data.credito_vencido.toLocaleString()}`;
    document.getElementById('tasaMorosidad').textContent = `${data.tasa_morosidad}%`;
}

// Actualizar gráficos de crédito
function actualizarGraficosCredito(data) {
    // Distribución de créditos
    const ctxDistribucion = document.getElementById('chartDistribucionCreditos');
    if (ctxDistribucion) {
        if (charts.distribucionCreditos) charts.distribucionCreditos.destroy();
        
        charts.distribucionCreditos = new Chart(ctxDistribucion, {
            type: 'doughnut',
            data: {
                labels: ['Disponible', 'En Uso', 'Vencido'],
                datasets: [{
                    data: [data.credito_disponible, data.credito_usado, data.credito_vencido],
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#9ca3af' }
                    }
                }
            }
        });
    }
    
    // Evolución de morosidad
    const ctxMorosidad = document.getElementById('chartEvolucionMorosidad');
    if (ctxMorosidad) {
        if (charts.evolucionMorosidad) charts.evolucionMorosidad.destroy();
        
        charts.evolucionMorosidad = new Chart(ctxMorosidad, {
            type: 'line',
            data: {
                labels: data.evolucion_morosidad.labels,
                datasets: [{
                    label: 'Tasa de Morosidad',
                    data: data.evolucion_morosidad.valores,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            color: '#9ca3af',
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        grid: { color: 'rgba(156, 163, 175, 0.1)' }
                    },
                    x: {
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(156, 163, 175, 0.1)' }
                    }
                }
            }
        });
    }
}

// Configurar event listeners
function configurarEventListeners() {
    // Navegación de pestañas
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => cambiarTab(btn.dataset.tab));
    });
    
    // Botón de notificaciones push
    document.getElementById('btnNotificaciones').addEventListener('click', abrirModalPush);
    
    // Modal push notifications
    document.getElementById('btnCerrarModalPush').addEventListener('click', cerrarModalPush);
    document.getElementById('btnCancelarPush').addEventListener('click', cerrarModalPush);
    document.getElementById('btnEnviarPush').addEventListener('click', enviarNotificacionPush);
    
    // Filtros
    document.getElementById('periodoVentas')?.addEventListener('change', cargarAnalisisVentas);
    
    // Botones de exportar
    document.getElementById('btnExportarVentas')?.addEventListener('click', exportarReporteVentas);
    
    // Botones de agregar
    document.getElementById('btnAgregarVendedor')?.addEventListener('click', mostrarFormularioVendedor);
    document.getElementById('btnAgregarEvaluador')?.addEventListener('click', mostrarFormularioEvaluador);
    document.getElementById('btnAgregarProducto')?.addEventListener('click', mostrarFormularioProducto);
    
    // Logout
    document.getElementById('btnLogout').addEventListener('click', function() {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
    });
    
    // Cerrar modal con ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            cerrarModalPush();
        }
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
    switch (tab) {
        case 'ventas':
            if (!dashboardData.ventas) cargarAnalisisVentas();
            break;
        case 'personal':
            if (!dashboardData.personal) cargarGestionPersonal();
            break;
        case 'productos':
            if (!dashboardData.productos) cargarProductosStock();
            break;
        case 'creditos':
            if (!dashboardData.creditos) cargarGestionCreditos();
            break;
    }
}

// Modal de notificaciones push
function abrirModalPush() {
    document.getElementById('modalPushNotifications').classList.remove('hidden');
    document.getElementById('modalPushNotifications').classList.add('flex');
}

function cerrarModalPush() {
    document.getElementById('modalPushNotifications').classList.add('hidden');
    document.getElementById('modalPushNotifications').classList.remove('flex');
    
    // Limpiar formulario
    document.getElementById('tipoDestinatario').value = 'todos';
    document.getElementById('tituloNotificacion').value = '';
    document.getElementById('mensajeNotificacion').value = '';
}

// Enviar notificación push
async function enviarNotificacionPush() {
    const tipo = document.getElementById('tipoDestinatario').value;
    const titulo = document.getElementById('tituloNotificacion').value.trim();
    const mensaje = document.getElementById('mensajeNotificacion').value.trim();
    
    if (!titulo || !mensaje) {
        mostrarError('Título y mensaje son obligatorios');
        return;
    }
    
    try {
        const response = await fetch('/api/ceo/enviar-push', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tipo_destinatario: tipo,
                titulo: titulo,
                mensaje: mensaje
            })
        });
        
        if (!response.ok) throw new Error('Error enviando notificación');
        
        const data = await response.json();
        if (data.success) {
            mostrarExito(`Notificación enviada a ${data.data.destinatarios} usuarios`);
            cerrarModalPush();
        } else {
            mostrarError(data.message);
        }
    } catch (error) {
        console.error('Error enviando notificación:', error);
        mostrarError('Error enviando la notificación push');
    }
}

// Iniciar actualización periódica
function iniciarActualizacionPeriodica() {
    // Actualizar datos generales cada 30 segundos
    refreshInterval = setInterval(() => {
        cargarDatosGenerales();
        
        // Actualizar datos específicos según la pestaña activa
        switch (currentTab) {
            case 'overview':
                cargarResumenEjecutivo();
                break;
            case 'ventas':
                cargarAnalisisVentas();
                break;
            case 'personal':
                cargarGestionPersonal();
                break;
            case 'productos':
                cargarProductosStock();
                break;
            case 'creditos':
                cargarGestionCreditos();
                break;
        }
    }, 30000);
}

// Funciones de utilidad
function mostrarCargando() {
    // Implementar indicador de carga
    console.log('Cargando dashboard...');
}

function ocultarCargando() {
    // Ocultar indicador de carga
    console.log('Dashboard cargado');
}

function mostrarError(mensaje) {
    console.error(mensaje);
    alert(`Error: ${mensaje}`);
}

function mostrarExito(mensaje) {
    console.log(mensaje);
    alert(mensaje);
}

// Funciones placeholder para funcionalidades futuras
function editarProducto(productoId) {
    console.log('Editar producto:', productoId);
    mostrarError('Funcionalidad en desarrollo');
}

function ajustarStock(productoId) {
    console.log('Ajustar stock:', productoId);
    mostrarError('Funcionalidad en desarrollo');
}

function mostrarFormularioVendedor() {
    console.log('Mostrar formulario vendedor');
    mostrarError('Funcionalidad en desarrollo');
}

function mostrarFormularioEvaluador() {
    console.log('Mostrar formulario evaluador');
    mostrarError('Funcionalidad en desarrollo');
}

function mostrarFormularioProducto() {
    console.log('Mostrar formulario producto');
    mostrarError('Funcionalidad en desarrollo');
}

function exportarReporteVentas() {
    console.log('Exportar reporte de ventas');
    mostrarError('Funcionalidad en desarrollo');
}

// Cleanup al cerrar la página
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    // Destruir gráficos
    Object.values(charts).forEach(chart => {
        if (chart) chart.destroy();
    });
});