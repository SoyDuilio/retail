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

// ============================================================================
// INICIALIZACIÓN AL CARGAR LA PÁGINA
// ============================================================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando Dashboard Vendedor...');
    
    // 1. Cargar token
    estadoApp.token = localStorage.getItem('auth_token');
    
    if (!estadoApp.token) {
        console.warn('No hay token de autenticación');
        window.location.href = '/login';
        return;
    }
    
    // 2. Inicializar componentes
    verificarAutenticacion();
    
    inicializarReconocimientoVoz();
    configurarEventListeners();
    
    // 3. Configurar input de productos
    const inputProductos = document.getElementById('inputProductos');
    if (inputProductos) {
        inputProductos.addEventListener('focus', function() {
            this.select();
        });
    }
    
    // ============================================
    // 4. CONFIGURAR BOTÓN CERRAR CHIP
    // ============================================
    const chipCliente = document.getElementById('chipCliente');
    if (chipCliente) {
        const btnCerrar = chipCliente.querySelector('.chip-close');
        if (btnCerrar) {
            btnCerrar.removeAttribute('onclick');
            btnCerrar.addEventListener('click', function(e) {
                e.stopPropagation();
                e.preventDefault();
                console.log('🔄 Click en cerrar chip');
                cambiarCliente();
            });
            console.log('✅ Listener botón cerrar chip configurado');
        }
    }
    
    // ============================================
    // 5. CONFIGURAR MODAL DE UBICACIÓN
    // ============================================
    const modalUbicacion = document.getElementById('modalUbicacion');
    if (modalUbicacion) {
        // Cerrar con click en overlay
        modalUbicacion.addEventListener('click', function(e) {
            if (e.target === modalUbicacion) {
                console.log('🚪 Click en overlay');
                cerrarModalUbicacion();
            }
        });
        
        // Cerrar con botón X
        const btnCerrarModal = modalUbicacion.querySelector('.modal-close, [data-close-modal]');
        if (btnCerrarModal) {
            btnCerrarModal.addEventListener('click', function(e) {
                e.stopPropagation();
                console.log('🚪 Click en botón X');
                cerrarModalUbicacion();
            });
        }
        
        // Cerrar con ESC
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modalUbicacion.classList.contains('modal-activo')) {
                console.log('🚪 Tecla ESC');
                cerrarModalUbicacion();
            }
        });
        
        console.log('✅ Modal ubicación configurado');
    }
    
    // ============================================
    // 6. CONFIGURAR INFO CRÉDITO PARA MOBILE
    // ============================================
    
});

function formatPrice(amount) {
    return new Intl.NumberFormat('es-PE', {
        style: 'currency',
        currency: 'PEN'
    }).format(amount);
}

// Función auxiliar para anunciar el total
async function announceTotal() {
    const total = estadoApp.pedido.reduce((sum, item) => sum + item.subtotal, 0);
    
    // Formatear mensaje para voz
    const totalRedondeado = Math.round(total * 100) / 100;
    const soles = Math.floor(totalRedondeado);
    const centavos = Math.round((totalRedondeado - soles) * 100);
    
    let mensaje = `Van ${soles} ${soles === 1 ? 'sol' : 'soles'}`;
    if (centavos > 0) {
        mensaje += ` con ${centavos} ${centavos === 1 ? 'centavo' : 'centavos'}`;
    }
    
    // Actualizar visual con efecto
    const totalElement = document.getElementById('totalPedido');
    if (totalElement) {
        totalElement.textContent = formatPrice(total);
        totalElement.classList.add('pulse');
        setTimeout(() => totalElement.classList.remove('pulse'), 500);
    }
    
    // Anunciar por voz
    if (window.ttsClient) {
        await window.ttsClient.speak(mensaje, { speed: 1.1 });
    }
}

// Verificar autenticación
function verificarAutenticacion() {
    // Leer token si no está cargado
    if (!estadoApp.token) {
        estadoApp.token = localStorage.getItem('auth_token');
    }
    
    if (!estadoApp.token) {
        console.warn('No hay token de autenticación');
        window.location.href = '/login';
        return false;
    }
    
    return true;
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
            headers: {
                'Authorization': `Bearer ${estadoApp.token}`
            }
        });
        
        if (!response.ok) throw new Error('Error cargando estadísticas');
        
        const data = await response.json();
        
        // ✅ Validar que los elementos existan antes de actualizar
        const pedidosHoy = document.getElementById('pedidosHoy');
        const ventasHoy = document.getElementById('ventasHoy');
        
        if (pedidosHoy) {
            pedidosHoy.textContent = data.pedidos || 0;
        } else {
            console.warn('⚠️ Elemento #pedidosHoy no encontrado');
        }
        
        if (ventasHoy) {
            ventasHoy.textContent = `S/ ${(data.ventas || 0).toFixed(2)}`;
        } else {
            console.warn('⚠️ Elemento #ventasHoy no encontrado');
        }
        
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
        // No mostrar error al usuario, solo en consola
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
    
    const options = {
        enableHighAccuracy: true,
        timeout: 30000,
        maximumAge: 0
    };
    
    navigator.geolocation.getCurrentPosition(
        (position) => {
            const precision = position.coords.accuracy;
            
            // ✅ 1. Guardar en estadoApp PRIMERO
            estadoApp.ubicacion = {
                latitud: position.coords.latitude,
                longitud: position.coords.longitude,
                precision: precision
            };
            
            console.log('📍 Ubicación guardada en estadoApp:', estadoApp.ubicacion);
            
            // ✅ 2. Mostrar Toast
            if (precision > 100) {
                if (typeof Toast !== 'undefined') {
                    Toast.warning(`Ubicación obtenida con baja precisión (±${Math.round(precision)}m)`);
                }
            } else {
                if (typeof Toast !== 'undefined') {
                    Toast.success(`Ubicación GPS confirmada (±${Math.round(precision)}m)`);
                }
            }
            
            // ✅ 3. Cerrar modal
            cerrarModalUbicacion();
            
            // ✅ 4. Actualizar GPS Tracker con múltiples reintentos
            let intentos = 0;
            const maxIntentos = 5;

            const actualizarConReintentos = () => {
                intentos++;
                console.log(`🔄 Intento ${intentos}/${maxIntentos} de actualizar ubicación...`);
                
                if (gpsTracker) {
                    gpsTracker.activarDesdeHeader(position);
                    gpsTracker.actualizarUbicacionBarra();
                    
                    // Verificar si se actualizó
                    const btnEl = document.getElementById('btnUbicacionBarra');
                    if (btnEl && btnEl.classList.contains('ubicacion-activa')) {
                        console.log('✅ Ubicación actualizada correctamente');
                        return;
                    }
                }
                
                // Reintentar si falla y no se alcanzó el máximo
                if (intentos < maxIntentos) {
                    setTimeout(actualizarConReintentos, 500);
                } else {
                    console.error('❌ No se pudo actualizar la ubicación después de', maxIntentos, 'intentos');
                }
            };

            setTimeout(actualizarConReintentos, 200);
            
            console.log('✅ Proceso de ubicación completado');
        },
        (error) => {
            console.error('❌ Error de geolocalización:', error);
            
            let mensaje = 'No se pudo obtener la ubicación.';
            
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    mensaje = 'Permiso de ubicación denegado.';
                    break;
                case error.POSITION_UNAVAILABLE:
                    mensaje = 'Ubicación no disponible. Activa el GPS.';
                    break;
                case error.TIMEOUT:
                    mensaje = 'Tiempo de espera agotado.';
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
    console.log('═══════════════════════════════════════');
    console.log('🗺️ INICIANDO mostrarModalUbicacion()');
    console.log('═══════════════════════════════════════');
    
    const modal = document.getElementById('modalUbicacion');
    console.log('1. Modal encontrado?', modal ? 'SÍ' : 'NO');
    
    if (!modal) {
        console.error('❌ Modal no encontrado en el DOM');
        alert('Error: Modal de ubicación no encontrado');
        return;
    }
    
    const contenido = document.getElementById('contenidoUbicacion');
    console.log('2. Contenido encontrado?', contenido ? 'SÍ' : 'NO');
    
    console.log('3. Estado de ubicación:', estadoApp.ubicacion);
    
    if (estadoApp.ubicacion) {
        let html = `
            <div style="padding: 16px; background: rgba(34, 197, 94, 0.1); border-radius: 8px; margin-bottom: 12px;">
                <p style="color: #22c55e; font-weight: 600; margin-bottom: 8px;">✓ Ubicación compartida</p>
                <p style="font-size: 13px; color: #93c5fd;">Latitud: ${estadoApp.ubicacion.latitud.toFixed(6)}</p>
                <p style="font-size: 13px; color: #93c5fd;">Longitud: ${estadoApp.ubicacion.longitud.toFixed(6)}</p>
                <p style="font-size: 12px; color: #6b7280; margin-top: 8px;">Precisión: ±${Math.round(estadoApp.ubicacion.precision)}m</p>
            </div>
            <button class="btn-compartir-ubicacion" onclick="solicitarUbicacion()">Actualizar Ubicación</button>
        `;
        contenido.innerHTML = html;
    } else {
        contenido.innerHTML = `
            <button class="btn-compartir-ubicacion" onclick="solicitarUbicacion()">
                <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                </svg>
                Compartir Ubicación
            </button>
        `;
    }
    
    console.log('4. Contenido HTML actualizado');
    console.log('5. Clases del modal ANTES:', modal.className);
    
    // Mostrar modal
    modal.classList.remove('hidden');
    modal.classList.add('modal-activo');
    
    console.log('6. Clases del modal DESPUÉS:', modal.className);
    console.log('7. Modal visible?', !modal.classList.contains('hidden'));
    console.log('✅ mostrarModalUbicacion() COMPLETADA');
    console.log('═══════════════════════════════════════');

}

function cerrarModalUbicacion() {
    console.log('🚪 Cerrando modal de ubicación');
    const modal = document.getElementById('modalUbicacion');
    if (modal) {
        modal.classList.remove('modal-activo');
        modal.classList.add('hidden');
        console.log('✅ Modal cerrado');
    }
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
        // ✅ USAR ESTO (funciona en local Y Railway):
        const url = `/api/clientes/buscar?q=${encodeURIComponent(query)}`;
        
        console.log('🔍 Buscando cliente:', query);
        
        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${estadoApp.token}` }
        });
        
        if (response.ok) {
            const resultado = await response.json();
            console.log('📦 Resultado:', resultado);
            
            // El endpoint de main.py retorna { success: true, data: [...] }
            const clientes = resultado.success ? resultado.data : [];
            mostrarResultadosClientes(clientes);
        } else {
            console.error('❌ Error:', response.status);
            ocultarDropdownClientes();
        }
    } catch (error) {
        console.error('❌ Error:', error);
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

async function seleccionarCliente(cliente) {
    console.log('🎯 Seleccionando cliente:', cliente);
    
    // ============================================
    // 1. NORMALIZAR ESTRUCTURA DEL CLIENTE
    // ============================================
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

    estadoApp.clienteSeleccionado = clienteNormalizado;
    
    // 2. OCULTAR BÚSQUEDA DE CLIENTE
    const busquedaWrapper = document.getElementById('busquedaClienteWrapper');
    if (busquedaWrapper) {
        busquedaWrapper.classList.add('hidden');
        console.log('✅ Búsqueda de cliente ocultada');
    }
    
    // ============================================
    // 3. MOSTRAR SOLO UN CHIP (EL PRINCIPAL)
    // ============================================
    
        
    // Chip del header (NO mostrarlo, usar solo para info de crédito)
    const chipHeader = document.getElementById('chipClienteHeader');
    if (chipHeader) {
        const nombreHeader = document.getElementById('chipClienteNombreHeader');
        const tipoHeader = document.getElementById('chipClienteTipoHeader');
        
        if (nombreHeader) nombreHeader.textContent = clienteNormalizado.nombre_completo;
        if (tipoHeader) tipoHeader.textContent = clienteNormalizado.tipo_cliente_nombre;
        
        chipHeader.classList.remove('hidden');
        console.log('✅ Chip header actualizado');
    }
    
    // 4. MOSTRAR TOGGLE CONTADO/CRÉDITO
    const togglePago = document.getElementById('togglePagoHeader');
    if (togglePago) {
        togglePago.classList.add('activo'); /* ✅ Usar clase activo */
        console.log('✅ Toggle pago mostrado');
    }
    
    // ============================================
    // 5. ACTIVAR BÚSQUEDA DE PRODUCTOS
    // ============================================
    const seccionBusqueda = document.querySelector('.seccion-busqueda-combinada');
    if (seccionBusqueda) {
        seccionBusqueda.classList.add('compacta');
        console.log('✅ Modo compacto activado');
    }
    
    const busquedaProductos = document.getElementById('busquedaProductos');
    if (busquedaProductos) {
        busquedaProductos.classList.remove('hidden');
        console.log('✅ Búsqueda de productos mostrada');
    }
    
    const inputProductos = document.getElementById('inputProductos');
    const micBrowser = document.getElementById('micBrowser');
    const micGoogle = document.getElementById('micGoogle');
    
    if (inputProductos) {
        inputProductos.disabled = false;
        console.log('✅ Input productos habilitado');
    }
    if (micBrowser) micBrowser.disabled = false;
    if (micGoogle) micGoogle.disabled = false;
    
    setTimeout(() => {
        if (inputProductos) {
            inputProductos.focus();
            inputProductos.select();
        }
    }, 100);
    
    // ============================================
    // 6. MOSTRAR FOOTER CON COMPARACIÓN
    // ============================================
    const footerComparacion = document.getElementById('footerComparacion');
    if (footerComparacion) {
        footerComparacion.classList.remove('hidden');
        console.log('✅ Footer comparación mostrado');
    }
    
    // ============================================
    // 7. CARGAR INFO CREDITICIA
    // ============================================
    if (preciosManager) {
        preciosManager.clienteActual = clienteNormalizado;
        await preciosManager.cargarInfoCredito(clienteNormalizado.id);
        
        // Actualizar comparación si hay productos
        if (estadoApp.pedido && estadoApp.pedido.length > 0) {
            preciosManager.productosCarrito = estadoApp.pedido.map(item => ({
                producto_id: item.producto_id,
                cantidad: item.cantidad
            }));
            await preciosManager.actualizarComparacion();
        }
        
        console.log('✅ Info crediticia cargada');
    }
    
    // ============================================
    // 8. VERIFICAR UBICACIÓN
    // ============================================
    if (!estadoApp.ubicacion) {
        setTimeout(() => {
            if (typeof Toast !== 'undefined') {
                Toast.warning('Comparte tu ubicación para poder enviar el pedido');
            }
            mostrarModalUbicacion();
        }, 500);
    } else {
        if (typeof Toast !== 'undefined') {
            Toast.success(`Cliente ${clienteNormalizado.nombre_completo} seleccionado`);
        }
    }
    
    console.log('✅ Cliente seleccionado correctamente');
}

function cambiarCliente() {
    console.log('🔄 Cambiando de cliente...');
    
    if (estadoApp.pedido.length > 0) {
        if (!confirm('¿Deseas cambiar de cliente? Se perderá el pedido actual.')) {
            return;
        }
    }
    
    // ============================================
    // 1. LIMPIAR ESTADO
    // ============================================
    estadoApp.clienteSeleccionado = null;
    estadoApp.pedido = [];
    estadoApp.productosSeleccionados.clear();

    // ✅ LIMPIAR DROPDOWN DE CLIENTES
    const dropdownClientes = document.getElementById('dropdownClientes');
    if (dropdownClientes) {
        dropdownClientes.classList.add('hidden');
        dropdownClientes.innerHTML = '';
    }

    // ✅ LIMPIAR INPUT
    const inputBusquedaCliente = document.getElementById('inputBusquedaCliente');
    if (inputBusquedaCliente) {
        inputBusquedaCliente.value = '';
    }
    
    // 2. MOSTRAR BÚSQUEDA DE CLIENTE
    const busquedaWrapper = document.getElementById('busquedaClienteWrapper');
    if (busquedaWrapper) {
        busquedaWrapper.classList.remove('hidden');
        console.log('✅ Búsqueda de cliente mostrada');
    }
    
    // ============================================
    // 3. OCULTAR CHIPS
    // ============================================
        
    const chipHeader = document.getElementById('chipClienteHeader');
    if (chipHeader) chipHeader.classList.add('hidden');
    
    // 4. OCULTAR TOGGLE Y FOOTER
    const togglePago = document.getElementById('togglePagoHeader');
    if (togglePago) {
        togglePago.classList.remove('activo');
        togglePago.classList.add('hidden');
    }
    
    const footerComparacion = document.getElementById('footerComparacion');
    if (footerComparacion) footerComparacion.classList.add('hidden');
    
    // ============================================
    // 5. OCULTAR BÚSQUEDA DE PRODUCTOS
    // ============================================
    const busquedaProductos = document.getElementById('busquedaProductos');
    if (busquedaProductos) busquedaProductos.classList.add('hidden');
    
    const inputProductos = document.getElementById('inputProductos');
    const micBrowser = document.getElementById('micBrowser');
    const micGoogle = document.getElementById('micGoogle');
    
    if (inputProductos) {
        inputProductos.disabled = true;
        inputProductos.value = '';
    }
    if (micBrowser) micBrowser.disabled = true;
    if (micGoogle) micGoogle.disabled = true;
    
    // ============================================
    // 6. LIMPIAR PRODUCTOS Y PRECIOS
    // ============================================
    const productosContainer = document.getElementById('productosContainer');
    if (productosContainer) productosContainer.classList.add('hidden');
    
    ocultarDropdownProductos();
    
    if (preciosManager) {
        preciosManager.limpiar();
    }
    
    console.log('✅ Cliente cambiado correctamente');
}


function seleccionarTipoPago(tipo) {
    console.log('💳 Tipo de pago seleccionado:', tipo);
    
    // ✅ Actualizar estado global
    estadoApp.tipoPagoSeleccionado = tipo;
    
    // ✅ Llamar al método de la clase (nombre correcto)
    if (preciosManager) {
        preciosManager.seleccionarTipoPago(tipo);  // ✅ Este método SÍ existe
    }
    
    console.log('✅ Tipo de pago actualizado');
}

// BÚSQUEDA DE PRODUCTOS
async function buscarProductos(query) {
    try {
        // ✅ Solo agregar parámetro SI existe cliente actual
        const tipoClienteId = estadoApp.clienteActual?.tipo_cliente_id;
        
        let url = `/api/productos/buscar?q=${encodeURIComponent(query)}`;
        
        // ✅ Solo agregar si tiene valor
        if (tipoClienteId) {
            url += `&tipo_cliente_id=${tipoClienteId}`;
        }
        
        console.log('🔍 Buscando con URL:', url);
        
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
        window['producto_' + producto.id] = producto;
        
        const estaEnPedido = estadoApp.pedido.some(item => item.producto_id === producto.id);
        const estaSeleccionado = estadoApp.productosSeleccionados.has(producto.id);
        
        // ✅ Determinar estado de stock
        const stock = producto.stock_disponible || 0;
        let stockClase = '';
        let stockIcono = '📦';
        
        if (stock === 0) {
            stockClase = 'sin-stock';
            stockIcono = '❌';
        } else if (stock < 10) {
            stockClase = 'stock-bajo';
            stockIcono = '⚠️';
        }
        
        html += `
            <div class="item-producto-dropdown ${estaSeleccionado ? 'seleccionado' : ''} ${estaEnPedido ? 'ya-agregado' : ''} ${stockClase}" 
                 onclick="if(!${estaEnPedido} && ${stock} > 0) toggleSeleccionProducto(${producto.id})">
                <input 
                    type="checkbox" 
                    class="producto-checkbox"
                    ${estaSeleccionado ? 'checked' : ''}
                    ${estaEnPedido || stock === 0 ? 'disabled' : ''}
                    onclick="event.stopPropagation()"
                    onchange="if(${stock} > 0) toggleSeleccionProducto(${producto.id})"
                />
                <div class="producto-dropdown-info">
                    <div class="producto-dropdown-nombre">${producto.nombre}</div>
                    <div class="producto-dropdown-detalles">
                        <span>Código: ${producto.codigo_producto}</span>
                        ${producto.categoria ? `<span>• ${producto.categoria}</span>` : ''}
                        <span class="stock-badge ${stockClase}">
                            ${stockIcono} ${stock} ${stock === 1 ? 'und' : 'unds'}
                        </span>
                    </div>
                    ${estaEnPedido ? '<div class="producto-ya-agregado">Ya está en el pedido</div>' : ''}
                    ${stock === 0 ? '<div class="producto-sin-stock">SIN STOCK</div>' : ''}
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

// 1️⃣ En agregarProductosSeleccionados() - AGREGAR AL FINAL
async function agregarProductosSeleccionados() {
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
                esNuevo: true
            });
        }
    });
    
    if (nuevosProductos.length > 0) {
        estadoApp.pedido.unshift(...nuevosProductos);
        estadoApp.productosSeleccionados.clear();
        ocultarDropdownProductos();
        mostrarProductosPedido();
        
        Toast.success(`${nuevosProductos.length} producto${nuevosProductos.length > 1 ? 's agregados' : ' agregado'} al pedido`);
        
        // ✅ Primero recalcular precios con API
        if (preciosManager) {
            await preciosManager.recalcularPreciosCarrito();
        }
        
        // 🎤 Luego anunciar total CORRECTO
        announceTotal();
        
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

// 2️⃣ En actualizarItemsDelPedido() - AGREGAR AL FINAL
function actualizarItemsDelPedido(nuevosProductos) {
    nuevosProductos.forEach(producto => {
        const index = estadoApp.pedido.findIndex(item => item.producto_id === producto.producto_id);
        
        if (index >= 0) {
            estadoApp.pedido[index].cantidad += producto.cantidad;
            estadoApp.pedido[index].subtotal = estadoApp.pedido[index].cantidad * estadoApp.pedido[index].precio_unitario;
        } else {
            estadoApp.pedido.push(producto);
        }
    });
    
    mostrarProductosPedido();
    
    // 🎤 AGREGAR ESTO:
    announceTotal();
}

function mostrarProductosPedido() {
    const container = document.getElementById('productosContainer');
    const lista = document.getElementById('listaProductos');
    
    if (estadoApp.pedido.length === 0) {
        container.classList.add('hidden');

        // ✅ Limpiar también la comparación
        if (preciosManager) {
            document.getElementById('totalCreditoComparacion').textContent = 'S/ 0.00';
            document.getElementById('totalContadoComparacion').textContent = 'S/ 0.00';
            document.getElementById('ahorroMonto').textContent = 'S/ 0.00';
        }
        return;
    }
    
    // Mostrar contenedor
    container.classList.remove('hidden');
    
    // Limpiar lista antes de renderizar
    lista.innerHTML = '';
    
    // ✅ Variable para acumular total
    let total = 0;
    
    // Renderizar cada producto
    estadoApp.pedido.forEach((item, index) => {
        const div = document.createElement('div');
        div.className = 'producto-item';
        
        // Agregar clase 'nuevo' para animación
        if (item.esNuevo) {
            div.classList.add('nuevo');
            delete item.esNuevo;
        }
        
        // ✅ Generar stock aleatorio si no existe (temporal)
        const producto = window['producto_' + item.producto_id];
        if (!producto.stock_disponible) {
            producto.stock_disponible = Math.floor(Math.random() * (500 - 50 + 1)) + 50; // Entre 50 y 500
        }
        const stock = producto.stock_disponible;
        
        // ✅ Determinar estado de stock
        let stockHTML = '';
        let stockClase = '';
        let btnMasDisabled = '';
        
        if (stock === 0) {
            stockHTML = '<div class="stock-info sin-stock">❌ Sin stock</div>';
            stockClase = 'sin-stock';
            btnMasDisabled = 'disabled';
        } else if (stock < 10) {
            stockHTML = `<div class="stock-info stock-bajo">⚠️ Quedan ${stock}</div>`;
            stockClase = 'stock-bajo';
            btnMasDisabled = item.cantidad >= stock ? 'disabled' : '';
        } else if (stock < 50) {
            stockHTML = `<div class="stock-info stock-medio">📦 ${stock} disponibles</div>`;
            btnMasDisabled = item.cantidad >= stock ? 'disabled' : '';
        } else {
            stockHTML = `<div class="stock-info stock-ok">✅ ${stock} disponibles</div>`;
            btnMasDisabled = item.cantidad >= stock ? 'disabled' : '';
        }
        
        div.innerHTML = `
            <div class="producto-info">
                <div class="producto-nombre">${item.nombre}</div>
                <div class="producto-codigo">${item.codigo_producto}</div>
                ${stockHTML}
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
                    max="${stock}"
                    onchange="actualizarCantidadDirecta(${index}, this.value)"
                    onclick="this.select()"
                />
                <button class="btn-cantidad" onclick="cambiarCantidad(${index}, 1)" ${btnMasDisabled}>
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
        
        // ✅ Acumular total
        total += item.subtotal;
    });

    // ✅ Actualizar total en UI
    document.getElementById('totalPedido').textContent = `S/ ${total.toFixed(2)}`;

    // ✅ Actualizar manager de precios
    if (preciosManager && estadoApp.clienteSeleccionado) {
        // Actualizar array de productos del manager
        preciosManager.productosCarrito = estadoApp.pedido.map(item => ({
            producto_id: item.producto_id,
            cantidad: item.cantidad
        }));
        
        // Actualizar total
        preciosManager.actualizarTotalPedido();
        
        // Actualizar comparación CRÉDITO vs CONTADO
        preciosManager.actualizarComparacion();
    }
}


// 4️⃣ En actualizarCantidadDirecta() - AGREGAR
function actualizarCantidadDirecta(index, nuevaCantidadStr) {
    const nuevaCantidad = parseInt(nuevaCantidadStr);
    const item = estadoApp.pedido[index];
    const producto = window['producto_' + item.producto_id];
    const stock = producto?.stock_disponible || 999;
    
    // ✅ Validar entrada
    if (isNaN(nuevaCantidad) || nuevaCantidad < 1) {
        Toast.warning('Cantidad mínima: 1');
        mostrarProductosPedido(); // Restaurar valor anterior
        return;
    }
    
    // ✅ Validar stock
    if (nuevaCantidad > stock) {
        Toast.warning(`⚠️ Solo hay ${stock} unidades disponibles`);
        mostrarProductosPedido(); // Restaurar valor anterior
        return;
    }
    
    // Actualizar
    item.cantidad = nuevaCantidad;
    item.subtotal = item.precio_unitario * nuevaCantidad;
    
    mostrarProductosPedido();
    
    if (preciosManager) {
        preciosManager.recalcularPreciosCarrito();
    }
}


// 6️⃣ En actualizarCantidad() - AGREGAR (si la usas)
function actualizarCantidad(productoId, nuevaCantidad) {
    if (nuevaCantidad < 1) return;
    
    const producto = estadoApp.pedido.find(p => p.producto_id === productoId);
    if (producto) {
        producto.cantidad = nuevaCantidad;
        producto.subtotal = producto.cantidad * producto.precio_unitario;
        mostrarProductosPedido();
        
        // 🎤 AGREGAR ESTO:
        announceTotal();
    }
}

// 3️⃣ En cambiarCantidad() - MODIFICAR
function cambiarCantidad(index, delta) {
    const item = estadoApp.pedido[index];
    const producto = window['producto_' + item.producto_id];
    const stock = producto?.stock_disponible || 999;
    
    const nuevaCantidad = item.cantidad + delta;
    
    // ✅ Validar límites
    if (nuevaCantidad < 1) {
        eliminarProducto(index);
        return;
    }
    
    // ✅ Validar stock
    if (nuevaCantidad > stock) {
        Toast.warning(`⚠️ Solo hay ${stock} unidades disponibles`);
        return;
    }
    
    // Actualizar cantidad
    item.cantidad = nuevaCantidad;
    item.subtotal = item.precio_unitario * nuevaCantidad;
    
    mostrarProductosPedido();
    
    // Recalcular totales
    if (preciosManager) {
        preciosManager.recalcularPreciosCarrito();
    }
}

// 5️⃣ En eliminarProducto() - AGREGAR
function eliminarProducto(index) {
    const item = estadoApp.pedido[index];
    
    // Remover del array
    estadoApp.pedido.splice(index, 1);
    
    // Actualizar UI
    mostrarProductosPedido();
    
    // ✅ Actualizar manager de precios
    if (preciosManager && item) {
        const indexManager = preciosManager.productosCarrito.findIndex(
            p => p.producto_id === item.producto_id
        );
        
        if (indexManager !== -1) {
            preciosManager.productosCarrito.splice(indexManager, 1);
        }
        
        preciosManager.recalcularPreciosCarrito();
        preciosManager.actualizarComparacion();
    }
    
    Toast.info('Producto eliminado del pedido');
    announceTotal();
}

function limpiarPedido() {
    if (confirm('¿Deseas limpiar todos los productos del pedido?')) {
        estadoApp.pedido = [];
        mostrarProductosPedido();
    }

    // ✅ AGREGAR: Limpiar manager
    if (preciosManager) {
        preciosManager.productosCarrito = [];
        preciosManager.actualizarComparacion();
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
        Toast.warning('Por favor, comparte tu ubicación');
        mostrarModalUbicacion();
        return;
    }
    
    // ✅ VERIFICAR que los elementos existan antes de usarlos
    const resumenCliente = document.getElementById('resumenCliente');
    const totalPedidoModal = document.getElementById('totalPedidoModal');
    const alertCoincidencia = document.getElementById('alertCoincidencia');
    
    console.log('Elementos del modal:', {
        resumenCliente: resumenCliente ? 'existe' : 'NO EXISTE',
        totalPedidoModal: totalPedidoModal ? 'existe' : 'NO EXISTE',
        alertCoincidencia: alertCoincidencia ? 'existe' : 'NO EXISTE'
    });
    
    // Solo actualizar si existen
    if (resumenCliente) {
        resumenCliente.textContent = 
            `${estadoApp.clienteSeleccionado.nombre_completo} - RUC: ${estadoApp.clienteSeleccionado.ruc}`;
    }
    
    // Calcular y mostrar total
    const total = estadoApp.pedido.reduce((sum, item) => sum + item.subtotal, 0);
    if (totalPedidoModal) {
        totalPedidoModal.textContent = `S/ ${total.toFixed(2)}`;
    }
    
    // Calcular coincidencia de ubicación
    if (alertCoincidencia && estadoApp.clienteSeleccionado.latitud && estadoApp.clienteSeleccionado.longitud) {
        const distancia = calcularDistancia(
            estadoApp.ubicacion.latitud,
            estadoApp.ubicacion.longitud,
            estadoApp.clienteSeleccionado.latitud,
            estadoApp.clienteSeleccionado.longitud
        );
        
        const porcentaje = calcularPorcentajeCoincidencia(distancia);
        
        let colorBg = '';
        let colorTexto = '';
        
        if (porcentaje >= 80) {
            colorBg = 'rgba(34, 197, 94, 0.1)';
            colorTexto = '#22c55e';
        } else if (porcentaje >= 50) {
            colorBg = 'rgba(251, 191, 36, 0.1)';
            colorTexto = '#fbbf24';
        } else {
            colorBg = 'rgba(239, 68, 68, 0.1)';
            colorTexto = '#ef4444';
        }
        
        alertCoincidencia.style.display = 'block';
        alertCoincidencia.style.background = colorBg;
        alertCoincidencia.style.borderRadius = '8px';
        alertCoincidencia.style.padding = '12px';
        alertCoincidencia.style.color = colorTexto;
        alertCoincidencia.innerHTML = `
            <strong>📍 Verificación de ubicación:</strong><br>
            Distancia a la bodega: ${distancia.toFixed(0)}m | Coincidencia: ${porcentaje}%
        `;
    } else if (alertCoincidencia) {
        alertCoincidencia.style.display = 'none';
    }
    
    // Abrir modal
    const modal = document.getElementById('modalConfirmarPedido');
    if (modal) {
        console.log('Abriendo modal confirmar pedido...');
        modal.classList.remove('hidden');
        modal.classList.add('modal-activo');
    } else {
        console.error('❌ Modal modalConfirmarPedido NO EXISTE');
        Toast.error('Error: Modal no encontrado');
    }
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
        const response = await fetch(`/api/clientes/validar-ruc/${ruc}`, {
            headers: { 'Authorization': `Bearer ${estadoApp.token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('nuevaRazonSocial').value = data.razon_social || '';
                
                // ✅ NUEVO: Detectar si es persona natural
                if (data.direccion) {
                    // Persona jurídica: llenar todos los campos
                    document.getElementById('nuevaDireccion').value = data.direccion;
                    document.getElementById('nuevoDistrito').value = data.distrito || '';
                    document.getElementById('nuevaProvincia').value = data.provincia || '';
                    document.getElementById('nuevaRegion').value = data.departamento || '';
                    
                    resultado.className = 'validation-message success';
                    resultado.textContent = '✓ RUC válido - Datos cargados';
                } else {
                    // Persona natural: limpiar y permitir ingreso manual
                    document.getElementById('nuevaDireccion').value = '';
                    document.getElementById('nuevaDireccion').removeAttribute('readonly');
                    document.getElementById('nuevoDistrito').value = '';
                    document.getElementById('nuevaProvincia').value = '';
                    document.getElementById('nuevaRegion').value = '';
                    
                    resultado.className = 'validation-message info';
                    resultado.textContent = '✓ RUC válido - Ingresa la dirección manualmente';
                    
                    Toast.info('RUC de persona natural. Ingresa la dirección del negocio');
                }
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

/*
function mostrarModalPedidos() {
    Toast.info('Modal de Pedidos del día - En desarrollo');
}
*/

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
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('modal-activo');  // ✅ Agregar esta línea
    }
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
let cargandoPedidos = false;

async function mostrarModalPedidos() {
    console.log('═══════════════════════════════════════');
    console.log('📦 INICIANDO mostrarModalPedidos()');
    console.log('═══════════════════════════════════════');
    
    if (cargandoPedidos) {
        console.log('⏳ Ya se está cargando, saliendo...');
        return;
    }
    
    const modal = document.getElementById('modalPedidos');
    console.log('1. Modal encontrado?', modal ? 'SÍ' : 'NO');
    
    if (!modal) {
        console.error('❌ Modal no encontrado en el DOM');
        alert('Error: Modal de pedidos no encontrado');
        return;
    }
    
    console.log('2. Clases del modal ANTES:', modal.className);
    
    modal.classList.remove('hidden');
    modal.classList.add('modal-activo');  // ✅ Agregar esta línea
    
    console.log('3. Clases del modal DESPUÉS:', modal.className);
    console.log('4. Modal visible?', !modal.classList.contains('hidden'));
    
    cargandoPedidos = true;
    console.log('5. Iniciando carga de pedidos...');
    
    try {
        await cargarPedidosHoy();
        console.log('✅ Carga completada');
    } catch (error) {
        console.error('❌ Error en carga:', error);
    } finally {
        cargandoPedidos = false;
    }
    
    console.log('═══════════════════════════════════════');
}

async function cargarPedidosHoy() {
    console.log('─────────────────────────────────────');
    console.log('📊 INICIANDO cargarPedidosHoy()');
    console.log('─────────────────────────────────────');
    
    const token = estadoApp.token;
    console.log('1. Token disponible?', token ? 'SÍ' : 'NO');
    
    if (!token) {
        console.error('❌ No hay token');
        document.getElementById('listaPedidosHoy').innerHTML = 
            '<p style="text-align:center;color:#ef4444;padding:40px;">Sesión expirada. Recarga la página.</p>';
        return;
    }
    
    console.log('2. Haciendo fetch a /api/vendedor/estadisticas/pedidos-hoy');
    
    try {
        const response = await fetch('/api/vendedor/estadisticas/pedidos-hoy', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        console.log('3. Response status:', response.status);
        console.log('4. Response ok?', response.ok);
        
        if (response.ok) {
            const data = await response.json();
            console.log('5. Data recibida:', data);
            console.log('6. data.success?', data.success);
            console.log('7. data.data:', data.data);
            
            if (data.success) {
                console.log('8. Llamando a mostrarPedidosEnModal...');
                mostrarPedidosEnModal(data.data);
            } else {
                console.error('❌ data.success es false');
                document.getElementById('listaPedidosHoy').innerHTML = 
                    `<p style="text-align:center;color:#ef4444;padding:40px;">Error: ${data.message || 'No se pudieron cargar los pedidos'}</p>`;
            }
        } else {
            console.error('❌ Response no ok');
            const errorText = await response.text();
            console.error('Error text:', errorText);
            document.getElementById('listaPedidosHoy').innerHTML = 
                '<p style="text-align:center;color:#ef4444;padding:40px;">Error al cargar pedidos</p>';
        }
    } catch (error) {
        console.error('❌ Exception:', error);
        console.error('Stack:', error.stack);
        document.getElementById('listaPedidosHoy').innerHTML = 
            '<p style="text-align:center;color:#ef4444;padding:40px;">Error de conexión</p>';
    }
    
    console.log('─────────────────────────────────────');
}

function mostrarPedidosEnModal(pedidos) {
    console.log('─────────────────────────────────────');
    console.log('🎨 INICIANDO mostrarPedidosEnModal()');
    console.log('🎨 Pedidos recibidos:', pedidos);
    console.log('🎨 Cantidad:', pedidos?.length);
    console.log('─────────────────────────────────────');
    
    // Calcular estadísticas
    const total = pedidos.length;
    const totalVentas = pedidos.reduce((sum, p) => sum + p.total, 0);
    const pendientes = pedidos.filter(p => p.estado === 'pendiente_aprobacion').length;
    
    console.log('Stats calculadas:', { total, totalVentas, pendientes });
    
    document.getElementById('totalPedidosHoy').textContent = total;
    document.getElementById('totalVentasHoy').textContent = `S/ ${totalVentas.toFixed(2)}`;
    document.getElementById('pendientesHoy').textContent = pendientes;
    
    // Mostrar lista
    const lista = document.getElementById('listaPedidosHoy');
    console.log('Lista elemento encontrado?', lista ? 'SÍ' : 'NO');
    
    if (pedidos.length === 0) {
        lista.innerHTML = '<p style="text-align:center;color:#93c5fd;padding:40px;">No hay pedidos hoy</p>';
        console.log('✅ Mostrando mensaje vacío');
        return;
    }
    
    const html = pedidos.map(p => `
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
    
    console.log('HTML generado (primeros 200 chars):', html.substring(0, 200));
    
    lista.innerHTML = html;
    
    console.log('✅ mostrarPedidosEnModal() COMPLETADA');
    console.log('─────────────────────────────────────');
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




// ============================================
// CALLBACK: Cliente recién creado
// ============================================

window.onClienteCreado = function(clienteData) {
    console.log('✅ Cliente creado, seleccionando automáticamente:', clienteData);
    
    // Normalizar datos del cliente recién creado
    const clienteNormalizado = {
        id: clienteData.id,
        codigo_cliente: clienteData.codigo_cliente,
        nombre_comercial: clienteData.nombre_comercial,
        razon_social: clienteData.razon_social,
        ruc: clienteData.ruc,
        telefono: clienteData.telefono,
        email: clienteData.email || '',
        direccion: clienteData.direccion_completa,
        distrito: clienteData.distrito,
        provincia: clienteData.provincia,
        departamento: clienteData.departamento,
        latitud: clienteData.latitud || null,
        longitud: clienteData.longitud || null,
        tipo_cliente_id: clienteData.tipo_cliente_id,
        tipo_cliente_nombre: 'Cliente', // Se podría mejorar consultando el tipo
        nombre_completo: clienteData.nombre_comercial || clienteData.razon_social
    };
    
    // Usar la función existente de selección
    seleccionarCliente(clienteNormalizado);
    
    // Mensaje de éxito
    Toast.success(`¡Cliente ${clienteData.codigo_cliente} seleccionado! Ya puedes agregar productos.`);
    
    // Enfocar en búsqueda de productos
    setTimeout(() => {
        const inputProductos = document.getElementById('inputProductos');
        if (inputProductos) {
            inputProductos.focus();
        }
    }, 500);
};
// FIN DEL ARCHIVO