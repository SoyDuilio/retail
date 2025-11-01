// ============================================
// GPS TRACKER - TRAZABILIDAD EN TIEMPO REAL
// ============================================

class GPSTracker {
    constructor() {
        this.isTracking = false;
        this.intervalId = null;
        this.watchId = null;
        this.ultimaUbicacion = null;
        this.intentosFallidos = 0;
        this.maxIntentosFallidos = 3;
        
        // Configuración
        this.config = {
            intervaloMs: 5 * 60 * 1000, // 5 minutos
            enableHighAccuracy: true,
            timeout: 15000, // ✅ Reducido de 30s a 15s
            maximumAge: 30000 // ✅ Aceptar caché de 30s
        };
        
        this.init();
    }
    
    init() {
        console.log('🛰️ Inicializando GPS Tracker...');
        this.crearWidget();
        this.crearBarraInferior(); // ✅ AGREGAR AQUÍ
        
        // ✅ Solo iniciar si el usuario ya dio permisos en el login
        if (estadoApp?.ubicacion?.latitud) {
            console.log('✅ Ubicación ya capturada en login, iniciando tracking');
            this.iniciarTracking();
            setTimeout(() => this.actualizarUbicacionBarra(), 200); // ✅ Con delay
        } else {
            console.log('⏸️ Esperando que el usuario autorice ubicación desde el header');
            this.actualizarEstadoWidget('waiting');
        }
    }
    
    // ✅ NUEVO: Método para activar desde el header
    activarDesdeHeader(ubicacion) {
        console.log('▶️ Activando GPS Tracker desde header');
        this.ultimaUbicacion = ubicacion;
        this.actualizarWidget(ubicacion);
        this.iniciarTracking();
    }
    
    crearWidget() {
        const widget = document.createElement('div');
        widget.id = 'gpsTrackerWidget';
        widget.className = 'gps-tracker-widget minimized';
        widget.innerHTML = `
            <div class="gps-widget-content">
                <!-- Versión minimizada -->
                <div class="gps-minimized">
                    <div class="gps-pulse-container">
                        <svg class="gps-icon" width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                            <circle cx="12" cy="10" r="3"/>
                        </svg>
                        <div class="gps-pulse-ring"></div>
                    </div>
                    <span class="gps-text-min">GPS</span>
                </div>
                
                <!-- Versión expandida -->
                <div class="gps-expanded">
                    <!-- ✅ NUEVO: Info de vendedor -->
                    
                    
                    <div class="gps-header-exp">
                        <div class="gps-pulse-container">
                            <svg class="gps-icon" width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                                <circle cx="12" cy="10" r="3"/>
                            </svg>
                            <div class="gps-pulse-ring"></div>
                        </div>
                        <div class="gps-title-group">
                            <span class="gps-title">GPS Tracking</span>
                            <span class="gps-subtitle" id="gpsStatus">Esperando...</span>
                        </div>
                    </div>
                    
                    <!-- ✅ Info de ubicación actual -->
                    <div class="gps-ubicacion-actual" id="gpsUbicacionActual">
                        <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                        </svg>
                        <span id="gpsUbicacionTexto">Sin ubicación</span>
                    </div>
                    
                    <div class="gps-stats-grid">
                        <div class="gps-stat-item">
                            <div class="stat-icon">📍</div>
                            <div class="stat-info">
                                <span class="stat-label">Precisión</span>
                                <span class="stat-value" id="gpsPrecision">--</span>
                            </div>
                        </div>
                        
                        <div class="gps-stat-item">
                            <div class="stat-icon">🔋</div>
                            <div class="stat-info">
                                <span class="stat-label">Batería</span>
                                <span class="stat-value" id="gpsBateria">--</span>
                            </div>
                        </div>
                        
                        <div class="gps-stat-item">
                            <div class="stat-icon">📡</div>
                            <div class="stat-info">
                                <span class="stat-label">Señal</span>
                                <span class="stat-value" id="gpsSenal">--</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="gps-footer">
                        <svg class="icon-clock" width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <circle cx="12" cy="12" r="10"/>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6l4 2"/>
                        </svg>
                        <span id="gpsUltimaActualizacion">Esperando autorización...</span>
                    </div>
                </div>
                
                <!-- Botón toggle -->
                <button class="gps-toggle-btn" id="gpsToggleBtn">
                    <svg class="icon-expand" width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"/>
                    </svg>
                    <svg class="icon-collapse" width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                    </svg>
                </button>
            </div>
        `;
        
        document.body.appendChild(widget);
        
        // ✅ AGREGAR: Barra inferior con vendedor + ubicación
        //this.crearBarraInferior();
        
        // Event listeners
        document.getElementById('gpsToggleBtn').addEventListener('click', () => {
            widget.classList.toggle('minimized');
        });
        
        // ✅ Cargar info del vendedor
        
    }

    crearBarraInferior() {
        const barra = document.createElement('div');
        barra.id = 'barraInferiorVendedor';
        barra.className = 'barra-inferior-vendedor';
        barra.innerHTML = `
            <div class="barra-content">
                <!-- Datos del vendedor -->
                <div class="vendedor-info-barra">
                    <div class="vendedor-avatar-barra">
                        <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                        </svg>
                    </div>
                    <div class="vendedor-texto-barra">
                        <span class="vendedor-nombre-barra" id="vendedorNombreBarra">Cargando...</span>
                        <span class="vendedor-codigo-barra" id="vendedorCodigoBarra">ID: --</span>
                    </div>
                </div>
                
                <!-- Botón Ubicación -->
                <button class="btn-ubicacion-barra" id="btnUbicacionBarra" onclick="mostrarModalUbicacion()">
                    <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                    </svg>
                    <span id="estadoUbicacionBarra">Sin ubicación</span>
                </button>
            </div>
        `;
        
        document.body.appendChild(barra);

        // ✅ Forzar múltiples intentos de carga
        let intentosCarga = 0;
        const cargarConReintentos = () => {
            intentosCarga++;
            console.log(`👤 Intento ${intentosCarga}/5 de cargar datos vendedor...`);
            
            const nombreEl = document.getElementById('vendedorNombreBarra');
            const codigoEl = document.getElementById('vendedorCodigoBarra');
            
            if (!nombreEl || !codigoEl) {
                console.warn('⚠️ Elementos aún no existen, reintentando...');
                if (intentosCarga < 5) {
                    setTimeout(cargarConReintentos, 300);
                }
                return;
            }
            
            // Elementos existen, cargar datos
            this.cargarDatosVendedorBarra();
            this.actualizarUbicacionBarra();
        };

        // ✅ Múltiples intentos con intervalos
        let intentos = 0;
        const intervalo = setInterval(() => {
            intentos++;
            console.log(`🔄 Intento ${intentos} de actualizar datos vendedor...`);
            
            this.cargarDatosVendedorBarra();
            
            // Verificar si se actualizó
            const nombreEl = document.getElementById('vendedorNombreBarra');
            if (nombreEl && nombreEl.textContent !== 'Cargando...') {
                console.log('✅ Datos actualizados, deteniendo reintentos');
                clearInterval(intervalo);
            }
            
            if (intentos >= 10) {
                console.error('❌ No se pudo actualizar después de 10 intentos');
                clearInterval(intervalo);
            }
        }, 500);


    }

    cargarDatosVendedorBarra() {
        console.log('👤 Cargando datos vendedor en barra...');
        
        const userDataStr = localStorage.getItem('user_data');
        if (!userDataStr) {
            console.warn('⚠️ No hay user_data en localStorage');
            return;
        }
        
        try {
            const userData = JSON.parse(userDataStr);
            console.log('📦 User data:', userData);
            
            // ✅ Actualizar TODOS los elementos con ese ID (no solo el primero)
            const nombresEl = document.querySelectorAll('#vendedorNombreBarra');
            const codigosEl = document.querySelectorAll('#vendedorCodigoBarra');

            if (nombresEl.length === 0 || codigosEl.length === 0) {
                console.error('❌ Elementos NO encontrados');
                setTimeout(() => this.cargarDatosVendedorBarra(), 500);
                return;
            }

            console.log(`✅ Encontrados ${nombresEl.length} elementos nombre y ${codigosEl.length} elementos código`);

            // ✅ Actualizar TODOS
            nombresEl.forEach((nombreEl, index) => {
                console.log(`   Actualizando elemento ${index + 1}`);
                nombreEl.textContent = userData.nombre || 'Vendedor';
                nombreEl.setAttribute('style', 'color: white !important; display: block !important; opacity: 1 !important; visibility: visible !important; font-size: 0.85rem; font-weight: 600;');
            });

            codigosEl.forEach((codigoEl, index) => {
                codigoEl.textContent = `ID: ${userData.id || '--'}`;
                codigoEl.setAttribute('style', 'color: rgba(255, 255, 255, 0.6) !important; display: block !important; opacity: 1 !important; visibility: visible !important; font-size: 0.7rem;');
            });
            
            if (!nombreEl || !codigoEl) {
                console.error('❌ Elementos vendedorNombreBarra o vendedorCodigoBarra no encontrados');
                return;
            }
            
            // ✅ Usar los campos correctos del objeto
            nombreEl.textContent = userData.nombre || 'Vendedor';
            nombreEl.style.cssText = 'color: white !important; display: block !important; opacity: 1 !important; visibility: visible !important; font-size: 0.85rem; font-weight: 600;';

            codigoEl.textContent = `ID: ${userData.id || '--'}`;
            codigoEl.style.cssText = 'color: rgba(255, 255, 255, 0.6) !important; display: block !important; opacity: 1 !important; visibility: visible !important; font-size: 0.7rem;';

            console.log('✅ Datos vendedor con estilos forzados:', {
                nombre: nombreEl.textContent,
                codigo: codigoEl.textContent,
                nombreVisible: window.getComputedStyle(nombreEl).display !== 'none',
                codigoVisible: window.getComputedStyle(codigoEl).display !== 'none'
            });
            
        } catch (error) {
            console.error('❌ Error parseando user_data:', error);
        }
    }

    actualizarUbicacionBarra() {
        console.log('📍 === INICIANDO actualizarUbicacionBarra() ===');
        
        // ✅ Actualizar TODOS los elementos (no solo el primero)
        const estadosEl = document.querySelectorAll('#estadoUbicacionBarra');
        const botonesEl = document.querySelectorAll('#btnUbicacionBarra');

        if (estadosEl.length === 0 || botonesEl.length === 0) {
            console.warn('⚠️ Elementos no encontrados, reintentando en 500ms...');
            setTimeout(() => this.actualizarUbicacionBarra(), 500);
            return;
        }

        console.log(`   Encontrados ${botonesEl.length} botones y ${estadosEl.length} textos`);
        console.log('   estadoApp.ubicacion:', estadoApp?.ubicacion);
        
        if (estadoApp?.ubicacion?.latitud) {
            const precision = Math.round(estadoApp.ubicacion.precision || 0);
            
            // ✅ Actualizar TODOS los textos
            estadosEl.forEach((estadoEl, index) => {
                estadoEl.textContent = 'Ubicación';
                estadoEl.style.cssText = 'color: #86efac !important; display: inline !important; visibility: visible !important;';
                console.log(`   Texto ${index + 1} actualizado a "Ubicación"`);
            });
            
            // ✅ Actualizar TODOS los botones
            botonesEl.forEach((btnEl, index) => {
                btnEl.classList.remove('sin-ubicacion');
                btnEl.classList.add('ubicacion-activa');
                btnEl.title = `Precisión: ±${precision}m`;
                console.log(`   Botón ${index + 1} activado (verde)`);
            });
            
            console.log('✅ ÉXITO: Todos los botones en estado ACTIVO (verde)');
            
        } else {
            // ✅ Estado SIN ubicación - actualizar TODOS
            estadosEl.forEach((estadoEl, index) => {
                estadoEl.textContent = 'Sin ubicación';
                estadoEl.style.cssText = 'color: #fca5a5 !important; display: inline !important; visibility: visible !important;';
                console.log(`   Texto ${index + 1} actualizado a "Sin ubicación"`);
            });
            
            botonesEl.forEach((btnEl, index) => {
                btnEl.classList.remove('ubicacion-activa');
                btnEl.classList.add('sin-ubicacion');
                btnEl.title = 'Click para compartir ubicación';
                console.log(`   Botón ${index + 1} desactivado (rojo)`);
            });
            
            console.log('⚠️ Todos los botones en estado INACTIVO (rojo)');
        }
        
        console.log('📍 === FIN actualizarUbicacionBarra() ===');
    }

    async iniciarTracking() {
        if (!navigator.geolocation) {
            console.error('❌ Geolocalización no soportada');
            this.mostrarError('Tu dispositivo no soporta GPS');
            return;
        }
        
        console.log('▶️ Iniciando tracking GPS automático...');
        this.isTracking = true;
        
        // ✅ Si ya tenemos ubicación del header, usarla
        if (estadoApp?.ubicacion?.latitud) {
            await this.enviarUbicacion({
                coords: {
                    latitude: estadoApp.ubicacion.latitud,
                    longitude: estadoApp.ubicacion.longitud,
                    accuracy: estadoApp.ubicacion.precision || 100
                }
            });
        }
        
        // Captura periódica cada 5 minutos
        this.intervalId = setInterval(() => {
            this.capturarUbicacion();
        }, this.config.intervaloMs);
        
        this.actualizarEstadoWidget('tracking');
        
        const statusEl = document.getElementById('gpsStatus');
        if (statusEl) statusEl.textContent = 'Activo';
    }
    
    async capturarUbicacion() {
        console.log('📍 Capturando ubicación...');
        
        return new Promise((resolve) => {
            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    await this.enviarUbicacion(position);
                    this.intentosFallidos = 0;
                    resolve(position);
                },
                (error) => {
                    console.error('❌ Error GPS:', error);
                    this.intentosFallidos++;
                    
                    // ✅ Si falla, usar última ubicación conocida del header
                    if (estadoApp?.ubicacion?.latitud) {
                        console.log('⚠️ Usando última ubicación conocida del header');
                        this.enviarUbicacion({
                            coords: {
                                latitude: estadoApp.ubicacion.latitud,
                                longitude: estadoApp.ubicacion.longitud,
                                accuracy: estadoApp.ubicacion.precision || 100
                            }
                        });
                    }
                    
                    resolve(null);
                },
                this.config
            );
        });
    }
    
    async enviarUbicacion(position) {
        try {
            const bateria = await this.obtenerNivelBateria();
            const conectividad = this.detectarTipoConexion();
            
            const datos = {
                latitud: position.coords.latitude,
                longitud: position.coords.longitude,
                precision_gps: position.coords.accuracy,
                tipo_registro: 'automatico',
                bateria_porcentaje: bateria,
                conectividad: conectividad
            };
            
            const token = estadoApp?.token || localStorage.getItem('auth_token');
            
            const response = await fetch('/api/ubicaciones/registrar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(datos)
            });
            
            if (response.ok) {
                console.log('✅ Ubicación enviada correctamente');
                this.ultimaUbicacion = position;
                this.actualizarWidget(position, bateria, conectividad);
                this.actualizarUbicacionBarra(); // ✅ AGREGAR AQUÍ
            } else {
                console.error('❌ Error al enviar ubicación:', response.status);
            }
            
        } catch (error) {
            console.error('❌ Error enviando ubicación:', error);
        }
    }
    
    actualizarWidget(position, bateria = null, conectividad = null) {
        // Actualizar precisión
        const precision = Math.round(position.coords.accuracy);
        const precisionEl = document.getElementById('gpsPrecision');
        if (precisionEl) {
            precisionEl.textContent = `±${precision}m`;
            precisionEl.className = 'stat-value ' + this.getCalidadClase(precision);
        }
        
        // Actualizar batería
        if (bateria !== null) {
            const bateriaEl = document.getElementById('gpsBateria');
            if (bateriaEl) {
                bateriaEl.textContent = `${bateria}%`;
                bateriaEl.className = 'stat-value ' + this.getBateriaClase(bateria);
            }
        } else {
            this.obtenerNivelBateria().then(nivel => {
                if (nivel !== null) {
                    const bateriaEl = document.getElementById('gpsBateria');
                    if (bateriaEl) {
                        bateriaEl.textContent = `${nivel}%`;
                        bateriaEl.className = 'stat-value ' + this.getBateriaClase(nivel);
                    }
                }
            });
        }
        
        // Actualizar señal
        if (conectividad) {
            const senalEl = document.getElementById('gpsSenal');
            if (senalEl) {
                senalEl.textContent = conectividad.toUpperCase();
            }
        }
        
        // Actualizar última actualización
        const ahora = new Date();
        const timeStr = ahora.toLocaleTimeString('es-PE', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        const ultimaActEl = document.getElementById('gpsUltimaActualizacion');
        if (ultimaActEl) {
            ultimaActEl.textContent = `Última: ${timeStr}`;
        }

        // ✅ AGREGAR: Actualizar texto de ubicación
        const ubicacionTextoEl = document.getElementById('gpsUbicacionTexto');
        if (ubicacionTextoEl) {
            const precision = Math.round(position.coords.accuracy);
            ubicacionTextoEl.textContent = `±${precision}m`;
            ubicacionTextoEl.className = this.getCalidadClase(precision);
        }
    }
    
    getCalidadClase(precision) {
        if (precision <= 20) return 'calidad-excelente';
        if (precision <= 50) return 'calidad-buena';
        if (precision <= 100) return 'calidad-regular';
        return 'calidad-mala';
    }
    
    getBateriaClase(nivel) {
        if (nivel >= 60) return 'bateria-alta';
        if (nivel >= 30) return 'bateria-media';
        return 'bateria-baja';
    }
    
    async obtenerNivelBateria() {
        try {
            if ('getBattery' in navigator) {
                const battery = await navigator.getBattery();
                return Math.round(battery.level * 100);
            }
        } catch (error) {
            console.warn('No se puede obtener nivel de batería');
        }
        return null;
    }
    
    detectarTipoConexion() {
        if ('connection' in navigator) {
            const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
            return connection?.effectiveType || 'unknown';
        }
        return 'unknown';
    }
    
    actualizarEstadoWidget(estado) {
        const widget = document.getElementById('gpsTrackerWidget');
        if (widget) {
            widget.setAttribute('data-status', estado);
        }
        
        const statusEl = document.getElementById('gpsStatus');
        if (statusEl) {
            const textos = {
                'waiting': 'Esperando...',
                'tracking': 'Activo',
                'error': 'Error',
                'stopped': 'Detenido'
            };
            statusEl.textContent = textos[estado] || 'Desconocido';
        }
    }
    
    mostrarError(mensaje) {
        if (typeof Toast !== 'undefined') {
            Toast.error(mensaje);
        }
        this.actualizarEstadoWidget('error');
    }
    
    detener() {
        console.log('⏹️ Deteniendo tracking GPS...');
        
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        
        if (this.watchId) {
            navigator.geolocation.clearWatch(this.watchId);
            this.watchId = null;
        }
        
        this.isTracking = false;
        this.actualizarEstadoWidget('stopped');
    }
}

// Instancia global
let gpsTracker = null;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    // Solo iniciar para vendedores
    const userDataStr = localStorage.getItem('user_data');
    if (userDataStr) {
        const userData = JSON.parse(userDataStr);
        if (userData.tipo === 'vendedor') {
            console.log('👤 Usuario es vendedor, preparando GPS Tracker...');
            gpsTracker = new GPSTracker();
        }
    }
});

// Limpiar al cerrar
window.addEventListener('beforeunload', () => {
    if (gpsTracker) {
        gpsTracker.detener();
    }
});