// -------------------------------------
// 1. ESTADO DE LA APLICACIÓN
// -------------------------------------
// CAMBIO: Centralizamos todo en un único objeto de estado. Esta es nuestra "única fuente de verdad".
let estadoPedido = { items: [], itemsNoEncontrados: [], cliente: null };
let vendedorData = null;
let token = localStorage.getItem('auth_token');

// --- Variables para los dos tipos de reconocimiento de voz ---
let isRecording = false;
let browserRecognition; // Para el del navegador
let mediaRecorder;      // Para el de Google
let audioChunks = [];

// -------------------------------------
// 2. INICIALIZACIÓN
// -------------------------------------

document.addEventListener('DOMContentLoaded', function() {
    cargarDatosVendedor();
    cargarEstadisticas();
    cargarPedidosRecientes();
    inicializarReconocimientoVozBrowser(); // Inicializamos el del navegador
});

// -------------------------------------
// 3. FUNCIONES DE CARGA Y DATOS INICIALES
// -------------------------------------
// Inicializar Web Speech API
// =============================================
// RECONOCIMIENTO DE VOZ - MOTOR DEL NAVEGADOR
// =============================================
function inicializarReconocimientoVozBrowser() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        browserRecognition = new SpeechRecognition();
        browserRecognition.lang = 'es-ES';
        browserRecognition.continuous = false;
        browserRecognition.interimResults = false;
    }
}

function toggleRecordingBrowser() {
    if (!browserRecognition) {
        alert('Tu navegador no soporta reconocimiento de voz.');
        return;
    }

    const micButton = document.getElementById('micBrowser');
    const inputProductos = document.getElementById('inputProductos');
    
    if (isRecording) {
        browserRecognition.stop();
        // onend se encargará de remover la clase 'recording' y cambiar isRecording
        return;
    }
    
    browserRecognition.start();
    isRecording = true;
    micButton.classList.add('recording');

    browserRecognition.onresult = function(event) {
        const texto = event.results[0][0].transcript.trim();
        inputProductos.value = texto;
        if (texto) {
            procesarPedidoTexto(texto);
        }
        inputProductos.value = '';
    };

    browserRecognition.onend = function() {
        isRecording = false;
        micButton.classList.remove('recording');
    };

    browserRecognition.onerror = function(event) {
        console.error("Error en reconocimiento de voz del navegador:", event.error);
        alert(`Error del micrófono: ${event.error}`);
        isRecording = false;
        micButton.classList.remove('recording');
    };
}


// =============================================
// RECONOCIMIENTO DE VOZ - MOTOR DE GOOGLE
// =============================================
function toggleRecordingGoogle() {
    const micButton = document.getElementById('micGoogle');
    
    if (isRecording) {
        // Detener manualmente
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
        }
        clearTimeout(googleRecordingTimeout); // Limpiamos el temporizador
        isRecording = false;
        micButton.classList.remove('recording');
    } else {
        // Iniciar grabación
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    isRecording = true;
                    micButton.classList.add('recording');
                    audioChunks = [];
                    
                    const options = { mimeType: 'audio/webm;codecs=opus' };
                    mediaRecorder = new MediaRecorder(stream, options);
                    
                    mediaRecorder.start();
                    console.log("Iniciando grabación para Google...");

                    // AÑADIDO: Temporizador de 5 segundos para detener automáticamente
                    googleRecordingTimeout = setTimeout(() => {
                        if (mediaRecorder.state === "recording") {
                            console.log("Grabación detenida automáticamente por timeout.");
                            mediaRecorder.stop();
                        }
                    }, 5000); // 5000 milisegundos = 5 segundos
                    
                    mediaRecorder.addEventListener("dataavailable", event => {
                        audioChunks.push(event.data);
                    });

                    mediaRecorder.addEventListener("stop", () => {
                        const audioBlob = new Blob(audioChunks, { type: options.mimeType });
                        procesarAudioConGoogle(audioBlob);
                        stream.getTracks().forEach(track => track.stop());
                        isRecording = false;
                        micButton.classList.remove('recording');
                        clearTimeout(googleRecordingTimeout); // Limpiamos por si se detuvo manualmente
                    });
                })
                .catch(error => {
                    console.error("Error al acceder al micrófono:", error);
                    alert("No se pudo acceder al micrófono.");
                    isRecording = false;
                    micButton.classList.remove('recording');
                });
        } else {
            alert("Tu navegador no soporta la grabación de audio.");
        }
    }
}

async function procesarAudioConGoogle(audioBlob) {
    document.getElementById('procesandoProductos').classList.remove('hidden');
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'grabacion.webm');

    try {
        const response = await fetch('/api/pedidos/procesar-texto-google', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            document.getElementById('inputProductos').value = `Google: "${data.message}"`;
            actualizarItemsDelPedido(data.data);
        } else {
            console.error("Error de la API de Google:", data.detail || data.message);
            alert(`Error (Google): ${data.detail || data.message}`);
        }
    } catch (error) {
        console.error('Error de red al enviar el audio:', error);
        alert('Error de conexión al enviar el audio.');
    } finally {
        document.getElementById('procesandoProductos').classList.add('hidden');
    }
}



function cargarDatosVendedor() {
    const userData = JSON.parse(localStorage.getItem('user_data') || '{}');
    document.getElementById('vendedorNombre').textContent = userData.nombre || 'Vendedor';
    document.getElementById('vendedorCodigo').textContent = `Código: ${userData.id || 'N/A'}`;
    vendedorData = userData;
}

async function cargarEstadisticas() {
    const token = localStorage.getItem('auth_token');
    if (!token) return;
    try {
        const response = await fetch('/api/vendedor/estadisticas', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('pedidosHoy').textContent = data.data.pedidos_hoy || 0;
            document.getElementById('ventasHoy').textContent = `S/${data.data.ventas_hoy || 0}`;
        }
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
}

async function cargarPedidosRecientes() {
    const token = localStorage.getItem('auth_token');
    if (!token) return;
    try {
        const response = await fetch('/api/vendedor/pedidos-recientes', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        
        if (data.success && data.data.length > 0) {
            mostrarPedidosRecientes(data.data);
        }
    } catch (error) {
        console.error('Error cargando pedidos:', error);
    }
}

function mostrarPedidosRecientes(pedidos) {
    const container = document.getElementById('pedidosRecientes');
    container.innerHTML = pedidos.map(pedido => `
        <div class="bg-white/5 p-2 rounded-lg border border-white/10">
            <div class="flex justify-between items-center">
                <div>
                    <h4 class="text-white text-sm font-medium">${pedido.cliente_nombre}</h4>
                    <p class="text-blue-200 text-xs">#${pedido.numero_pedido}</p>
                </div>
                <div class="text-right">
                    <p class="text-green-400 font-semibold text-sm">S/ ${pedido.total}</p>
                    <span class="inline-block px-2 py-1 text-xs rounded-full ${getEstadoColor(pedido.estado)}">
                        ${pedido.estado}
                    </span>
                </div>
            </div>
        </div>
    `).join('');
}

/*
function getEstadoColor(estado) {
    const colores = {
        'pendiente': 'bg-yellow-500/20 text-yellow-300',
        'confirmado': 'bg-green-500/20 text-green-300',
        'rechazado': 'bg-red-500/20 text-red-300'
    };
    return colores[estado] || 'bg-gray-500/20 text-gray-300';
}
*/

function getEstadoColor(estado) {
        switch(estado.toLowerCase()) {
            case 'confirmado':
                return 'bg-green-100 text-green-800';
            case 'pendiente':
                return 'bg-yellow-100 text-yellow-800';
            case 'entregado':
                return 'bg-blue-100 text-blue-800';
            case 'cancelado':
                return 'bg-red-100 text-red-800';
            case 'rechazado':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
}


// -------------------------------------
// 4. LÓGICA DE PROCESAMIENTO DE PEDIDOS (EL CORAZÓN)
// -------------------------------------
// Manejo del input principal de productos
function handleEnterProductos(event) {
    if (event.key === 'Enter') {
        const input = event.target;
        const texto = input.value.trim();
        if (texto) {
            procesarPedidoTexto(texto);
            // CAMBIO: Limpiamos el input después de la búsqueda (Solución al Punto #3)
            input.value = ''; 
        }
    }
}

function toggleRecordingProductos() {
    if (!recognition) {
        alert('Tu navegador no soporta reconocimiento de voz');
        return;
    }

    const micButton = document.getElementById('micProductos');
    const inputProductos = document.getElementById('inputProductos'); // Obtenemos referencia al input
    
    if (isRecording) {
        recognition.stop();
        micButton.classList.remove('recording');
        isRecording = false;
    } else {
        recognition.start();
        micButton.classList.add('recording');
        isRecording = true;
        
        // --- ESTA ES LA PARTE CORREGIDA ---
        recognition.onresult = function(event) {
            const texto = event.results[0][0].transcript.trim();
            
            // 1. Opcional: Mostramos el texto transcrito en el input para feedback visual.
            inputProductos.value = texto;
            
            // 2. ¡La clave! Llamamos a la misma función que usa la tecla "Enter".
            // Esta función ahora se encarga de todo: llamar a la API, actualizar el estado y renderizar.
            if (texto) {
                procesarPedidoTexto(texto);
            }
            
            // 3. Mejora de UX: Limpiamos el input después de procesar, igual que con "Enter".
            inputProductos.value = '';
        };
        
        recognition.onend = function() {
            micButton.classList.remove('recording');
            isRecording = false;
        };

        recognition.onerror = function(event) {
            console.error("Error en reconocimiento de voz:", event.error);
            micButton.classList.remove('recording');
            isRecording = false;
        }
    }
}

async function procesarPedidoTexto(texto) {
    document.getElementById('procesandoProductos').classList.remove('hidden');
    
    try {
        const response = await fetch('/api/pedidos/procesar-texto', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify({ texto: texto, es_voz: false })
        });
        
        const data = await response.json();
        
        if (data.success && data.data.length > 0) {
            // CAMBIO: Llamamos a la nueva función que actualiza el estado inteligentemente.
            actualizarItemsDelPedido(data.data);
        } else {
            alert('No se pudieron identificar productos en el texto');
        }
    } catch (error) {
        console.error('Error procesando pedido:', error);
        alert('Error procesando pedido');
    } finally {
        document.getElementById('procesandoProductos').classList.add('hidden');
    }
}


// CAMBIO: Nueva función central para manejar los productos que llegan de la API (Solución al Punto #1)
function actualizarItemsDelPedido(productosDetectados) {
    productosDetectados.forEach(productoNuevo => {
        // CAMBIO: Lógica para manejar productos no encontrados (Solución al Punto #4)
        if (!productoNuevo.encontrado) {
            // Por ahora solo lo registramos, podrías mostrarlo en otra lista
            estadoPedido.itemsNoEncontrados.push(productoNuevo);
            console.warn("Producto no encontrado:", productoNuevo.nombre);
            return; // No continuamos con este item
        }

        // Buscamos si el producto ya existe en nuestro pedido actual
        const itemExistente = estadoPedido.items.find(item => item.producto_id === productoNuevo.producto_id);

        if (itemExistente) {
            // Si ya existe, actualizamos la cantidad y recalculamos su subtotal
            itemExistente.cantidad += productoNuevo.cantidad;
            itemExistente.subtotal = itemExistente.cantidad * itemExistente.precio_unitario;
        } else {
            // Si es nuevo, lo añadimos al estado del pedido
            estadoPedido.items.push({
                producto_id: productoNuevo.producto_id,
                nombre: productoNuevo.nombre,
                codigo_producto: productoNuevo.codigo_producto,
                cantidad: productoNuevo.cantidad,
                unidad: productoNuevo.unidad,
                precio_unitario: productoNuevo.precio_unitario,
                subtotal: productoNuevo.precio_total, // Usamos el total que ya calculó el backend
                encontrado: true
            });
        }
    });

    // CAMBIO: Después de modificar el estado, SIEMPRE llamamos a renderizar para actualizar la UI.
    renderizarPedidoCompleto();
}

// -------------------------------------
// 5. FUNCIONES DE RENDERIZADO (UI)
// -------------------------------------

// CAMBIO: Nueva función central para dibujar la lista de productos y el total.
function renderizarPedidoCompleto() {
    mostrarProductosIdentificados();
    actualizarTotal();
}


function mostrarProductosIdentificados() {
    const container = document.getElementById('productosContainer');
    const lista = document.getElementById('listaProductos');

    // CAMBIO: Leemos directamente desde nuestro estado 'estadoPedido.items'.
    if (estadoPedido.items.length === 0) {
        container.classList.add('hidden');
        lista.innerHTML = '';
        return;
    }

    lista.innerHTML = estadoPedido.items.map(producto => {
        const precioUnitario = `S/ ${producto.precio_unitario.toFixed(2)}`;
        const subtotal = `S/ ${producto.subtotal.toFixed(2)}`;
        
        // Usamos una clave única para cada producto en el DOM
        const productoKey = `prod-${producto.producto_id}`;

        return `
            <div class="bg-white/5 p-3 rounded-lg border border-white/10">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <h4 class="text-white font-medium text-sm">${producto.nombre}</h4>
                        <p class="text-blue-200 text-xs">Código: ${producto.codigo_producto ?? 'N/D'}</p>
                        <div class="flex items-center space-x-2 mt-1">
                            <button onclick="cambiarCantidad('${productoKey}', -1)" class="w-6 h-6 bg-red-500 hover:bg-red-600 rounded-full flex items-center justify-center text-white text-xs">-</button>
                            <span class="text-white font-semibold" id="cantidad_${productoKey}">${producto.cantidad}</span>
                            <button onclick="cambiarCantidad('${productoKey}', 1)" class="w-6 h-6 bg-green-500 hover:bg-green-600 rounded-full flex items-center justify-center text-white text-xs">+</button>
                            <span class="text-blue-200 text-xs ml-2">${producto.unidad}</span>
                        </div>
                    </div>
                    <div class="text-right">
                        <p class="text-white font-semibold">${precioUnitario}</p>
                        <p class="text-green-400 font-bold" id="subtotal_${productoKey}">${subtotal}</p>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    container.classList.remove('hidden');
}


function cambiarCantidad(productoKey, cambio) {
    const productoId = parseInt(productoKey.split('-')[1]);
    // CAMBIO: Buscamos y modificamos el producto en nuestro estado central.
    const producto = estadoPedido.items.find(p => p.producto_id === productoId);
    
    if (producto) {
        producto.cantidad += cambio;
        if (producto.cantidad <= 0) {
            // Si la cantidad es 0 o menos, eliminamos el item del pedido.
            estadoPedido.items = estadoPedido.items.filter(p => p.producto_id !== productoId);
        } else {
            producto.subtotal = producto.cantidad * producto.precio_unitario;
        }
        
        // CAMBIO: Después de cualquier cambio, redibujamos todo para asegurar consistencia.
        renderizarPedidoCompleto();
    }
}

function actualizarTotal() {
    // CAMBIO: Calculamos el total leyendo siempre desde el estado.
    const total = estadoPedido.items.reduce((sum, p) => sum + (p.subtotal || 0), 0);
    document.getElementById('totalPedido').textContent = `S/ ${total.toFixed(2)}`;
}

function limpiarPedido() {
    // CAMBIO: Limpiar es tan simple como resetear el estado y volver a renderizar.
    estadoPedido.items = [];
    estadoPedido.itemsNoEncontrados = [];
    renderizarPedidoCompleto();
    document.getElementById('inputProductos').value = '';
}

// -------------------------------------
// 6. LÓGICA DE CLIENTES Y MODAL (SIN CAMBIOS SIGNIFICATIVOS)
// -------------------------------------
function abrirModalCliente() {
    // CAMBIO: Verificamos el estado en lugar de una variable separada.
    if (estadoPedido.items.length === 0) {
        alert('Agrega productos al pedido primero');
        return;
    }
    document.getElementById('modalCliente').classList.remove('hidden');
}

function cerrarModalCliente() {
    document.getElementById('modalCliente').classList.add('hidden');
}

// Búsqueda de bodeguero
let timeoutBusquedaBodeguero;
function buscarBodegueroEnTiempoReal() {
    clearTimeout(timeoutBusquedaBodeguero);
    const termino = document.getElementById('busquedaBodeguero').value;
    
    if (termino.length < 2) {
        document.getElementById('resultadosBusquedaBodeguero').innerHTML = '';
        return;
    }
    
    timeoutBusquedaBodeguero = setTimeout(() => {
        realizarBusquedaBodeguero(termino);
    }, 300);
}

async function realizarBusquedaBodeguero(termino) {
    try {
        const response = await fetch('/api/clientes/buscar-por-voz', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                texto: termino,
                es_voz: false
            })
        });
        const data = await response.json();
        
        if (data.success) {
            mostrarResultadosBusquedaBodeguero(data.data);
        }
    } catch (error) {
        console.error('Error en búsqueda:', error);
    }
}

function mostrarResultadosBusquedaBodeguero(clientes) {
    const container = document.getElementById('resultadosBusquedaBodeguero');
    
    if (clientes.length === 0) {
        container.innerHTML = '<p class="text-blue-300 text-center py-2 text-sm">No se encontraron bodegueros</p>';
        return;
    }
    
    container.innerHTML = clientes.map(cliente => `
        <div class="bg-white/5 p-3 rounded-lg border border-white/10 cursor-pointer hover:bg-white/10 transition-colors"
                onclick="seleccionarCliente(${JSON.stringify(cliente).replace(/"/g, '&quot;')})">
            <h4 class="text-white font-medium text-sm">${cliente.nombre_comercial}</h4>
            <p class="text-blue-200 text-xs">${cliente.ruc || 'Sin RUC'} - ${cliente.distrito}</p>
            <p class="text-blue-300 text-xs">${cliente.telefono}</p>
        </div>
    `).join('');
}

function seleccionarCliente(cliente) {
    clienteSeleccionado = cliente;
    document.getElementById('busquedaBodeguero').value = cliente.nombre_comercial;
    document.getElementById('resultadosBusquedaBodeguero').innerHTML = '';
    document.getElementById('formularioNuevaBodega').classList.add('hidden');
}

function toggleRecordingBodeguero() {
    if (!recognition) {
        alert('Tu navegador no soporta reconocimiento de voz');
        return;
    }

    const micButton = document.getElementById('micBodeguero');
    
    if (isRecording) {
        recognition.stop();
        micButton.classList.remove('recording');
        isRecording = false;
    } else {
        recognition.start();
        micButton.classList.add('recording');
        isRecording = true;
        
        recognition.onresult = function(event) {
            const texto = event.results[0][0].transcript;
            document.getElementById('busquedaBodeguero').value = texto;
            realizarBusquedaBodeguero(texto);
        };
        
        recognition.onend = function() {
            micButton.classList.remove('recording');
            isRecording = false;
        };
    }
}

// Gestión de nueva bodega
function mostrarFormularioNuevaBodega() {
    document.getElementById('formularioNuevaBodega').classList.remove('hidden');
}

let timeoutValidacionRuc;
function validarRucEnTiempoReal() {
    clearTimeout(timeoutValidacionRuc);
    const ruc = document.getElementById('nuevoRuc').value;
    
    if (ruc.length !== 11 || !/^\d+$/.test(ruc)) {
        document.getElementById('resultadoValidacionRuc').innerHTML = '';
        return;
    }
    
    document.getElementById('validandoRuc').classList.remove('hidden');
    
    timeoutValidacionRuc = setTimeout(() => {
        consultarApiSunat(ruc);
    }, 500);
}

async function consultarApiSunat(ruc) {
    try {
        // Simulación de API SUNAT - En producción usar API real
        // const response = await fetch(`/api/sunat/consultar-ruc/${ruc}`);
        
        // Simulación de respuesta de API
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const datosSimulados = {
            success: true,
            data: {
                ruc: ruc,
                razon_social: "BODEGA SAN MARTIN E.I.R.L.",
                nombre_comercial: "Bodega San Martin",
                estado: "ACTIVO",
                direccion: "No disponible en SUNAT"
            }
        };
        
        if (datosSimulados.success) {
            document.getElementById('nuevaRazonSocial').value = datosSimulados.data.razon_social;
            document.getElementById('nuevoNombreComercial').value = datosSimulados.data.nombre_comercial;
            
            document.getElementById('resultadoValidacionRuc').innerHTML = `
                <span class="text-green-400">✓ RUC válido - ${datosSimulados.data.estado}</span>
            `;
        } else {
            document.getElementById('resultadoValidacionRuc').innerHTML = `
                <span class="text-red-400">✗ RUC no encontrado</span>
            `;
        }
    } catch (error) {
        document.getElementById('resultadoValidacionRuc').innerHTML = `
            <span class="text-yellow-400">⚠ Error validando RUC</span>
        `;
    } finally {
        document.getElementById('validandoRuc').classList.add('hidden');
    }
}

async function registrarNuevaBodega() {
    const nuevaBodega = {
        ruc: document.getElementById('nuevoRuc').value,
        razon_social: document.getElementById('nuevaRazonSocial').value,
        nombre_comercial: document.getElementById('nuevoNombreComercial').value,
        direccion_completa: document.getElementById('nuevaDireccion').value,
        distrito: document.getElementById('nuevoDistrito').value,
        provincia: document.getElementById('nuevaProvincia').value,
        departamento: document.getElementById('nuevaRegion').value,
        telefono: document.getElementById('nuevoTelefono').value,
        persona_pedido: document.getElementById('personaPedido').value
    };
    
    // Validaciones básicas
    if (!nuevaBodega.nombre_comercial || !nuevaBodega.telefono) {
        alert('Nombre comercial y teléfono son obligatorios');
        return;
    }
    
    try {
        const response = await fetch('/api/clientes/registrar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(nuevaBodega)
        });
        
        const data = await response.json();
        
        if (data.success) {
            clienteSeleccionado = data.data;
            alert('Bodega registrada correctamente');
            document.getElementById('formularioNuevaBodega').classList.add('hidden');
            document.getElementById('busquedaBodeguero').value = nuevaBodega.nombre_comercial;
            
            // Limpiar formulario
            ['nuevoRuc', 'nuevaRazonSocial', 'nuevoNombreComercial', 'nuevaDireccion', 
                'nuevoDistrito', 'nuevaProvincia', 'nuevaRegion', 'nuevoTelefono', 'personaPedido']
                .forEach(id => document.getElementById(id).value = '');
        } else {
            alert('Error registrando bodega: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error de conexión');
    }
}

async function enviarPedidoFinal() {
    // CAMBIO: Aseguramos que se use el estado central.
    if (!estadoPedido.cliente) { // Usamos estadoPedido.cliente
        alert('Selecciona o registra una bodega primero');
        return;
    }

    if (estadoPedido.items.length === 0) {
        alert('No hay productos en el pedido');
        return;
    }

    const pedidoData = {
        productos: estadoPedido.items, // Usamos estadoPedido.items
        cliente_id: estadoPedido.cliente.cliente_id,
        modalidad_pago: document.getElementById('modalidadPago').value,
        plazo_pago: getPlazoPago(document.getElementById('modalidadPago').value),
        observaciones: document.getElementById('observacionesPedido').value,
        coordenadas: await obtenerUbicacionActual()
    };

    try {
        document.getElementById('btnEnviarPedido').disabled = true;
        document.getElementById('btnEnviarPedido').textContent = 'Enviando...';

        const response = await fetch('/api/pedidos/confirmar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(pedidoData)
        });

        const data = await response.json();

        if (data.success) {
            alert(`¡Pedido enviado exitosamente!\nNúmero: ${data.data.numero_pedido}`);
            
            // Limpiar todo
            limpiarPedido();
            cerrarModalCliente();
            clienteSeleccionado = null;
            document.getElementById('busquedaBodeguero').value = '';
            document.getElementById('modalidadPago').value = 'credito_15_dias';
            document.getElementById('observacionesPedido').value = '';
            
            // Recargar estadísticas
            cargarEstadisticas();
            cargarPedidosRecientes();
        } else {
            alert('Error enviando pedido: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error de conexión');
    } finally {
        document.getElementById('btnEnviarPedido').disabled = false;
        document.getElementById('btnEnviarPedido').textContent = 'ENVIAR PEDIDO';
    }
}

function getPlazoPago(modalidad) {
    const plazos = {
        'efectivo_cash': 0,
        'efectivo_yape': 0,
        'efectivo_plin': 0,
        'credito_15_dias': 15,
        'credito_30_dias': 30,
        'credito_45_dias': 45
    };
    return plazos[modalidad] || 15;
}

async function obtenerUbicacionActual() {
    return new Promise((resolve) => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve({
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    });
                },
                () => {
                    resolve({ lat: -12.0464, lng: -77.0428 }); // Lima por defecto
                }
            );
        } else {
            resolve({ lat: -12.0464, lng: -77.0428 });
        }
    });
}

function actualizarPedidos() {
    cargarPedidosRecientes();
    cargarEstadisticas();
}

function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    window.location.href = '/';
}
