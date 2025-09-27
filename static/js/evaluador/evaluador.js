// Variables globales
let pedidosData = [];
let filtrosActivos = {
    estado: 'todos',
    monto: 'todos', 
    vendedor: 'todos',
    busqueda: ''
};

// Datos simulados para la demo
const pedidosSimulados = [
    {
        id: 'PED-2025-001',
        cliente: 'Bodega Central',
        ruc: '20123456789',
        vendedor: 'Juan Pérez',
        vendedorCode: 'juan',
        monto: 8500,
        tiempo: '2h 15m',
        estado: 'urgente',
        productos: ['24x Coca Cola 500ml', '12x Inca Kola 1L', '+ 3 productos más'],
        credito: { usado: '30%', dias: '30', limite: 'S/ 10,000', score: '85/100' }
    },
    {
        id: 'PED-2025-002',
        cliente: 'Minimarket El Sol',
        ruc: '20987654321',
        vendedor: 'María García',
        vendedorCode: 'maria',
        monto: 3200,
        tiempo: '45m',
        estado: 'pendiente',
        productos: ['48x Agua San Luis 625ml', '24x Sprite 500ml'],
        credito: { usado: '64%', dias: '15', limite: 'S/ 5,000', score: '72/100' }
    },
    {
        id: 'PED-2025-003',
        cliente: 'Tienda Los Amigos',
        ruc: '20456789123',
        vendedor: 'Carlos López',
        vendedorCode: 'carlos',
        monto: 1850,
        tiempo: '15m',
        estado: 'normal',
        productos: ['36x Fanta 500ml'],
        credito: { usado: '37%', dias: '30', limite: 'S/ 5,000', score: '91/100' }
    },
    {
        id: 'PED-2025-004',
        cliente: 'Supermercado La Familia',
        ruc: '20123987456',
        vendedor: 'Ana Rodríguez',
        vendedorCode: 'ana',
        monto: 12750,
        tiempo: '1h 20m',
        estado: 'pendiente',
        productos: ['100x Coca Cola 500ml', '50x Inca Kola 1L', '+ 8 productos más'],
        credito: { usado: '85%', dias: '45', limite: 'S/ 15,000', score: '68/100' }
    },
    {
        id: 'PED-2025-005',
        cliente: 'Bazar San Miguel',
        ruc: '20789456123',
        vendedor: 'Roberto Silva',
        vendedorCode: 'roberto',
        monto: 2680,
        tiempo: '3h 45m',
        estado: 'pendiente',
        productos: ['24x Sprite 1L', '12x Fanta 2L'],
        credito: { usado: '54%', dias: '30', limite: 'S/ 5,000', score: '78/100' }
    },
    {
        id: 'PED-2025-006',
        cliente: 'Distribuidora Norte',
        ruc: '20654321987',
        vendedor: 'Luis Mendoza',
        vendedorCode: 'luis',
        monto: 6420,
        tiempo: '25m',
        estado: 'pendiente',
        productos: ['72x Coca Cola 500ml', '24x Agua San Luis 625ml', '+ 2 productos más'],
        credito: { usado: '43%', dias: '30', limite: 'S/ 15,000', score: '88/100' }
    }
];

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    pedidosData = [...pedidosSimulados];
    cargarPedidos();
    actualizarContadores();
    
    // Configurar eventos de teclado
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            cerrarModal();
        }
    });
    
    // Notificación de bienvenida
    setTimeout(() => {
        mostrarNotificacion('Sistema conectado - Datos simulados para demo', 'success');
    }, 1000);
});

// Función para cargar y mostrar pedidos
function cargarPedidos() {
    const container = document.getElementById('pedidos-container');
    container.innerHTML = '';
    
    pedidosData.forEach(pedido => {
        const pedidoCard = crearTarjetaPedido(pedido);
        container.appendChild(pedidoCard);
    });
}

// Crear tarjeta de pedido
function crearTarjetaPedido(pedido) {
    const card = document.createElement('div');
    card.className = `pedido-card ${pedido.estado}`;
    card.draggable = true;
    card.dataset.pedidoId = pedido.id;
    card.dataset.monto = pedido.monto;
    card.dataset.vendedor = pedido.vendedorCode;
    card.dataset.cliente = pedido.cliente;
    
    card.addEventListener('dragstart', drag);
    
    card.innerHTML = `
        <div class="card-header">
            <span class="pedido-id">#${pedido.id}</span>
            <span class="tiempo">${pedido.tiempo}</span>
        </div>
        <div class="cliente-info">
            <h4>${pedido.cliente}</h4>
            <p>RUC: ${pedido.ruc}</p>
            <p>Vendedor: ${pedido.vendedor}</p>
        </div>
        <div class="monto">
            <div class="total">S/ ${pedido.monto.toLocaleString()}</div>
        </div>
        <div class="productos">
            ${pedido.productos.map(prod => `<div class="producto-item">${prod}</div>`).join('')}
        </div>
        <div class="credito-info">
            <div class="credito-item">
                <span class="credito-label">Crédito usado:</span>
                <span class="credito-value">${pedido.credito.usado}</span>
            </div>
            <div class="credito-item">
                <span class="credito-label">Días:</span>
                <span class="credito-value">${pedido.credito.dias}</span>
            </div>
            <div class="credito-item">
                <span class="credito-label">Límite:</span>
                <span class="credito-value">${pedido.credito.limite}</span>
            </div>
            <div class="credito-item">
                <span class="credito-label">Score:</span>
                <span class="credito-value">${pedido.credito.score}</span>
            </div>
        </div>
        <div class="card-actions">
            <button class="btn-evaluar" onclick="abrirEvaluacion('${pedido.id}')">Evaluar Pedido</button>
            <button class="btn-rechazar" onclick="rechazarPedido('${pedido.id}')">✕</button>
        </div>
    `;
    
    return card;
}

// Función de logout mejorada
async function logout() {
    if (confirm('¿Estás seguro de que quieres cerrar sesión?')) {
        try {
            // Simular llamada al backend
            await new Promise(resolve => setTimeout(resolve, 500));
            
            localStorage.removeItem('token');
            localStorage.removeItem('user_data');
            mostrarNotificacion('Sesión cerrada correctamente', 'success');
            
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } catch (error) {
            console.error('Error en logout:', error);
            window.location.href = '/';
        }
    }
}

// Sistema de notificaciones
function mostrarNotificacion(mensaje, tipo = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = mensaje;
    notification.className = `notification ${tipo}`;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Búsqueda y filtrado
function filtrarPedidos() {
    const busqueda = document.querySelector('.search-input').value.toLowerCase();
    const estado = document.querySelector('.filter-select').value;
    const monto = document.querySelectorAll('.filter-select')[1].value;
    const vendedor = document.querySelectorAll('.filter-select')[2].value;
    
    filtrosActivos = { estado, monto, vendedor, busqueda };
    
    const pedidos = document.querySelectorAll('.pedido-card');
    let pedidosVisibles = 0;
    
    pedidos.forEach(pedido => {
        let mostrar = true;
        
        // Filtro por búsqueda
        if (busqueda) {
            const texto = pedido.textContent.toLowerCase();
            mostrar = mostrar && texto.includes(busqueda);
        }
        
        // Filtro por estado
        if (estado !== 'todos') {
            mostrar = mostrar && pedido.classList.contains(estado);
        }
        
        // Filtro por monto
        if (monto !== 'todos') {
            const montoValor = parseInt(pedido.dataset.monto);
            switch (monto) {
                case 'bajo':
                    mostrar = mostrar && montoValor < 1000;
                    break;
                case 'medio':
                    mostrar = mostrar && montoValor >= 1000 && montoValor <= 5000;
                    break;
                case 'alto':
                    mostrar = mostrar && montoValor > 5000;
                    break;
            }
        }
        
        // Filtro por vendedor
        if (vendedor !== 'todos') {
            mostrar = mostrar && pedido.dataset.vendedor === vendedor;
        }
        
        pedido.style.display = mostrar ? 'block' : 'none';
        if (mostrar) pedidosVisibles++;
    });
    
    // Actualizar mensaje de paginación
    const paginationSpan = document.querySelector('.pagination span');
    if (paginationSpan) {
        paginationSpan.textContent = `Mostrando ${pedidosVisibles} de ${pedidos.length} pedidos`;
    }
    
    actualizarContadores();
}

// Ordenamiento
function ordenarPedidos() {
    const criterio = document.querySelectorAll('.filter-select')[3].value;
    const container = document.getElementById('pedidos-container');
    const pedidos = Array.from(container.children);
    
    pedidos.sort((a, b) => {
        switch (criterio) {
            case 'monto':
                return parseInt(b.dataset.monto) - parseInt(a.dataset.monto);
            case 'prioridad':
                const prioridades = { urgente: 3, pendiente: 2, normal: 1 };
                const prioridadA = prioridades[a.className.split(' ')[1]] || 0;
                const prioridadB = prioridades[b.className.split(' ')[1]] || 0;
                return prioridadB - prioridadA;
            case 'cliente':
                return a.dataset.cliente.localeCompare(b.dataset.cliente);
            default: // tiempo
                return a.querySelector('.tiempo').textContent.localeCompare(b.querySelector('.tiempo').textContent);
        }
    });
    
    pedidos.forEach(pedido => container.appendChild(pedido));
    mostrarNotificacion(`Pedidos ordenados por ${criterio}`, 'success');
}

// Drag and Drop
function allowDrop(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.add('drag-over');
}

function drag(ev) {
    ev.dataTransfer.setData("text", ev.target.dataset.pedidoId);
}

function drop(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.remove('drag-over');
    const pedidoId = ev.dataTransfer.getData("text");
    mostrarNotificacion(`Pedido ${pedidoId} reorganizado`, 'success');
}

// Modal de evaluación
function abrirEvaluacion(pedidoId) {
    const pedido = pedidosData.find(p => p.id === pedidoId);
    if (!pedido) return;
    
    document.getElementById('modal-pedido-id').textContent = pedidoId;
    
    // Prellenar datos del pedido
    const scoreValue = parseInt(pedido.credito.score.split('/')[0]);
    const utilizacionValue = parseInt(pedido.credito.usado.replace('%', ''));
    
    // Actualizar indicadores de riesgo
    actualizarIndicadoresRiesgo(scoreValue, utilizacionValue);
    
    document.getElementById('modal-evaluacion').classList.add('show');
}

function actualizarIndicadoresRiesgo(score, utilizacion) {
    const riskCards = document.querySelectorAll('.risk-card');
    
    // Actualizar score crediticio
    const scoreCard = riskCards[0];
    scoreCard.querySelector('div[style*="font-size"]').textContent = `${score}/100`;
    scoreCard.className = `risk-card ${score >= 80 ? 'low' : score >= 60 ? 'medium' : 'high'}`;
    scoreCard.querySelector('small').textContent = score >= 80 ? 'Riesgo Bajo' : score >= 60 ? 'Riesgo Medio' : 'Riesgo Alto';
    
    // Actualizar utilización
    const utilizacionCard = riskCards[1];
    utilizacionCard.querySelector('div[style*="font-size"]').textContent = `${utilizacion}%`;
    utilizacionCard.className = `risk-card ${utilizacion <= 50 ? 'low' : utilizacion <= 75 ? 'medium' : 'high'}`;
    utilizacionCard.querySelector('small').textContent = utilizacion <= 50 ? 'Uso Bajo' : utilizacion <= 75 ? 'Uso Moderado' : 'Uso Alto';
}

function cerrarModal() {
    document.getElementById('modal-evaluacion').classList.remove('show');
}

function guardarEvaluacion() {
    const pedidoId = document.getElementById('modal-pedido-id').textContent;
    const decision = document.getElementById('decision-evaluacion').value;
    const limite = document.getElementById('limite-credito').value;
    const dias = document.getElementById('dias-credito').value;
    const comentarios = document.getElementById('comentarios').value;
    
    // Validaciones
    if (!limite || limite <= 0) {
        mostrarNotificacion('El límite de crédito debe ser mayor a 0', 'error');
        return;
    }
    
    // Simular guardado
    const loadingMsg = mostrarNotificacion('Guardando evaluación...', 'success');
    
    setTimeout(() => {
        const decisionTexto = {
            'aprobado': 'aprobado',
            'condicional': 'aprobado con condiciones', 
            'rechazado': 'rechazado'
        }[decision];
        
        mostrarNotificacion(`Evaluación de ${pedidoId} guardada: ${decisionTexto}`, 'success');
        cerrarModal();
        
        // Remover pedido del dashboard con animación
        const pedidoCard = document.querySelector(`[data-pedido-id="${pedidoId}"]`);
        if (pedidoCard) {
            pedidoCard.style.transition = 'all 0.5s ease';
            pedidoCard.style.transform = 'scale(0)';
            pedidoCard.style.opacity = '0';
            setTimeout(() => {
                pedidoCard.remove();
                // Remover del array de datos
                pedidosData = pedidosData.filter(p => p.id !== pedidoId);
                actualizarContadores();
            }, 500);
        }
        
        // Limpiar formulario
        document.getElementById('comentarios').value = '';
        document.getElementById('limite-credito').value = '10000';
        document.getElementById('dias-credito').value = '30';
        document.getElementById('decision-evaluacion').value = 'aprobado';
        
    }, 1500);
}

function rechazarPedido(pedidoId) {
    if (confirm(`¿Estás seguro de rechazar el pedido ${pedidoId}?`)) {
        mostrarNotificacion(`Pedido ${pedidoId} rechazado`, 'error');
        
        const pedidoCard = document.querySelector(`[data-pedido-id="${pedidoId}"]`);
        if (pedidoCard) {
            pedidoCard.style.transition = 'all 0.5s ease';
            pedidoCard.style.transform = 'scale(0)';
            pedidoCard.style.opacity = '0';
            setTimeout(() => {
                pedidoCard.remove();
                pedidosData = pedidosData.filter(p => p.id !== pedidoId);
                actualizarContadores();
            }, 500);
        }
    }
}

// Actualizar contadores
function actualizarContadores() {
    const totalPedidos = document.querySelectorAll('.pedido-card').length;
    const pedidosUrgentes = document.querySelectorAll('.pedido-card.urgente').length;
    
    // Actualizar estadísticas en el header
    const statNumbers = document.querySelectorAll('.stat-number');
    if (statNumbers.length >= 3) {
        statNumbers[0].textContent = totalPedidos; // Pendientes
        statNumbers[1].textContent = Math.max(0, 15 - totalPedidos); // Evaluados hoy (simulado)
        // El porcentaje de aprobación se mantiene estático para la demo
    }
}

// Actualización automática
function actualizarPedidos() {
    mostrarNotificacion('Actualizando pedidos...', 'success');
    
    setTimeout(() => {
        // Simular actualización - en producción aquí iría la llamada al API
        mostrarNotificacion('Pedidos actualizados', 'success');
        
        // Simular nuevos pedidos urgentes ocasionalmente
        if (Math.random() > 0.8) {
            agregarNuevoPedidoSimulado();
            mostrarNotificacion('¡Nuevo pedido urgente recibido!', 'warning');
        }
    }, 1000);
}

// Agregar nuevo pedido simulado
function agregarNuevoPedidoSimulado() {
    const nuevoId = `PED-2025-${String(Date.now()).slice(-3)}`;
    const clientesRandom = ['Bodega Express', 'Market Central', 'Tienda Real', 'Distribuidora Sur'];
    const vendedoresRandom = [
        { nombre: 'Juan Pérez', code: 'juan' },
        { nombre: 'María García', code: 'maria' },
        { nombre: 'Carlos López', code: 'carlos' }
    ];
    
    const vendedorRandom = vendedoresRandom[Math.floor(Math.random() * vendedoresRandom.length)];
    const clienteRandom = clientesRandom[Math.floor(Math.random() * clientesRandom.length)];
    
    const nuevoPedido = {
        id: nuevoId,
        cliente: clienteRandom,
        ruc: `201${Math.floor(Math.random() * 99999999)}`,
        vendedor: vendedorRandom.nombre,
        vendedorCode: vendedorRandom.code,
        monto: Math.floor(Math.random() * 10000) + 1000,
        tiempo: '5m',
        estado: Math.random() > 0.7 ? 'urgente' : 'pendiente',
        productos: ['24x Producto Nuevo'],
        credito: { 
            usado: `${Math.floor(Math.random() * 80)}%`, 
            dias: '30', 
            limite: 'S/ 5,000', 
            score: `${Math.floor(Math.random() * 40) + 60}/100` 
        }
    };
    
    pedidosData.unshift(nuevoPedido);
    const container = document.getElementById('pedidos-container');
    const nuevaCard = crearTarjetaPedido(nuevoPedido);
    
    // Insertar al inicio con animación
    nuevaCard.style.transform = 'scale(0)';
    nuevaCard.style.opacity = '0';
    container.insertBefore(nuevaCard, container.firstChild);
    
    setTimeout(() => {
        nuevaCard.style.transition = 'all 0.5s ease';
        nuevaCard.style.transform = 'scale(1)';
        nuevaCard.style.opacity = '1';
    }, 100);
    
    actualizarContadores();
}

// Auto-actualización cada 30 segundos
setInterval(actualizarPedidos, 30000);

// Actualizar tiempos cada minuto (simulado)
setInterval(() => {
    document.querySelectorAll('.tiempo').forEach(tiempo => {
        // En producción aquí se actualizarían los tiempos reales
        // Por ahora solo agregamos un indicador visual sutil
        tiempo.style.animation = 'none';
        setTimeout(() => {
            tiempo.style.animation = 'pulse 0.5s ease';
        }, 10);
    });
}, 60000);