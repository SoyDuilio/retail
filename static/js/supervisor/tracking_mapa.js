// ============================================
// TRACKING MAPA - SUPERVISOR
// ============================================

let mapaTracking = null;
let marcadoresVendedores = {};
let intervalActualizacion = null;

// Inicializar mapa
// Inicializar mapa
function inicializarMapa() {
    if (mapaTracking) return;
    
    console.log('🗺️ Inicializando mapa de tracking...');
    
    // ✅ Centrar en una ubicación más neutral hasta cargar vendedores
    mapaTracking = L.map('mapaTracking').setView([0, 0], 2);
    
    // Agregar capa de OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(mapaTracking);
    
    // Cargar ubicaciones iniciales
    cargarUbicacionesVendedores();
    
    // Auto-refresh cada 30 segundos
    intervalActualizacion = setInterval(cargarUbicacionesVendedores, 30000);
}

// Cargar ubicaciones de vendedores
async function cargarUbicacionesVendedores() {
    try {
        const token = localStorage.getItem('auth_token');
        
        const response = await fetch('/api/ubicaciones/ultimas', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Error al cargar ubicaciones');
        }
        
        const data = await response.json();
        console.log('📍 Ubicaciones recibidas:', data);
        
        if (data.success) {
            actualizarMapa(data.data);
            actualizarListaVendedores(data.data);
            actualizarEstadisticas(data.data);
        }
        
    } catch (error) {
        console.error('❌ Error cargando ubicaciones:', error);
    }
}

// Actualizar marcadores en el mapa
function actualizarMapa(vendedores) {
    if (!mapaTracking) return;
    
    vendedores.forEach(vendedor => {
        if (!vendedor.latitud || !vendedor.longitud) return;
        
        const vendedorId = vendedor.vendedor_id;
        const posicion = [vendedor.latitud, vendedor.longitud];
        
        // Si ya existe el marcador, actualizar posición
        if (marcadoresVendedores[vendedorId]) {
            marcadoresVendedores[vendedorId].setLatLng(posicion);
        } else {
            // Crear nuevo marcador
            const icono = L.divIcon({
                className: 'custom-marker',
                html: `
                    <div class="marker-vendedor ${getEstadoClase(vendedor.minutos_inactivo)}">
                        <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                        </svg>
                        <div class="marker-label">${vendedor.nombre}</div>
                    </div>
                `,
                iconSize: [40, 40],
                iconAnchor: [20, 40]
            });
            
            const marcador = L.marker(posicion, { icon: icono }).addTo(mapaTracking);
            
            // Popup con información
            const popupContent = `
                <div class="popup-vendedor">
                    <h4 class="font-semibold">${vendedor.nombre} ${vendedor.apellidos}</h4>
                    <p class="text-sm text-gray-600">${vendedor.codigo_vendedor}</p>
                    <div class="mt-2 text-xs space-y-1">
                        <div>📍 Precisión: ±${Math.round(vendedor.precision_gps || 0)}m</div>
                        <div>🔋 Batería: ${vendedor.bateria_porcentaje || '--'}%</div>
                        <div>📡 Señal: ${vendedor.conectividad || '--'}</div>
                        <div>⏰ Última actualización: ${formatearTiempo(vendedor.minutos_inactivo)}</div>
                    </div>
                    <button onclick="verHistorialVendedor(${vendedor.vendedor_id})" class="mt-2 bg-blue-600 text-white px-3 py-1 rounded text-xs w-full">
                        Ver Historial
                    </button>
                </div>
            `;
            
            marcador.bindPopup(popupContent);
            marcadoresVendedores[vendedorId] = marcador;
        }
    });
    
    // Ajustar vista para mostrar todos los marcadores
    if (vendedores.length > 0) {
        const bounds = vendedores
            .filter(v => v.latitud && v.longitud)
            .map(v => [v.latitud, v.longitud]);
        
        if (bounds.length > 0) {
            mapaTracking.fitBounds(bounds, { padding: [50, 50] });
        }
    }
}

// Actualizar lista lateral de vendedores
function actualizarListaVendedores(vendedores) {
    const lista = document.getElementById('listaVendedoresTracking');
    if (!lista) return;
    
    if (vendedores.length === 0) {
        lista.innerHTML = `
            <div class="text-center text-gray-500 py-8">
                <p class="text-sm">No hay vendedores activos</p>
            </div>
        `;
        return;
    }
    
    lista.innerHTML = vendedores.map(v => `
        <div class="vendedor-item ${getEstadoClase(v.minutos_inactivo)}" onclick="centrarEnVendedor(${v.vendedor_id})">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                    <div class="status-dot"></div>
                    <div>
                        <div class="font-semibold text-sm">${v.nombre}</div>
                        <div class="text-xs text-gray-400">${v.codigo_vendedor}</div>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-xs text-gray-400">${formatearTiempo(v.minutos_inactivo)}</div>
                    <div class="text-xs ${getPrecisionColor(v.precision_gps)}">±${Math.round(v.precision_gps || 0)}m</div>
                </div>
            </div>
        </div>
    `).join('');
    
    // Actualizar select de filtro
    const select = document.getElementById('filtroVendedor');
    if (select) {
        const opcionesActuales = Array.from(select.options).map(o => o.value);
        vendedores.forEach(v => {
            if (!opcionesActuales.includes(v.vendedor_id.toString())) {
                const option = document.createElement('option');
                option.value = v.vendedor_id;
                option.textContent = `${v.nombre} ${v.apellidos}`;
                select.appendChild(option);
            }
        });
    }
}

// Actualizar estadísticas
// Actualizar estadísticas
function actualizarEstadisticas(vendedores) {
    // Vendedores activos (últimos 15 minutos)
    const activos = vendedores.filter(v => v.minutos_inactivo !== null && v.minutos_inactivo <= 15).length;
    
    const elemVendedoresActivos = document.getElementById('vendedoresActivos');
    if (elemVendedoresActivos) {
        elemVendedoresActivos.textContent = activos;
    }
    
    // Última actualización
    const ahora = new Date().toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' });
    const elemUltimaAct = document.getElementById('ultimaActualizacionMapa');
    if (elemUltimaAct) {
        elemUltimaAct.textContent = ahora;
    }
    
    // TODO: Calcular distancia total y visitas desde el backend
    const elemDistancia = document.getElementById('distanciaTotal');
    if (elemDistancia) {
        elemDistancia.textContent = '0 km';
    }
    
    const elemVisitas = document.getElementById('visitasRealizadas');
    if (elemVisitas) {
        elemVisitas.textContent = '0';
    }
}

// Centrar mapa en vendedor específico
function centrarEnVendedor(vendedorId) {
    const marcador = marcadoresVendedores[vendedorId];
    if (marcador && mapaTracking) {
        mapaTracking.setView(marcador.getLatLng(), 16);
        marcador.openPopup();
    }
}

// Ver historial de ruta de vendedor
async function verHistorialVendedor(vendedorId) {
    try {
        const token = localStorage.getItem('auth_token');
        const fecha = new Date().toISOString().split('T')[0];
        
        const response = await fetch(`/api/ubicaciones/historial/${vendedorId}?fecha=${fecha}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (data.success && data.data.ruta.length > 0) {
            // Dibujar ruta en el mapa
            const coordenadas = data.data.ruta.map(p => [p.latitud, p.longitud]);
            
            // Limpiar rutas anteriores
            mapaTracking.eachLayer(layer => {
                if (layer instanceof L.Polyline) {
                    mapaTracking.removeLayer(layer);
                }
            });
            
            // Dibujar nueva ruta
            const ruta = L.polyline(coordenadas, {
                color: '#3b82f6',
                weight: 3,
                opacity: 0.7
            }).addTo(mapaTracking);
            
            mapaTracking.fitBounds(ruta.getBounds());
            
            // Mostrar info
            alert(`Ruta del día:\n- Puntos registrados: ${data.data.total_registros}\n- Distancia recorrida: ${data.data.distancia_recorrida_km.toFixed(2)} km`);
        } else {
            alert('No hay historial de ruta para hoy');
        }
        
    } catch (error) {
        console.error('Error cargando historial:', error);
        alert('Error al cargar historial de ruta');
    }
}

// Utilidades
function getEstadoClase(minutosInactivo) {
    if (minutosInactivo <= 5) return 'estado-activo';
    if (minutosInactivo <= 15) return 'estado-reciente';
    return 'estado-inactivo';
}

function getPrecisionColor(precision) {
    if (precision <= 20) return 'text-green-400';
    if (precision <= 50) return 'text-blue-400';
    if (precision <= 100) return 'text-yellow-400';
    return 'text-red-400';
}

function formatearTiempo(minutos) {
    if (!minutos) return 'Ahora';
    if (minutos < 1) return 'Ahora';
    if (minutos < 60) return `Hace ${Math.round(minutos)}m`;
    return `Hace ${Math.round(minutos / 60)}h`;
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar cuando se active el tab
    const tabTracking = document.querySelector('[data-tab="tracking"]');
    if (tabTracking) {
        tabTracking.addEventListener('click', () => {
            setTimeout(inicializarMapa, 100);
        });
    }
    
    // Botón refrescar
    const btnRefresh = document.getElementById('btnRefreshMapa');
    if (btnRefresh) {
        btnRefresh.addEventListener('click', cargarUbicacionesVendedores);
    }
});

// Limpiar al salir
window.addEventListener('beforeunload', () => {
    if (intervalActualizacion) {
        clearInterval(intervalActualizacion);
    }
});