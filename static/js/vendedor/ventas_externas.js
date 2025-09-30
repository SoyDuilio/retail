// Estado global de la aplicación
const estadoApp = {
    token: localStorage.getItem('auth_token'),
    vendedor: null,
    ubicacion: null,
    clienteSeleccionado: null,
    pedido: [],
    productosSeleccionados: new Set(), // Para checkboxes de productos
    recognitionCliente: null,
    recognitionProductos: null,
    isRecordingCliente: false,
    isRecordingProductos: false
};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    verificarAutenticacion();
    cargarDatosVendedor();
    inicializarReconocimientoVoz();
    configurarEventListeners();
});

// Verificar autenticación
function verificarAutenticacion() {
    // TODO: Verificar correctamente la autenticación cuando sepamos cómo funciona
    // Temporalmente deshabilitado para poder ver la página
    
    /* DESCOMENTAR CUANDO SE ARREGLE:
    if (!estadoApp.token) {
        window.location.href = '/';
        return;
    }
    */
   
    // Por ahora solo verificamos si existe, sin redirigir
    if (!estadoApp.token) {
        console.warn('No hay token de autenticación');
    }
}

// Cargar datos del vendedor
async function cargarDatosVendedor() {
    try {
        // Obtener datos del localStorage que guarda el login
        const userDataStr = localStorage.getItem('user_data');
        
        if (userDataStr) {
            const userData = JSON.parse(userDataStr);
            estadoApp.vendedor = {
                id: userData.id,
                nombre: userData.nombre,
                tipo: userData.tipo,
                codigo: userData.id
            };
            
            document.getElementById('vendedorNombre').textContent = userData.nombre;
            document.getElementById('vendedorCodigo').textContent = `ID: ${userData.id}`;
        } else {
            // Si no hay datos, valores por defecto
            document.getElementById('vendedorNombre').textContent = 'Vendedor';
            document.getElementById('vendedorCodigo').textContent = 'Sistema';
        }
        
        cargarEstadisticas();
        
    } catch (error) {
        console.error('Error cargando datos:', error);
        document.getElementById('vendedorNombre').textContent = 'Vendedor';
        document.getElementById('vendedorCodigo').textContent = 'Sistema';
    }
}

// Cargar estadísticas
async function cargarEstadisticas() {
    try {
        // TODO: Crear endpoint /api/vendedor/estadisticas/hoy en el backend
        // Temporalmente usar valores por defecto
        document.getElementById('pedidosHoy').textContent = '0';
        document.getElementById('ventasHoy').textContent = 'S/0';
        
        /* ENDPOINT QUE FALTA - Descomentar cuando esté creado:
        const response = await fetch('/api/vendedor/estadisticas/hoy', {
            headers: { 'Authorization': `Bearer ${estadoApp.token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            document.getElementById('pedidosHoy').textContent = data.pedidos || 0;
            document.getElementById('ventasHoy').textContent = `S/${(data.ventas || 0).toFixed(0)}`;
        }
        */
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
}

// Configurar event listeners
function configurarEventListeners() {
    const inputCliente = document.getElementById('inputBusquedaCliente');
    const inputProductos = document.getElementById('inputProductos');
    
    // Búsqueda de cliente en tiempo real
    let timeoutCliente;
    inputCliente.addEventListener('input', function() {
        clearTimeout(timeoutCliente);
        const query = this.value.trim();
        
        if (query.length >= 3) {
            timeoutCliente = setTimeout(() => buscarCliente(query), 300);
        } else {
            ocultarDropdownClientes();
        }
    });
    
    // Búsqueda de productos en tiempo real
    let timeoutProductos;
    inputProductos.addEventListener('input', function() {
        clearTimeout(timeoutProductos);
        const query = this.value.trim();
        
        if (query.length >= 3) {
            timeoutProductos = setTimeout(() => buscarProductos(query), 300);
        } else {
            ocultarDropdownProductos();
        }
    });
    
    // Validación RUC en tiempo real
    const inputRuc = document.getElementById('nuevoRuc');
    if (inputRuc) {
        let timeoutRuc;
        inputRuc.addEventListener('input', function() {
            clearTimeout(timeoutRuc);
            const ruc = this.value.trim();
            
            if (ruc.length === 11 && /^\d+$/.test(ruc)) {
                timeoutRuc = setTimeout(() => validarRuc(ruc), 500);
            }
        });
    }
}

// Inicializar reconocimiento de voz
function inicializarReconocimientoVoz() {
    if (!('webkitSpeechRecognition' in window)) {
        console.log('Reconocimiento de voz no disponible');
        return;
    }
    
    // Para búsqueda de cliente
    estadoApp.recognitionCliente = new webkitSpeechRecognition();
    estadoApp.recognitionCliente.continuous = false;
    estadoApp.recognitionCliente.interimResults = false;
    estadoApp.recognitionCliente.lang = 'es-PE';
    
    estadoApp.recognitionCliente.onresult = function(event) {
        const texto = event.results[0][0].transcript;
        document.getElementById('inputBusquedaCliente').value = texto;
        buscarCliente(texto);
    };
    
    estadoApp.recognitionCliente.onend = function() {
        estadoApp.isRecordingCliente = false;
        document.getElementById('micCliente').classList.remove('recording');
    };
    
    // Para productos
    estadoApp.recognitionProductos = new webkitSpeechRecognition();
    estadoApp.recognitionProductos.continuous = false;
    estadoApp.recognitionProductos.interimResults = false;
    estadoApp.recognitionProductos.lang = 'es-PE';
    
    estadoApp.recognitionProductos.onresult = function(event) {
        const texto = event.results[0][0].transcript;
        document.getElementById('inputProductos').value = texto;
        procesarPedidoTexto(texto);
    };
    
    estadoApp.recognitionProductos.onend = function() {
        estadoApp.isRecordingProductos = false;
        document.getElementById('micProductos').classList.remove('recording');
    };
}

// Dictado para cliente
function iniciarDictadoCliente() {
    if (!estadoApp.recognitionCliente) return;
    
    if (estadoApp.isRecordingCliente) {
        estadoApp.recognitionCliente.stop();
    } else {
        estadoApp.recognitionCliente.start();
        estadoApp.isRecordingCliente = true;
        document.getElementById('micCliente').classList.add('recording');
    }
}

// Dictado para productos
function iniciarDictadoProductos() {
    if (!estadoApp.recognitionProductos || !estadoApp.clienteSeleccionado) return;
    
    if (estadoApp.isRecordingProductos) {
        estadoApp.recognitionProductos.stop();
    } else {
        estadoApp.recognitionProductos.start();
        estadoApp.isRecordingProductos = true;
        document.getElementById('micProductos').classList.add('recording');
    }
}

// GESTIÓN DE UBICACIÓN
async function solicitarUbicacion() {
    if (!navigator.geolocation) {
        alert('Tu navegador no soporta geolocalización');
        return;
    }
    
    try {
        const position = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            });
        });
        
        estadoApp.ubicacion = {
            latitud: position.coords.latitude,
            longitud: position.coords.longitude,
            precision: position.coords.accuracy,
            timestamp: new Date().toISOString()
        };
        
        actualizarEstadoUbicacion();
        cerrarModal('modalUbicacion');
        
        // Guardar en servidor
        await guardarUbicacion(estadoApp.ubicacion);
        
    } catch (error) {
        alert('No se pudo obtener la ubicación. Por favor, permite el acceso en tu navegador.');
    }
}

function actualizarEstadoUbicacion() {
    const btnUbicacion = document.getElementById('btnUbicacion');
    const estadoTexto = document.getElementById('estadoUbicacion');
    
    if (estadoApp.ubicacion) {
        btnUbicacion.classList.add('activo');
        estadoTexto.textContent = 'Ubicación OK';
    } else {
        btnUbicacion.classList.remove('activo');
        btnUbicacion.classList.add('alerta');
        estadoTexto.textContent = 'Sin ubicación';
    }
}

async function guardarUbicacion(ubicacion) {
    try {
        await fetch('/api/vendedor/ubicacion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${estadoApp.token}`
            },
            body: JSON.stringify(ubicacion)
        });
    } catch (error) {
        console.error('Error guardando ubicación:', error);
    }
}

function mostrarModalUbicacion() {
    const modal = document.getElementById('modalUbicacion');
    const contenido = document.getElementById('contenidoUbicacion');
    
    if (estadoApp.ubicacion) {
        let html = `
            <div style="padding: 16px; background: rgba(34, 197, 94, 0.1); border-radius: 8px; margin-bottom: 12px;">
                <p style="color: #22c55e; font-weight: 600; margin-bottom: 8px;">✓ Ubicación compartida</p>
                <p style="font-size: 13px; color: #93c5fd;">Latitud: ${estadoApp.ubicacion.latitud.toFixed(6)}</p>
                <p style="font-size: 13px; color: #93c5fd;">Longitud: ${estadoApp.ubicacion.longitud.toFixed(6)}</p>
                <p style="font-size: 12px; color: #6b7280; margin-top: 8px;">Precisión: ±${Math.round(estadoApp.ubicacion.precision)}m</p>
            </div>
        `;
        
        // Si hay cliente seleccionado con coordenadas, mostrar comparación
        if (estadoApp.clienteSeleccionado && estadoApp.clienteSeleccionado.latitud) {
            const distancia = calcularDistancia(
                estadoApp.ubicacion.latitud,
                estadoApp.ubicacion.longitud,
                estadoApp.clienteSeleccionado.latitud,
                estadoApp.clienteSeleccionado.longitud
            );
            
            const porcentaje = calcularPorcentajeCoincidencia(distancia);
            const clase = porcentaje >= 80 ? 'alta' : porcentaje >= 50 ? 'media' : 'baja';
            
            html += `
                <div class="alert-coincidencia ${clase}">
                    <p style="font-weight: 600; margin-bottom: 4px;">Comparación con bodega</p>
                    <p style="font-size: 13px;">Distancia: ${distancia.toFixed(0)}m</p>
                    <p style="font-size: 13px;">Coincidencia: ${porcentaje}%</p>
                </div>
            `;
        }
        
        html += `<button class="btn-compartir-ubicacion" onclick="solicitarUbicacion()">Actualizar Ubicación</button>`;
        contenido.innerHTML = html;
    } else {
        contenido.innerHTML = `<button class="btn-compartir-ubicacion" onclick="solicitarUbicacion()">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
            </svg>
            Compartir Ubicación
        </button>`;
    }
    
    modal.classList.remove('hidden');
}

// Calcular distancia entre dos puntos (fórmula de Haversine)
function calcularDistancia(lat1, lon1, lat2, lon2) {
    const R = 6371e3; // Radio de la Tierra en metros
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;

    const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ/2) * Math.sin(Δλ/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    return R * c; // Distancia en metros
}

// Calcular porcentaje de coincidencia (0-100%)
function calcularPorcentajeCoincidencia(distanciaMetros) {
    const MAX_DISTANCIA = 20; // 20 metros como máximo válido
    if (distanciaMetros <= MAX_DISTANCIA) {
        return Math.round((1 - distanciaMetros / MAX_DISTANCIA) * 100);
    }
    return 0;
}

// BÚSQUEDA DE CLIENTES
async function buscarCliente(query) {
    try {
        // Tu endpoint espera el parámetro 'q'
        const url = `/api/clientes/buscar?q=${encodeURIComponent(query)}`;
        
        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${estadoApp.token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            // Adaptar según la estructura de tu respuesta
            const clientes = data.clientes || data.data || [data];
            mostrarResultadosClientes(clientes);
        } else {
            console.error('Error en búsqueda:', response.status);
            ocultarDropdownClientes();
        }
    } catch (error) {
        console.error('Error buscando cliente:', error);
        ocultarDropdownClientes();
    }
}

function determinarTipoBusqueda(query) {
    const soloNumeros = /^\d+$/.test(query);
    
    if (soloNumeros) {
        if (query.length === 11) return 'ruc';
        if (query.length === 9) return 'whatsapp';
    }
    return 'nombre';
}

function mostrarResultadosClientes(clientes) {
    const dropdown = document.getElementById('dropdownClientes');
    
    if (!clientes || clientes.length === 0) {
        dropdown.innerHTML = '<div class="empty-state">No se encontraron clientes</div>';
        dropdown.classList.remove('hidden');
        return;
    }
    
    const html = clientes.map(cliente => {
        // Usar estructura REAL de la tabla
        const nombre = cliente.nombre_comercial || cliente.razon_social || `Cliente RUC ${cliente.ruc}`;
        const ruc = cliente.ruc || 'N/D';
        const tipo = cliente.tipo_cliente?.nombre || 'Cliente';
        const direccion = cliente.distrito || cliente.direccion || '';
        const id = cliente.id;
        
        // Guardar cliente en memoria temporal
        window['cliente_' + id] = cliente;
        
        return `
            <div class="resultado-cliente" onclick='seleccionarClienteTemp(${id})'>
                <div class="resultado-cliente-nombre">${nombre}</div>
                <div class="resultado-cliente-info">
                    <span>RUC: ${ruc}</span>
                    <span class="resultado-cliente-tag">${tipo}</span>
                </div>
                ${direccion ? `<div style="font-size: 11px; color: #6b7280; margin-top: 4px;">${direccion}</div>` : ''}
            </div>
        `;
    }).join('');
    
    dropdown.innerHTML = html;
    dropdown.classList.remove('hidden');
}

// Función auxiliar para seleccionar desde el objeto temporal
function seleccionarClienteTemp(clienteId) {
    const cliente = window['cliente_' + clienteId];
    if (cliente) {
        seleccionarCliente(cliente);
        // Limpiar referencia temporal
        delete window['cliente_' + clienteId];
    }
}

function ocultarDropdownClientes() {
    document.getElementById('dropdownClientes').classList.add('hidden');
}

function seleccionarCliente(cliente) {
    // Usar estructura REAL de la base de datos
    const clienteNormalizado = {
        id: cliente.id,
        codigo_cliente: cliente.codigo_cliente || '',
        nombre_comercial: cliente.nombre_comercial || '',
        razon_social: cliente.razon_social || '',
        ruc: cliente.ruc || '',
        telefono: cliente.telefono || '',
        email: cliente.email || '',
        direccion: cliente.direccion || cliente.direccion_completa || '',
        distrito: cliente.distrito || '',
        provincia: cliente.provincia || '',
        departamento: cliente.departamento || '',
        latitud: cliente.latitud || null,
        longitud: cliente.longitud || null,
        tipo_cliente_id: cliente.tipo_cliente_id,
        tipo_cliente_nombre: cliente.tipo_cliente?.nombre || 'Cliente',
        // Nombre para mostrar
        nombre_completo: cliente.nombre_comercial || cliente.razon_social || `Cliente RUC ${cliente.ruc}`
    };
    
    estadoApp.clienteSeleccionado = clienteNormalizado;
    
    // Actualizar UI
    document.getElementById('inputBusquedaCliente').value = '';
    ocultarDropdownClientes();
    
    // Mostrar chip en header
    const chip = document.getElementById('chipCliente');
    document.getElementById('chipClienteNombre').textContent = clienteNormalizado.nombre_completo;
    document.getElementById('chipClienteTipo').textContent = clienteNormalizado.tipo_cliente_nombre;
    chip.classList.remove('hidden');
    
    // Compactar sección de búsqueda
    document.getElementById('seccionBusquedaCliente').classList.add('compacta');
    
    // Habilitar input de productos
    const inputProductos = document.getElementById('inputProductos');
    const micProductos = document.getElementById('micProductos');
    inputProductos.disabled = false;
    micProductos.disabled = false;
    inputProductos.focus();
    
    // Verificar si necesitamos ubicación
    if (!estadoApp.ubicacion) {
        setTimeout(() => {
            //alert('Por favor, comparte tu ubicación para continuar');
            mostrarModalUbicacion();
        }, 500);
    }
}

function cambiarCliente() {
    if (estadoApp.pedido.length > 0) {
        if (!confirm('¿Deseas cambiar de cliente? Se perderá el pedido actual.')) {
            return;
        }
    }
    
    estadoApp.clienteSeleccionado = null;
    estadoApp.pedido = [];
    
    // Ocultar chip
    document.getElementById('chipCliente').classList.add('hidden');
    
    // Expandir sección de búsqueda
    document.getElementById('seccionBusquedaCliente').classList.remove('compacta');
    
    // Deshabilitar productos
    const inputProductos = document.getElementById('inputProductos');
    const micProductos = document.getElementById('micProductos');
    inputProductos.disabled = true;
    micProductos.disabled = true;
    inputProductos.value = '';
    
    // Limpiar productos
    document.getElementById('productosContainer').classList.add('hidden');
    
    // Focus en búsqueda de cliente
    document.getElementById('inputBusquedaCliente').focus();
}

// BÚSQUEDA DE PRODUCTOS
async function buscarProductos(query) {
    try {
        const url = `/api/productos/buscar?q=${encodeURIComponent(query)}`;
        
        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${estadoApp.token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            const productos = data.data || [];
            mostrarResultadosProductos(productos);
        } else {
            console.error('Error en búsqueda:', response.status);
            ocultarDropdownProductos();
        }
    } catch (error) {
        console.error('Error buscando productos:', error);
        ocultarDropdownProductos();
    }
}

function mostrarResultadosProductos(productos) {
    const dropdown = document.getElementById('dropdownProductos');
    const lista = document.getElementById('listaProductosDropdown');
    
    if (!productos || productos.length === 0) {
        dropdown.classList.add('hidden');
        return;
    }
    
    const html = productos.map(producto => {
        const estaSeleccionado = estadoApp.productosSeleccionados.has(producto.id);
        const estaEnPedido = estadoApp.pedido.some(item => item.producto_id === producto.id);
        
        // Guardar en memoria temporal
        window['prod_' + producto.id] = producto;
        
        return `
            <div class="item-producto-dropdown ${estaSeleccionado ? 'seleccionado' : ''} ${estaEnPedido ? 'en-pedido' : ''}" 
                 onclick="${estaEnPedido ? '' : `toggleSeleccionProducto(${producto.id})`}">
                <input 
                    type="checkbox" 
                    class="producto-checkbox"
                    ${estaSeleccionado ? 'checked' : ''}
                    ${estaEnPedido ? 'disabled' : ''}
                    onclick="event.stopPropagation()"
                    onchange="toggleSeleccionProducto(${producto.id})"
                />
                <div class="producto-dropdown-info">
                    <div class="producto-dropdown-nombre">${producto.nombre}</div>
                    <div class="producto-dropdown-detalles">
                        <span>Código: ${producto.codigo_producto}</span>
                        ${producto.categoria ? `<span>• ${producto.categoria}</span>` : ''}
                    </div>
                    ${estaEnPedido ? '<div class="producto-ya-agregado">Ya está en el pedido</div>' : ''}
                </div>
                <div class="producto-dropdown-precio">
                    S/ ${parseFloat(producto.precio_unitario).toFixed(2)}
                </div>
            </div>
        `;
    }).join('');
    
    lista.innerHTML = html;
    actualizarContadorSeleccionados();
    dropdown.classList.remove('hidden');
}

function ocultarDropdownProductos() {
    document.getElementById('dropdownProductos').classList.add('hidden');
    estadoApp.productosSeleccionados.clear();
    actualizarContadorSeleccionados();
}

function toggleSeleccionProducto(productoId) {
    // Verificar si ya está en el pedido
    if (estadoApp.pedido.some(item => item.producto_id === productoId)) {
        return;
    }
    
    if (estadoApp.productosSeleccionados.has(productoId)) {
        estadoApp.productosSeleccionados.delete(productoId);
    } else {
        estadoApp.productosSeleccionados.add(productoId);
    }
    
    actualizarContadorSeleccionados();
    actualizarEstiloProductoDropdown(productoId);
}

function actualizarEstiloProductoDropdown(productoId) {
    const items = document.querySelectorAll('.item-producto-dropdown');
    items.forEach(item => {
        const checkbox = item.querySelector('.producto-checkbox');
        if (checkbox && !checkbox.disabled) {
            const estaSeleccionado = estadoApp.productosSeleccionados.has(productoId);
            if (item.querySelector(`input[onchange*="${productoId}"]`)) {
                if (estaSeleccionado) {
                    item.classList.add('seleccionado');
                } else {
                    item.classList.remove('seleccionado');
                }
            }
        }
    });
}

function actualizarContadorSeleccionados() {
    const count = estadoApp.productosSeleccionados.size;
    document.getElementById('countSeleccionados').textContent = `${count} seleccionado${count !== 1 ? 's' : ''}`;
    
    const btnAgregar = document.getElementById('btnAgregarProductos');
    if (count > 0) {
        btnAgregar.classList.remove('hidden');
    } else {
        btnAgregar.classList.add('hidden');
    }
}

function agregarProductosSeleccionados() {
    const nuevosItems = [];
    
    estadoApp.productosSeleccionados.forEach(prodId => {
        const producto = window['prod_' + prodId];
        if (producto && !estadoApp.pedido.find(item => item.producto_id === prodId)) {
            nuevosItems.push({
                producto_id: producto.id,
                codigo_producto: producto.codigo_producto,
                nombre: producto.nombre,
                cantidad: 1,
                unidad: 'unidad', // Ajustar según tu lógica
                precio_unitario: parseFloat(producto.precio_unitario),
                subtotal: parseFloat(producto.precio_unitario)
            });
        }
    });
    
    if (nuevosItems.length > 0) {
        estadoApp.pedido.push(...nuevosItems);
        estadoApp.productosSeleccionados.clear();
        document.getElementById('inputProductos').value = '';
        ocultarDropdownProductos();
        mostrarProductosPedido();
    }
}

// Eliminar función handleEnterProductos ya que ahora es búsqueda en tiempo real
function handleEnterProductos(event) {
    // Mantener por compatibilidad pero ya no se usa
}

async function procesarPedidoTexto(texto) {
    if (!estadoApp.clienteSeleccionado) {
        alert('Primero selecciona un cliente');
        return;
    }
    
    if (!estadoApp.ubicacion) {
        alert('Primero comparte tu ubicación');
        mostrarModalUbicacion();
        return;
    }
    
    document.getElementById('procesandoProductos').classList.remove('hidden');
    
    try {
        const response = await fetch('/api/pedidos/procesar-texto', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${estadoApp.token}`
            },
            body: JSON.stringify({
                texto: texto,
                es_voz: false
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.data && data.data.length > 0) {
            // Convertir los productos detectados al formato del pedido
            const productosParaPedido = data.data
                .filter(p => p.encontrado) // Solo productos encontrados en BD
                .map(p => ({
                    producto_id: p.producto_id,
                    codigo_producto: p.codigo_producto || 'N/D',
                    nombre: p.nombre,
                    cantidad: p.cantidad,
                    unidad: p.unidad,
                    precio_unitario: p.precio_unitario,
                    subtotal: p.precio_total
                }));
            
            if (productosParaPedido.length > 0) {
                actualizarItemsDelPedido(productosParaPedido);
            } else {
                alert('No se encontraron productos en la base de datos');
            }
            
            // Mostrar productos no encontrados
            const noEncontrados = data.data.filter(p => !p.encontrado);
            if (noEncontrados.length > 0) {
                console.warn('Productos no encontrados:', noEncontrados.map(p => p.nombre));
            }
        } else {
            alert(data.message || 'No se pudieron identificar productos');
        }
    } catch (error) {
        console.error('Error procesando pedido:', error);
        alert('Error procesando pedido');
    } finally {
        document.getElementById('procesandoProductos').classList.add('hidden');
    }
}

function actualizarItemsDelPedido(nuevosProductos) {
    nuevosProductos.forEach(producto => {
        const index = estadoApp.pedido.findIndex(item => item.producto_id === producto.producto_id);
        
        if (index >= 0) {
            // Actualizar cantidad si ya existe
            estadoApp.pedido[index].cantidad += producto.cantidad;
            estadoApp.pedido[index].subtotal = estadoApp.pedido[index].cantidad * estadoApp.pedido[index].precio_unitario;
        } else {
            // Agregar nuevo producto
            estadoApp.pedido.push(producto);
        }
    });
    
    mostrarProductosPedido();
}

function mostrarProductosPedido() {
    const container = document.getElementById('productosContainer');
    const lista = document.getElementById('listaProductos');
    
    if (estadoApp.pedido.length === 0) {
        container.classList.add('hidden');
        return;
    }
    
    const html = estadoApp.pedido.map(producto => `
        <div class="item-producto" id="prod-${producto.producto_id}">
            <div class="producto-info">
                <div class="producto-nombre">${producto.nombre}</div>
                <div class="producto-codigo">Código: ${producto.codigo_producto || 'N/D'}</div>
            </div>
            <div class="producto-controles">
                <div class="cantidad-control">
                    <button class="btn-cantidad" onclick="actualizarCantidad(${producto.producto_id}, ${producto.cantidad - 1})">
                        <svg class="icon-small" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"></path>
                        </svg>
                    </button>
                    <div class="cantidad-valor">
                        <div class="cantidad-numero">${producto.cantidad}</div>
                        <div class="cantidad-unidad">${producto.unidad}</div>
                    </div>
                    <button class="btn-cantidad" onclick="actualizarCantidad(${producto.producto_id}, ${producto.cantidad + 1})">
                        <svg class="icon-small" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                        </svg>
                    </button>
                </div>
                <div class="producto-precios">
                    <div class="precio-unitario">S/ ${producto.precio_unitario.toFixed(2)}</div>
                    <div class="precio-subtotal">S/ ${producto.subtotal.toFixed(2)}</div>
                </div>
                <button class="btn-eliminar" onclick="eliminarProducto(${producto.producto_id})">
                    <svg class="icon-small" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                </button>
            </div>
        </div>
    `).join('');
    
    lista.innerHTML = html;
    actualizarTotal();
    container.classList.remove('hidden');
}

function actualizarCantidad(productoId, nuevaCantidad) {
    if (nuevaCantidad < 1) return;
    
    const producto = estadoApp.pedido.find(p => p.producto_id === productoId);
    if (producto) {
        producto.cantidad = nuevaCantidad;
        producto.subtotal = producto.cantidad * producto.precio_unitario;
        mostrarProductosPedido();
    }
}

function eliminarProducto(productoId) {
    estadoApp.pedido = estadoApp.pedido.filter(p => p.producto_id !== productoId);
    mostrarProductosPedido();
}

function limpiarPedido() {
    if (confirm('¿Deseas limpiar todos los productos del pedido?')) {
        estadoApp.pedido = [];
        mostrarProductosPedido();
    }
}

function actualizarTotal() {
    const total = estadoApp.pedido.reduce((sum, p) => sum + p.subtotal, 0);
    document.getElementById('totalPedido').textContent = `S/ ${total.toFixed(2)}`;
}

// CONFIRMAR Y ENVIAR PEDIDO
function confirmarPedido() {
    if (estadoApp.pedido.length === 0) {
        alert('Agrega productos al pedido');
        return;
    }
    
    if (!estadoApp.ubicacion) {
        alert('Por favor, comparte tu ubicación');
        mostrarModalUbicacion();
        return;
    }
    
    // Calcular coincidencia de ubicación
    if (estadoApp.clienteSeleccionado.latitud && estadoApp.clienteSeleccionado.longitud) {
        const distancia = calcularDistancia(
            estadoApp.ubicacion.latitud,
            estadoApp.ubicacion.longitud,
            estadoApp.clienteSeleccionado.latitud,
            estadoApp.clienteSeleccionado.longitud
        );
        
        const porcentaje = calcularPorcentajeCoincidencia(distancia);
        const alertDiv = document.getElementById('alertCoincidencia');
        const clase = porcentaje >= 80 ? 'alta' : porcentaje >= 50 ? 'media' : 'baja';
        
        alertDiv.className = `alert-coincidencia ${clase}`;
        alertDiv.innerHTML = `
            <strong>Verificación de ubicación:</strong><br>
            Distancia a la bodega: ${distancia.toFixed(0)}m | Coincidencia: ${porcentaje}%
        `;
    }
    
    abrirModal('modalConfirmarPedido');
}

async function enviarPedidoFinal() {
    const modalidadPago = document.getElementById('modalidadPago').value;
    const observaciones = document.getElementById('observacionesPedido').value.trim();
    
    // Mapear modalidad de pago al enum correcto
    let tipoPago = "contado"; // valor por defecto
    if (modalidadPago.includes('credito')) {
        tipoPago = "credito";
    } else if (modalidadPago.includes('yape')) {
        tipoPago = "yape";
    } else if (modalidadPago.includes('plin')) {
        tipoPago = "plin";
    }
    
    // Calcular porcentaje de coincidencia
    let porcentajeCoincidencia = 0;
    if (estadoApp.clienteSeleccionado.latitud && estadoApp.clienteSeleccionado.longitud) {
        const distancia = calcularDistancia(
            estadoApp.ubicacion.latitud,
            estadoApp.ubicacion.longitud,
            estadoApp.clienteSeleccionado.latitud,
            estadoApp.clienteSeleccionado.longitud
        );
        porcentajeCoincidencia = calcularPorcentajeCoincidencia(distancia);
    }
    
    // Estructura según tu PedidoCreate schema con valores MINÚSCULAS
    const pedidoData = {
        cliente_id: estadoApp.clienteSeleccionado.id,
        tipo_venta: "externa", // minúscula según tu enum
        tipo_pago: tipoPago,   // minúscula según tu enum
        latitud_pedido: estadoApp.ubicacion.latitud,
        longitud_pedido: estadoApp.ubicacion.longitud,
        observaciones: observaciones,
        items: estadoApp.pedido.map(item => ({
            producto_id: item.producto_id,
            cantidad: item.cantidad,
            override_tipo_cliente_id: null
        }))
    };
    
    try {
        const response = await fetch('/api/pedidos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${estadoApp.token}`
            },
            body: JSON.stringify(pedidoData)
        });
        
        if (response.ok) {
            const data = await response.json();
            alert(`¡Pedido ${data.data.numero_pedido} creado exitosamente!\nTotal: S/ ${data.data.total.toFixed(2)}`);
            
            // Limpiar estado
            estadoApp.pedido = [];
            document.getElementById('observacionesPedido').value = '';
            cerrarModal('modalConfirmarPedido');
            mostrarProductosPedido();
            
            // Actualizar estadísticas
            cargarEstadisticas();
        } else {
            const error = await response.json();
            alert(`Error: ${error.detail || 'No se pudo crear el pedido'}`);
        }
    } catch (error) {
        console.error('Error enviando pedido:', error);
        alert('Error al enviar el pedido');
    }
}

// NUEVO CLIENTE
function abrirModalNuevoCliente() {
    abrirModal('modalNuevoCliente');
}

async function validarRuc(ruc) {
    const spinner = document.getElementById('validandoRuc');
    const resultado = document.getElementById('resultadoValidacionRuc');
    
    spinner.classList.remove('hidden');
    resultado.innerHTML = '';
    
    try {
        const response = await fetch(`/api/utils/ruc/${ruc}`);
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('nuevaRazonSocial').value = data.razon_social || '';
                document.getElementById('nuevaDireccion').value = data.direccion || '';
                document.getElementById('nuevoDistrito').value = data.distrito || '';
                document.getElementById('nuevaProvincia').value = data.provincia || '';
                document.getElementById('nuevaRegion').value = data.departamento || '';
                
                resultado.className = 'validation-message success';
                resultado.textContent = '✓ RUC válido - Datos cargados';
            } else {
                resultado.className = 'validation-message error';
                resultado.textContent = '✗ RUC no encontrado';
            }
        }
    } catch (error) {
        resultado.className = 'validation-message error';
        resultado.textContent = '✗ Error validando RUC';
    } finally {
        spinner.classList.add('hidden');
    }
}

async function registrarNuevoCliente() {
    const nuevoCliente = {
        ruc: document.getElementById('nuevoRuc').value.trim(),
        razon_social: document.getElementById('nuevaRazonSocial').value.trim(),
        nombre_comercial: document.getElementById('nuevoNombreComercial').value.trim(),
        direccion: document.getElementById('nuevaDireccion').value.trim(),
        distrito: document.getElementById('nuevoDistrito').value.trim(),
        provincia: document.getElementById('nuevaProvincia').value.trim(),
        region: document.getElementById('nuevaRegion').value.trim(),
        telefono: document.getElementById('nuevoTelefono').value.trim(),
        persona_pedido: document.getElementById('personaPedido').value.trim(),
        latitud: estadoApp.ubicacion?.latitud,
        longitud: estadoApp.ubicacion?.longitud
    };
    
    if (!nuevoCliente.ruc || !nuevoCliente.razon_social) {
        alert('Completa los campos obligatorios');
        return;
    }
    
    try {
        const response = await fetch('/api/clientes/crear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${estadoApp.token}`
            },
            body: JSON.stringify(nuevoCliente)
        });
        
        if (response.ok) {
            const data = await response.json();
            alert('Cliente registrado exitosamente');
            cerrarModal('modalNuevoCliente');
            
            // Seleccionar automáticamente el nuevo cliente
            seleccionarCliente(data.cliente);
            
            // Limpiar formulario
            document.getElementById('formNuevoCliente').reset();
        } else {
            alert('Error al registrar cliente');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al registrar cliente');
    }
}

// MODALES DE ESTADÍSTICAS
function mostrarModalMeta() {
    alert('Modal de Meta - En desarrollo');
}

function mostrarModalPedidos() {
    alert('Modal de Pedidos del día - En desarrollo');
}

function mostrarModalRanking() {
    alert('Modal de Ranking - En desarrollo');
}

function mostrarMenuMas() {
    alert('Menú adicional - En desarrollo');
}

// UTILIDADES
function abrirModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
}

function cerrarModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

function logout() {
    if (confirm('¿Deseas cerrar sesión?')) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        window.location.href = '/';
    }
}

async function actualizarPedidos() {
    // Implementar según tu endpoint de pedidos recientes
    console.log('Actualizando pedidos recientes...');
}