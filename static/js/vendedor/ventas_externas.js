// SISTEMA DE NOTIFICACIONES TOAST
const Toast = {
    container: null,
    
    init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    },
    
    show(message, type = 'info', duration = 4000) {
        this.init();
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>',
            error: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>',
            warning: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>',
            info: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>'
        };
        
        const titles = {
            success: '¡Éxito!',
            error: 'Error',
            warning: 'Advertencia',
            info: 'Información'
        };
        
        toast.innerHTML = `
            <div class="toast-icon">
                <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    ${icons[type]}
                </svg>
            </div>
            <div class="toast-content">
                <div class="toast-title">${titles[type]}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="Toast.remove(this.parentElement)">
                <svg class="icon-small" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        `;
        
        this.container.appendChild(toast);
        
        if (duration > 0) {
            setTimeout(() => this.remove(toast), duration);
        }
        
        return toast;
    },
    
    remove(toast) {
        toast.classList.add('removing');
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
        }, 300);
    },
    
    success(message, duration) { return this.show(message, 'success', duration); },
    error(message, duration) { return this.show(message, 'error', duration); },
    warning(message, duration) { return this.show(message, 'warning', duration); },
    info(message, duration) { return this.show(message, 'info', duration); }
};


// Estado global de la aplicación
const estadoApp = {
    token: localStorage.getItem('auth_token'),
    vendedor: null,
    ubicacion: null,
    clienteSeleccionado: null,
    pedido: [],
    productosSeleccionados: new Set(),
    recognitionCliente: null,
    recognitionBrowser: null, // Para productos con navegador
    mediaRecorder: null,      // Para productos con Google
    audioChunks: [],
    isRecordingCliente: false,
    isRecordingBrowser: false,
    isRecordingGoogle: false,
    googleRecordingTimeout: null
};

// Agregar event listener para seleccionar texto al enfocar
// Inicialización (mantener SOLO esta)
document.addEventListener('DOMContentLoaded', function() {
    verificarAutenticacion();
    cargarDatosVendedor();
    inicializarReconocimientoVoz();
    configurarEventListeners();
    
    // AGREGAR ESTO:
    const inputProductos = document.getElementById('inputProductos');
    if (inputProductos) {
        inputProductos.addEventListener('focus', function() {
            this.select();
        });
    }
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
        const response = await fetch('/api/vendedor/estadisticas/hoy', {
            headers: { 'Authorization': `Bearer ${estadoApp.token}` }
        });
        
        if (response.ok) {
            const result = await response.json();
            document.getElementById('pedidosHoy').textContent = result.data.pedidos || 0;
            document.getElementById('ventasHoy').textContent = `S/. ${(result.data.ventas || 0).toFixed(2)}`;
        } else {
            console.error('Error en estadísticas:', response.status);
        }
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
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        console.log('Reconocimiento de voz no disponible');
        return;
    }
    
    // Para búsqueda de cliente
    estadoApp.recognitionCliente = new SpeechRecognition();
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
    
    // Para productos con navegador
    estadoApp.recognitionBrowser = new SpeechRecognition();
    estadoApp.recognitionBrowser.continuous = false;
    estadoApp.recognitionBrowser.interimResults = false;
    estadoApp.recognitionBrowser.lang = 'es-PE';
    
    estadoApp.recognitionBrowser.onresult = function(event) {
        const texto = event.results[0][0].transcript.trim();
        if (texto.length >= 3) {
            buscarProductos(texto);
        }
    };
    
    estadoApp.recognitionBrowser.onend = function() {
        estadoApp.isRecordingBrowser = false;
        document.getElementById('micBrowser').classList.remove('recording');
    };
    
    estadoApp.recognitionBrowser.onerror = function(event) {
        console.error('Error en reconocimiento de voz:', event.error);
        estadoApp.isRecordingBrowser = false;
        document.getElementById('micBrowser').classList.remove('recording');
    };
}

// Micrófono del navegador para productos
function toggleRecordingBrowser() {
    if (!estadoApp.recognitionBrowser || !estadoApp.clienteSeleccionado) {
        if (!estadoApp.clienteSeleccionado) {
            Toast.info('Primero selecciona un cliente');
        }
        return;
    }
    
    const micButton = document.getElementById('micBrowser');
    
    if (estadoApp.isRecordingBrowser) {
        estadoApp.recognitionBrowser.stop();
    } else {
        estadoApp.recognitionBrowser.start();
        estadoApp.isRecordingBrowser = true;
        micButton.classList.add('recording');
    }
}

// Micrófono de Google para productos
function toggleRecordingGoogle() {
    if (!estadoApp.clienteSeleccionado) {
        Toast.info('Primero selecciona un cliente');
        return;
    }
    
    const micButton = document.getElementById('micGoogle');
    
    if (estadoApp.isRecordingGoogle) {
        // Detener grabación
        if (estadoApp.mediaRecorder && estadoApp.mediaRecorder.state === "recording") {
            estadoApp.mediaRecorder.stop();
        }
        clearTimeout(estadoApp.googleRecordingTimeout);
        estadoApp.isRecordingGoogle = false;
        micButton.classList.remove('recording');
    } else {
        // Iniciar grabación
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    estadoApp.isRecordingGoogle = true;
                    micButton.classList.add('recording');
                    estadoApp.audioChunks = [];
                    
                    const options = { mimeType: 'audio/webm;codecs=opus' };
                    estadoApp.mediaRecorder = new MediaRecorder(stream, options);
                    
                    estadoApp.mediaRecorder.start();
                    console.log("Grabación iniciada con Google...");

                    // Detener automáticamente después de 5 segundos
                    estadoApp.googleRecordingTimeout = setTimeout(() => {
                        if (estadoApp.mediaRecorder.state === "recording") {
                            console.log("Deteniendo grabación automáticamente...");
                            estadoApp.mediaRecorder.stop();
                        }
                    }, 5000);
                    
                    estadoApp.mediaRecorder.addEventListener("dataavailable", event => {
                        estadoApp.audioChunks.push(event.data);
                    });

                    estadoApp.mediaRecorder.addEventListener("stop", () => {
                        const audioBlob = new Blob(estadoApp.audioChunks, { type: options.mimeType });
                        procesarAudioConGoogle(audioBlob);
                        stream.getTracks().forEach(track => track.stop());
                        estadoApp.isRecordingGoogle = false;
                        micButton.classList.remove('recording');
                        clearTimeout(estadoApp.googleRecordingTimeout);
                    });
                })
                .catch(error => {
                    console.error("Error al acceder al micrófono:", error);
                    Toast.info("No se pudo acceder al micrófono.");
                    estadoApp.isRecordingGoogle = false;
                    micButton.classList.remove('recording');
                });
        } else {
            Toast.info("Tu navegador no soporta la grabación de audio.");
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
            headers: { 'Authorization': `Bearer ${estadoApp.token}` },
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Buscar productos con el texto transcrito
            const textoTranscrito = data.message || '';
            if (textoTranscrito && textoTranscrito.length >= 3) {
                buscarProductos(textoTranscrito);
            }
        } else {
            console.error("Error de Google API:", data.detail || data.message);
            Toast.error(`Error (Google): ${data.detail || data.message}`);
        }
    } catch (error) {
        console.error('Error enviando audio:', error);
        Toast.error('Error de conexión al enviar el audio.');
    } finally {
        document.getElementById('procesandoProductos').classList.add('hidden');
    }
}

// GESTIÓN DE UBICACIÓN
function solicitarUbicacion() {
    if (!navigator.geolocation) {
        if (typeof Toast !== 'undefined') {
            Toast.error('Tu navegador no soporta geolocalización');
        } else {
            alert('Tu navegador no soporta geolocalización');
        }
        return;
    }
    
    if (typeof Toast !== 'undefined') {
        Toast.info('Solicitando ubicación GPS...');
    }
    
    // Opciones para MÁXIMA precisión
    const options = {
        enableHighAccuracy: true,  // Forzar GPS
        timeout: 30000,            // Esperar hasta 30 segundos
        maximumAge: 0              // No usar caché
    };
    
    navigator.geolocation.getCurrentPosition(
        (position) => {
            const precision = position.coords.accuracy;
            
            estadoApp.ubicacion = {
                latitud: position.coords.latitude,
                longitud: position.coords.longitude,
                precision: precision
            };
            
            // Validar precisión
            if (precision > 100) {
                if (typeof Toast !== 'undefined') {
                    Toast.warning(`Ubicación obtenida pero con baja precisión (±${Math.round(precision)}m). Asegúrate de activar el GPS.`);
                } else {
                    alert(`Precisión baja: ±${Math.round(precision)}m. Activa el GPS para mayor precisión.`);
                }
            } else {
                if (typeof Toast !== 'undefined') {
                    Toast.success(`Ubicación GPS confirmada (±${Math.round(precision)}m)`);
                } else {
                    alert('Ubicación GPS confirmada');
                }
            }
            
            // Actualizar UI
            document.getElementById('estadoUbicacion').textContent = `GPS: ±${Math.round(precision)}m`;
            document.getElementById('btnUbicacion').classList.add('ubicacion-activa');
            
            // Cerrar modal si existe
            const modal = document.getElementById('modalUbicacion');
            if (modal) {
                modal.classList.add('hidden');
            }
        },
        (error) => {
            console.error('Error de geolocalización:', error);
            
            let mensaje = 'No se pudo obtener la ubicación.';
            
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    mensaje = 'Permiso de ubicación denegado. Ve a configuración del navegador.';
                    break;
                case error.POSITION_UNAVAILABLE:
                    mensaje = 'Ubicación no disponible. Activa el GPS.';
                    break;
                case error.TIMEOUT:
                    mensaje = 'Tiempo de espera agotado. Intenta de nuevo.';
                    break;
            }
            
            if (typeof Toast !== 'undefined') {
                Toast.error(mensaje);
            } else {
                alert(mensaje);
            }
        },
        options
    );
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
    // Normalizar estructura del cliente
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
        nombre_completo: cliente.nombre_comercial || cliente.razon_social || `Cliente RUC ${cliente.ruc}`
    };

    // PRIMERO: Guardar el cliente seleccionado
    estadoApp.clienteSeleccionado = clienteNormalizado;
    
    // SEGUNDO: Actualizar UI del chip
    const chip = document.getElementById('chipCliente');
    document.getElementById('chipClienteNombre').textContent = clienteNormalizado.nombre_completo;
    document.getElementById('chipClienteTipo').textContent = clienteNormalizado.tipo_cliente_nombre;
    chip.classList.remove('hidden');
    
    // TERCERO: Limpiar búsqueda de cliente
    document.getElementById('inputBusquedaCliente').value = '';
    ocultarDropdownClientes();
    
    // CUARTO: Activar modo compacta
    document.querySelector('.seccion-busqueda-combinada').classList.add('compacta');
    
    // QUINTO: Mostrar y habilitar búsqueda de productos
    document.getElementById('busquedaProductos').classList.remove('hidden');
    
    const inputProductos = document.getElementById('inputProductos');
    const micBrowser = document.getElementById('micBrowser');
    const micGoogle = document.getElementById('micGoogle');
    
    inputProductos.disabled = false;
    micBrowser.disabled = false;
    micGoogle.disabled = false;
    
    // SEXTO: Enfocar input de productos
    setTimeout(() => {
        inputProductos.focus();
        inputProductos.select();
    }, 100);
    
    // SÉPTIMO: Verificar ubicación (DESPUÉS de todo lo demás)
    if (!estadoApp.ubicacion) {
        setTimeout(() => {
            if (typeof Toast !== 'undefined') {
                Toast.warning('Comparte tu ubicación para poder enviar el pedido');
            }
            mostrarModalUbicacion();
        }, 500);
    } else {
        // Ya tiene ubicación
        if (typeof Toast !== 'undefined') {
            Toast.success(`Cliente ${clienteNormalizado.nombre_completo} seleccionado`);
        }
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
    estadoApp.productosSeleccionados.clear();
    
    // Ocultar búsqueda de productos
    document.getElementById('busquedaProductos').classList.add('hidden');

    // Ocultar chip
    document.getElementById('chipCliente').classList.add('hidden');

    // Desactivar modo compacta
    document.querySelector('.seccion-busqueda-combinada').classList.remove('compacta');

    // Ocultar búsqueda de productos
    document.getElementById('busquedaProductos').classList.add('hidden');

    
    // Expandir sección de búsqueda
    document.querySelector('.seccion-busqueda-combinada').classList.remove('compacta');
    
    // Deshabilitar productos y AMBOS micrófonos
    const inputProductos = document.getElementById('inputProductos');
    const micBrowser = document.getElementById('micBrowser');
    const micGoogle = document.getElementById('micGoogle');
    
    inputProductos.disabled = true;
    micBrowser.disabled = true;
    micGoogle.disabled = true;
    inputProductos.value = '';
    
    // Limpiar productos
    document.getElementById('productosContainer').classList.add('hidden');
    ocultarDropdownProductos();
    
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
        ocultarDropdownProductos();
        return;
    }
    
    let html = '';
    
    productos.forEach(producto => {
        // Guardar referencia global
        window['producto_' + producto.id] = producto;
        
        const estaEnPedido = estadoApp.pedido.some(item => item.producto_id === producto.id);
        const estaSeleccionado = estadoApp.productosSeleccionados.has(producto.id);
        
        html += `
            <div class="item-producto-dropdown ${estaSeleccionado ? 'seleccionado' : ''} ${estaEnPedido ? 'ya-agregado' : ''}" 
                 onclick="if(!${estaEnPedido}) toggleSeleccionProducto(${producto.id})">
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
    });
    
    lista.innerHTML = html;
    actualizarContadorSeleccionados();
    dropdown.classList.remove('hidden');

    // Asegurar z-index alto
    dropdown.style.zIndex = '2000';
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
    
    // Toggle del Set
    if (estadoApp.productosSeleccionados.has(productoId)) {
        estadoApp.productosSeleccionados.delete(productoId);
    } else {
        estadoApp.productosSeleccionados.add(productoId);
    }
    
    // Actualizar contador
    actualizarContadorSeleccionados();
    
    // CORRECCIÓN: Actualizar checkbox visual
    const checkbox = document.querySelector(`input[onchange*="${productoId}"]`);
    if (checkbox) {
        checkbox.checked = estadoApp.productosSeleccionados.has(productoId);
    }
    
    // Actualizar estilo de la fila
    const item = checkbox?.closest('.item-producto-dropdown');
    if (item) {
        if (estadoApp.productosSeleccionados.has(productoId)) {
            item.classList.add('seleccionado');
        } else {
            item.classList.remove('seleccionado');
        }
    }
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
    const nuevosProductos = [];
    
    estadoApp.productosSeleccionados.forEach(productoId => {
        const productoData = window['producto_' + productoId];
        if (productoData) {
            nuevosProductos.push({
                producto_id: productoData.id,
                codigo_producto: productoData.codigo_producto,
                nombre: productoData.nombre,
                cantidad: 1,
                unidad: productoData.unidad || 'unidad',
                precio_unitario: parseFloat(productoData.precio_unitario),
                subtotal: parseFloat(productoData.precio_unitario),
                esNuevo: true // Marca para animación
            });
        }
    });
    
    if (nuevosProductos.length > 0) {
        // CORRECCIÓN #2: Agregar al INICIO en lugar del final
        estadoApp.pedido.unshift(...nuevosProductos);
        
        // Limpiar selección y actualizar UI
        estadoApp.productosSeleccionados.clear();
        ocultarDropdownProductos();
        mostrarProductosPedido();
        
        // Notificación Toast
        Toast.success(`${nuevosProductos.length} producto${nuevosProductos.length > 1 ? 's agregados' : ' agregado'} al pedido`);
    } else {
        Toast.warning('No hay productos seleccionados');
    }
}

// Eliminar función handleEnterProductos ya que ahora es búsqueda en tiempo real
function handleEnterProductos(event) {
    // Mantener por compatibilidad pero ya no se usa
}

async function procesarPedidoTexto(texto) {
    if (!estadoApp.clienteSeleccionado) {
        Toast.info('Primero selecciona un cliente');
        return;
    }
    
    if (!estadoApp.ubicacion) {
        Toast.info('Primero comparte tu ubicación');
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
                Toast.info('No se encontraron productos en la base de datos');
            }
            
            // Mostrar productos no encontrados
            const noEncontrados = data.data.filter(p => !p.encontrado);
            if (noEncontrados.length > 0) {
                console.warn('Productos no encontrados:', noEncontrados.map(p => p.nombre));
            }
        } else {
            Toast.info(data.message || 'No se pudieron identificar productos');
        }
    } catch (error) {
        console.error('Error procesando pedido:', error);
        Toast.error('Error procesando pedido');
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
    
    container.classList.remove('hidden');
    lista.innerHTML = '';
    
    let total = 0;
    
    estadoApp.pedido.forEach((item, index) => {
        const div = document.createElement('div');
        div.className = 'producto-item';
        
        // CORRECCIÓN: Agregar clase 'nuevo' para animación
        if (item.esNuevo) {
            div.classList.add('nuevo');
            delete item.esNuevo;
        }
        
        div.innerHTML = `
            <div class="producto-info">
                <div class="producto-nombre">${item.nombre}</div>
                <div class="producto-codigo">${item.codigo_producto}</div>
            </div>
            <div class="producto-cantidad">
                <button class="btn-cantidad" onclick="cambiarCantidad(${index}, -1)">
                    <svg class="icon-small" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"></path>
                    </svg>
                </button>
                <input 
                    type="number" 
                    class="cantidad-input" 
                    value="${item.cantidad}"
                    min="1"
                    max="9999"
                    onchange="actualizarCantidadDirecta(${index}, this.value)"
                    onclick="this.select()"
                />
                <button class="btn-cantidad" onclick="cambiarCantidad(${index}, 1)">
                    <svg class="icon-small" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                    </svg>
                </button>
            </div>
            <div class="producto-precio">
                <div class="precio-unitario">S/ ${item.precio_unitario.toFixed(2)}</div>
                <div class="subtotal">S/ ${item.subtotal.toFixed(2)}</div>
            </div>
            <button class="btn-eliminar" onclick="eliminarProducto(${index})">
                <svg class="icon-small" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                </svg>
            </button>
        `;
        
        lista.appendChild(div);
        total += item.subtotal;
    });
    
    document.getElementById('totalPedido').textContent = `S/ ${total.toFixed(2)}`;
}


// Actualizar cantidad escribiendo directamente
function actualizarCantidadDirecta(index, valor) {
    const cantidad = parseInt(valor);
    
    // Validar cantidad
    if (isNaN(cantidad) || cantidad < 1) {
        Toast.warning('La cantidad mínima es 1');
        mostrarProductosPedido(); // Restaurar valor anterior
        return;
    }
    
    if (cantidad > 9999) {
        Toast.warning('La cantidad máxima es 9999');
        mostrarProductosPedido();
        return;
    }
    
    // Actualizar
    const item = estadoApp.pedido[index];
    item.cantidad = cantidad;
    item.subtotal = item.cantidad * item.precio_unitario;
    
    mostrarProductosPedido();
    Toast.success(`Cantidad actualizada: ${cantidad} unidades`);
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

// Cambiar cantidad de producto en el pedido
function cambiarCantidad(index, delta) {
    const item = estadoApp.pedido[index];
    const nuevaCantidad = item.cantidad + delta;
    
    if (nuevaCantidad <= 0) {
        eliminarProducto(index);
        return;
    }
    
    item.cantidad = nuevaCantidad;
    item.subtotal = item.cantidad * item.precio_unitario;
    mostrarProductosPedido();
}

// Eliminar producto del pedido
function eliminarProducto(index) {
    const producto = estadoApp.pedido[index];
    estadoApp.pedido.splice(index, 1);
    mostrarProductosPedido();
    
    // Notificación (si tienes Toast, sino usa alert)
    if (typeof Toast !== 'undefined') {
        Toast.info(`${producto.nombre} eliminado del pedido`);
    }
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
        Toast.info('Agrega productos al pedido');
        return;
    }
    
    if (!estadoApp.ubicacion) {
        Toast.info('Por favor, comparte tu ubicación');
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

    // Validar precisión antes de enviar
    if (estadoApp.ubicacion.precision > 1000) {
        if (!confirm(`La precisión de tu ubicación es baja (±${Math.round(estadoApp.ubicacion.precision)}m). ¿Deseas continuar de todas formas?`)) {
            return;
        }
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
            Toast.success(`¡Pedido ${data.data.numero_pedido} creado exitosamente!\nTotal: S/ ${data.data.total.toFixed(2)}`);
            
            // Limpiar estado
            estadoApp.pedido = [];
            document.getElementById('observacionesPedido').value = '';
            cerrarModal('modalConfirmarPedido');
            mostrarProductosPedido();
            
            // Actualizar estadísticas
            cargarEstadisticas();
        } else {
            const error = await response.json();
            Toast.error(`Error: ${error.detail || 'No se pudo crear el pedido'}`);
        }
    } catch (error) {
        console.error('Error enviando pedido:', error);
        Toast.error('Error al enviar el pedido');
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
        Toast.warning('Completa los campos obligatorios');
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
            Toast.success('Cliente registrado exitosamente');
            cerrarModal('modalNuevoCliente');
            
            // Seleccionar automáticamente el nuevo cliente
            seleccionarCliente(data.cliente);
            
            // Limpiar formulario
            document.getElementById('formNuevoCliente').reset();
        } else {
            Toast.error('Error al registrar cliente');
        }
    } catch (error) {
        console.error('Error:', error);
        Toast.error('Error al registrar cliente');
    }
}

// MODALES DE ESTADÍSTICAS
function mostrarModalMeta() {
    Toast.info('Modal de Meta - En desarrollo');
}

function mostrarModalPedidos() {
    Toast.info('Modal de Pedidos del día - En desarrollo');
}

function mostrarModalRanking() {
    Toast.info('Modal de Ranking - En desarrollo');
}

function mostrarMenuMas() {
    Toast.info('Menú adicional - En desarrollo');
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


// MODAL DE ESTADISTICAS - PEDIDOS DEL DÍA
// Modal de Pedidos del Día
async function mostrarModalPedidos() {
    document.getElementById('modalPedidos').classList.remove('hidden');
    await cargarPedidosHoy();
}

async function cargarPedidosHoy() {
    // Debug: ver todas las cookies
    console.log('Todas las cookies:', document.cookie);
    
    // Intentar con auth_token (del localStorage)
    let token = localStorage.getItem('auth_token');
    
    console.log('Token extraído:', token ? 'SÍ' : 'NO');
    
    if (!token) {
        document.getElementById('listaPedidosHoy').innerHTML = 
            '<p style="text-align:center;color:#ef4444;">Sesión expirada. Recarga la página.</p>';
        return;
    }
    
    try {
        const response = await fetch('/api/vendedor/estadisticas/pedidos-hoy', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarPedidosEnModal(data.data);
        } else {
            document.getElementById('listaPedidosHoy').innerHTML = 
                `<p style="text-align:center;color:#ef4444;">Error: ${data.message}</p>`;
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('listaPedidosHoy').innerHTML = 
            '<p style="text-align:center;color:#ef4444;">Error de conexión</p>';
    }
}

function mostrarPedidosEnModal(pedidos) {
    // Calcular estadísticas
    const total = pedidos.length;
    const totalVentas = pedidos.reduce((sum, p) => sum + p.total, 0);
    const pendientes = pedidos.filter(p => p.estado === 'pendiente_aprobacion').length;
    
    document.getElementById('totalPedidosHoy').textContent = total;
    document.getElementById('totalVentasHoy').textContent = `S/ ${totalVentas.toFixed(2)}`;
    document.getElementById('pendientesHoy').textContent = pendientes;
    
    // Mostrar lista
    const lista = document.getElementById('listaPedidosHoy');
    
    if (pedidos.length === 0) {
        lista.innerHTML = '<p style="text-align:center;color:#93c5fd;">No hay pedidos hoy</p>';
        return;
    }
    
    lista.innerHTML = pedidos.map(p => `
        <div class="pedido-card">
            <div class="pedido-card-header">
                <span class="pedido-numero">${p.numero_pedido}</span>
                <span class="pedido-estado estado-${p.estado}">${formatearEstado(p.estado)}</span>
            </div>
            <div class="pedido-info">
                <div class="pedido-dato"><strong>Cliente:</strong> ${p.cliente_nombre}</div>
                <div class="pedido-dato"><strong>Hora:</strong> ${p.hora}</div>
                <div class="pedido-dato"><strong>Items:</strong> ${p.items_count} productos</div>
                <div class="pedido-total">S/ ${p.total.toFixed(2)}</div>
            </div>
        </div>
    `).join('');
}

function formatearEstado(estado) {
    const estados = {
        'pendiente_aprobacion': 'Pendiente',
        'aprobado': 'Aprobado',
        'rechazado': 'Rechazado',
        'en_preparacion': 'En Preparación',
        'en_ruta': 'En Ruta',
        'entregado': 'Entregado'
    };
    return estados[estado] || estado;
}
