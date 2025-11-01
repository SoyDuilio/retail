/**
 * Sistema de Precios y Crédito para Pedidos
 * Maneja cálculo de precios CONTADO/CRÉDITO y validación de crédito disponible
 */

// ============================================
// CLASE PRINCIPAL
// ============================================

class PreciosManager {
    constructor() {
        this.clienteActual = null;
        this.infoCreditoActual = null;
        this.productosCarrito = [];
        this.tipoPagoActual = 'CREDITO';
        this.popoverInstance = null;
        
        this.initEventListeners();
    }

    // ============================================
    // HELPERS
    // ============================================

    getAuthToken() {
        return localStorage.getItem('auth_token');
    }

    getAuthHeaders() {
        const token = this.getAuthToken();
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        };
    }

    initEventListeners() {
        // Cambio de tipo de pago
        const radioCreditoPedido = document.getElementById('radioCreditoPedido');
        const radioContadoPedido = document.getElementById('radioContadoPedido');
        
        if (radioCreditoPedido) {
            radioCreditoPedido.addEventListener('change', () => this.cambiarTipoPago('CREDITO'));
        }
        if (radioContadoPedido) {
            radioContadoPedido.addEventListener('change', () => this.cambiarTipoPago('CONTADO'));
        }
    }

    // ============================================
    // INFORMACIÓN CREDITICIA
    // ============================================

    async cargarInfoCredito(clienteId) {
        try {
            console.log('📊 Cargando info crediticia para cliente:', clienteId);
            
            // ✅ Cambiar por el endpoint correcto de tu backend
            const response = await fetch(`/api/vendedor/clientes/${clienteId}/credito`, {
                headers: {
                    'Authorization': `Bearer ${estadoApp.token || localStorage.getItem('auth_token')}`
                }
            });

            if (!response.ok) {
                console.warn('⚠️ Error 404 - Backend no devuelve datos, usando ejemplo');
                
                // ✅ DATOS DE EJEMPLO MIENTRAS SE ARREGLA BACKEND
                this.infoCreditoActual = {
                    limite_credito: 5000.00,
                    credito_usado: 0.00,
                    credito_disponible: 5000.00,
                    deuda_total: 0.00,
                    estado: 'al_dia'
                };
                
                this.actualizarBotonCredito(this.infoCreditoActual);
                setTimeout(() => this.configurarPopover(), 300);
                
                console.log('✅ Info crédito cargada (datos de ejemplo)');
                return; // ✅ IMPORTANTE: Salir sin error
            }

            const data = await response.json();
            console.log('📦 Datos de crédito recibidos:', data);
            
            this.infoCreditoActual = data;
            this.actualizarBotonCredito(data);
            
            setTimeout(() => {
                this.configurarPopover();
            }, 300);

            console.log('✅ Info crediticia cargada correctamente');

        } catch (error) {
            console.error('💥 Error al cargar info crediticia:', error);
            this.infoCreditoActual = null;
        }
    }


    configurarPopover() {
        console.log('🎯 === CONFIGURANDO POPOVER ===');
        
        const btnInfoCredito = document.getElementById('btnInfoCredito');
        console.log('   Botón encontrado:', !!btnInfoCredito);
        console.log('   Info actual:', this.infoCreditoActual);
        
        if (!btnInfoCredito) {
            console.error('❌ Botón no encontrado');
            return;
        }
        
        if (!this.infoCreditoActual) {
            console.error('❌ No hay info crédito');
            return;
        }

        const self = this; // ✅ Guardar contexto
        const content = this.generarContenidoPopover(this.infoCreditoActual);

        // ✅ Limpiar listeners previos
        btnInfoCredito.onclick = null;
        btnInfoCredito.replaceWith(btnInfoCredito.cloneNode(true));
        
        // Obtener referencia nueva
        const nuevoBtn = document.getElementById('btnInfoCredito');
        
        // ✅ Agregar listener simple
        nuevoBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('💳 === CLICK EN BOTÓN CRÉDITO ===');
            self.mostrarTooltipManual(nuevoBtn, content);
        };
        
        // ✅ También agregar hover
        nuevoBtn.addEventListener('mouseenter', function() {
            console.log('🖱️ Hover en botón crédito');
            self.mostrarTooltipManual(nuevoBtn, content);
        });

        console.log('✅ Popover configurado');
        console.log('🎯 === FIN CONFIGURAR POPOVER ===');
    }


    // ✅ NUEVO: Tooltip manual (sin Bootstrap)
    mostrarTooltipManual(elemento, contenido) {
        this.ocultarTooltipManual();
        
        const tooltip = document.createElement('div');
        tooltip.id = 'tooltip-credito-manual';
        tooltip.className = 'tooltip-manual';
        tooltip.innerHTML = contenido;
        
        document.body.appendChild(tooltip);
        
        console.log('✅ Tooltip mostrado');
        
        // ✅ Cerrar con click en el botón X (usando ::after)
        tooltip.addEventListener('click', (e) => {
            const rect = tooltip.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            // Área del botón X (top-right corner)
            if (x > rect.width - 50 && y < 50) {
                this.ocultarTooltipManual();
            }
        });
        
        // ✅ Cerrar con click en el overlay (fuera de la tarjeta)
        setTimeout(() => {
            document.addEventListener('click', (e) => {
                if (!tooltip.contains(e.target) && !elemento.contains(e.target)) {
                    this.ocultarTooltipManual();
                }
            }, { once: true });
        }, 100);
        
        // ✅ Cerrar con tecla ESC
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                this.ocultarTooltipManual();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);
    }

    ocultarTooltipManual() {
        const tooltip = document.getElementById('tooltip-credito-manual');
        if (tooltip) {
            tooltip.remove();
        }
    }

    actualizarBotonCredito(info) {
        const btnInfoCredito = document.getElementById('btnInfoCredito');
        if (!btnInfoCredito) return;

        const iconoEl = document.getElementById('creditoIcono');
        const resumenEl = document.getElementById('creditoResumen');

        if (!iconoEl || !resumenEl) return;

        // Determinar estado según deuda y disponible
        const creditoDisponible = parseFloat(info.credito_disponible) || 0;
        const deudaTotal = parseFloat(info.deuda_total) || 0;
        
        let estado = 'normal';
        let icono = '💳';
        let texto = 'Ver crédito';

        if (deudaTotal > 0 && info.estado !== 'al_dia') {
            estado = 'moroso';
            icono = '⚠️';
            texto = 'Moroso';
        } else if (creditoDisponible < 100) {
            estado = 'advertencia';
            icono = '⚡';
            texto = 'Bajo';
        }

        // Actualizar clases
        btnInfoCredito.className = 'btn-credito-mini estado-' + estado;
        iconoEl.textContent = icono;
        resumenEl.textContent = texto;

        console.log('✅ Botón crédito actualizado:', { estado, icono, texto });
    }

    generarContenidoPopover(info) {
        console.log('🎨 Generando contenido popover con:', info);
        
        // ✅ VALIDACIÓN ROBUSTA - Convertir TODOS los valores
        const limiteCredito = info?.limite_credito !== undefined ? parseFloat(info.limite_credito) : 0;
        const creditoUsado = info?.credito_usado !== undefined ? parseFloat(info.credito_usado) : 0;
        const creditoDisponible = info?.credito_disponible !== undefined ? parseFloat(info.credito_disponible) : 0;
        const deudaTotal = info?.deuda_total !== undefined ? parseFloat(info.deuda_total) : 0;
        
        // Validar que sean números válidos
        const limiteOk = !isNaN(limiteCredito) ? limiteCredito : 0;
        const usadoOk = !isNaN(creditoUsado) ? creditoUsado : 0;
        const disponibleOk = !isNaN(creditoDisponible) ? creditoDisponible : 0;
        const deudaOk = !isNaN(deudaTotal) ? deudaTotal : 0;
        
        const estadoClase = info?.estado === 'al_dia' ? 'al-dia' : 'moroso';
        const estadoTexto = info?.estado === 'al_dia' ? 'Al día' : 'Moroso';
        
        console.log('✅ Valores convertidos:', {
            limiteOk,
            usadoOk,
            disponibleOk,
            deudaOk
        });
        
        return `
            <div class="credito-popover-content">
                <div class="credito-row">
                    <span class="label">Límite Total:</span>
                    <span class="value credito-limite">S/ ${limiteOk.toFixed(2)}</span>
                </div>
                <div class="credito-row">
                    <span class="label">Crédito Usado:</span>
                    <span class="value credito-usado">S/ ${usadoOk.toFixed(2)}</span>
                </div>
                <div class="credito-row highlighted">
                    <span class="label">💰 Disponible:</span>
                    <span class="value credito-disponible">S/ ${disponibleOk.toFixed(2)}</span>
                </div>
                <hr style="margin: 0.5rem 0; border: none; border-top: 1px solid #e5e7eb;">
                <div class="credito-row">
                    <span class="label">Deuda:</span>
                    <span class="value text-danger credito-deuda">S/ ${deudaOk.toFixed(2)}</span>
                </div>
                <div class="credito-row">
                    <span class="label">Estado:</span>
                    <span class="value credito-estado-texto ${estadoClase}">${estadoTexto}</span>
                </div>
            </div>
        `;
    }

    validarCreditoDisponible() {
        if (!this.infoCreditoActual) return;

        const radioCreditoPedido = document.getElementById('radioCreditoPedido');
        const radioContadoPedido = document.getElementById('radioContadoPedido');
        const info = this.infoCreditoActual;

        // Si no puede usar crédito, forzar CONTADO
        if (!info.puede_credito) {
            if (radioCreditoPedido) {
                radioCreditoPedido.disabled = true;
            }
            if (radioContadoPedido) {
                radioContadoPedido.checked = true;
            }
            this.tipoPagoActual = 'CONTADO';
            
            mostrarNotificacion(
                info.mensaje || 'Solo se permite pago al contado por situación crediticia',
                'warning',
                5000
            );
        } else {
            if (radioCreditoPedido) {
                radioCreditoPedido.disabled = false;
            }
        }

        // Validar si el total actual supera crédito disponible
        this.validarTotalContraCredito();
    }

    validarTotalContraCredito() {
        if (!this.infoCreditoActual || this.tipoPagoActual !== 'CREDITO') return;

        const totalPedido = this.calcularTotalCarrito();
        const disponible = this.infoCreditoActual.credito_disponible;

        if (totalPedido > disponible) {
            mostrarNotificacion(
                `⚠️ El monto (S/ ${totalPedido.toFixed(2)}) supera el crédito disponible (S/ ${disponible.toFixed(2)})`,
                'warning',
                5000
            );
        }
    }

    // ============================================
    // CÁLCULO DE PRECIOS
    // ============================================

    async cambiarTipoPago(nuevoTipo) {
        this.tipoPagoActual = nuevoTipo;
        
        console.log(`🔄 Cambiando tipo de pago a: ${nuevoTipo}`);
        
        // Recalcular todos los precios del carrito
        await this.recalcularPreciosCarrito();
        
        // Actualizar comparación
        this.actualizarComparacion();
        
        // Validar crédito si es necesario
        if (nuevoTipo === 'CREDITO') {
            this.validarTotalContraCredito();
        }
    }

    seleccionarTipoPago(tipo) {
        console.log('💳 Tipo de pago seleccionado desde botones:', tipo);
        
        // ✅ Actualizar radio buttons correspondientes
        const radioCredito = document.getElementById('radioCreditoPedido');
        const radioContado = document.getElementById('radioContadoPedido');
        
        if (tipo === 'CREDITO' && radioCredito) {
            radioCredito.checked = true;
        } else if (tipo === 'CONTADO' && radioContado) {
            radioContado.checked = true;
        }
        
        // ✅ Llamar al método principal
        this.cambiarTipoPago(tipo);
    }

    async calcularPreciosProducto(productoId, cantidad = 1) {
        if (!this.clienteActual || !this.clienteActual.tipo_cliente_id) {
            console.error('No hay cliente o tipo de cliente');
            return null;
        }

        try {
            const response = await fetch('/api/precios/comparar', {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({
                    cliente_id: this.clienteActual.id,
                    items: [{ producto_id: productoId, cantidad: cantidad }]
                })
            });

            if (!response.ok) {
                throw new Error('Error al calcular precios');
            }

            const data = await response.json();
            return data.items && data.items.length > 0 ? data.items[0] : null;
        } catch (error) {
            console.error('Error calculando precios:', error);
            return null;
        }
    }

    async recalcularPreciosCarrito() {
        if (!estadoApp?.pedido || estadoApp.pedido.length === 0) {
            console.log('⚠️ Carrito vacío');
            return;
        }

        if (!this.clienteActual) {
            console.error('❌ No hay cliente actual');
            return;
        }

        console.log(`🔄 Recalculando precios del carrito (${estadoApp.pedido.length} items)...`);

        try {
            // ✅ Preparar items para API
            const items = estadoApp.pedido.map(item => ({
                producto_id: item.producto_id,
                cantidad: item.cantidad
            }));

            // ✅ Llamar a API de comparación
            const response = await fetch('/api/precios/comparar', {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({
                    cliente_id: this.clienteActual.id,
                    items: items
                })
            });

            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }

            const data = await response.json();
            console.log('📦 Respuesta API precios:', data);

            // ✅ Actualizar precios en el carrito
            data.items.forEach((itemAPI, index) => {
                if (estadoApp.pedido[index]) {
                    estadoApp.pedido[index].precio_credito = parseFloat(itemAPI.precio_credito.precio_final);
                    estadoApp.pedido[index].precio_contado = parseFloat(itemAPI.precio_contado.precio_final);
                    
                    // Actualizar precio y subtotal según tipo de pago actual
                    if (this.tipoPagoActual === 'CREDITO') {
                        estadoApp.pedido[index].precio_unitario = estadoApp.pedido[index].precio_credito;
                        estadoApp.pedido[index].subtotal = parseFloat(itemAPI.precio_credito.subtotal);
                    } else {
                        estadoApp.pedido[index].precio_unitario = estadoApp.pedido[index].precio_contado;
                        estadoApp.pedido[index].subtotal = parseFloat(itemAPI.precio_contado.subtotal);
                    }
                }
            });

            // ✅ Actualizar totales en UI
            const totalCredito = parseFloat(data.total_credito);
            const totalContado = parseFloat(data.total_contado);
            const ahorro = parseFloat(data.ahorro_contado);

            const elemCredito = document.getElementById('totalCreditoComparacion');
            const elemContado = document.getElementById('totalContadoComparacion');
            const elemAhorro = document.getElementById('ahorroMonto');
            const elemTotal = document.getElementById('totalPedido');

            if (elemCredito) elemCredito.textContent = `S/ ${totalCredito.toFixed(2)}`;
            if (elemContado) elemContado.textContent = `S/ ${totalContado.toFixed(2)}`;
            if (elemAhorro) elemAhorro.textContent = `S/ ${ahorro.toFixed(2)}`;
            
            if (elemTotal) {
                const totalActual = this.tipoPagoActual === 'CREDITO' ? totalCredito : totalContado;
                elemTotal.textContent = `S/ ${totalActual.toFixed(2)}`;
                console.log(`💰 Total actualizado: S/ ${totalActual.toFixed(2)}`);
            }

            console.log('✅ Comparación actualizada:', {totalCredito, totalContado, ahorro});

            // ✅ Re-renderizar productos si existe la función
            if (typeof mostrarProductosPedido === 'function') {
                mostrarProductosPedido();
            }

        } catch (error) {
            console.error('❌ Error recalculando precios:', error);
        }
    }

    async actualizarComparacion() {
        if (!this.clienteActual || this.productosCarrito.length === 0) {
            return;
        }

        try {
            const items = this.productosCarrito.map(p => ({
                producto_id: p.producto_id,
                cantidad: p.cantidad
            }));

            const response = await fetch('/api/precios/comparar', {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({
                    cliente_id: this.clienteActual.id,
                    items: items
                })
            });

            if (!response.ok) throw new Error('Error en comparación');

            const data = await response.json();

            // ✅ Convertir a números por seguridad
            const totalCredito = parseFloat(data.total_credito) || 0;
            const totalContado = parseFloat(data.total_contado) || 0;
            const ahorro = parseFloat(data.ahorro_contado) || 0;

            // Actualizar UI
            const elemCreditoComp = document.getElementById('totalCreditoComparacion');
            const elemContadoComp = document.getElementById('totalContadoComparacion');
            const elemAhorro = document.getElementById('ahorroMonto');
            const elemTotal = document.getElementById('totalPedido');

            // ✅ AGREGAR animación
            if (elemCreditoComp) {
                elemCreditoComp.classList.add('actualizando');
                elemCreditoComp.textContent = `S/ ${totalCredito.toFixed(2)}`;
                setTimeout(() => elemCreditoComp.classList.remove('actualizando'), 500);
            }

            if (elemContadoComp) {
                elemContadoComp.classList.add('actualizando');
                elemContadoComp.textContent = `S/ ${totalContado.toFixed(2)}`;
                setTimeout(() => elemContadoComp.classList.remove('actualizando'), 500);
            }

            if (elemAhorro) {
                elemAhorro.classList.add('actualizando');
                elemAhorro.textContent = `S/ ${ahorro.toFixed(2)}`;
                setTimeout(() => elemAhorro.classList.remove('actualizando'), 500);
            }

            if (elemTotal) {
                elemTotal.classList.add('actualizando');
                setTimeout(() => elemTotal.classList.remove('actualizando'), 500);
            }

            console.log('✅ Comparación actualizada:', { totalCredito, totalContado, ahorro });

        } catch (error) {
            console.error('Error actualizando comparación:', error);
        }
    }

    calcularTotalCarrito() {
        // Tu estructura usa estadoApp.pedido
        let total = 0;
        
        if (estadoApp && estadoApp.pedido) {
            estadoApp.pedido.forEach(item => {
                total += item.subtotal || 0;
            });
        }
        
        return total;
    }

    actualizarTotalPedido() {
        const total = this.calcularTotalCarrito();
        
        // Buscar el span del total en el footer
        const totalSpan = document.getElementById('totalPedido');
        
        if (totalSpan) {
            totalSpan.textContent = `S/ ${total.toFixed(2)}`;
        }
        
        console.log(`💰 Total actualizado: S/ ${total.toFixed(2)}`);
    }

    // ============================================
    // LIMPIEZA
    // ============================================

    limpiar() {
        this.clienteActual = null;
        this.infoCreditoActual = null;
        this.productosCarrito = [];
        this.tipoPagoActual = 'CREDITO';
        
        // Resetear radio buttons
        const radioCreditoPedido = document.getElementById('radioCreditoPedido');
        if (radioCreditoPedido) {
            radioCreditoPedido.checked = true;
            radioCreditoPedido.disabled = false;
        }
        
        // Resetear totales
        const elemCreditoComp = document.getElementById('totalCreditoComparacion');
        const elemContadoComp = document.getElementById('totalContadoComparacion');
        const elemAhorro = document.getElementById('ahorroMonto');
        
        if (elemCreditoComp) elemCreditoComp.textContent = 'S/ 0.00';
        if (elemContadoComp) elemContadoComp.textContent = 'S/ 0.00';
        if (elemAhorro) elemAhorro.textContent = 'S/ 0.00';
        
        // Destruir popover
        if (this.popoverInstance) {
            this.popoverInstance.dispose();
            this.popoverInstance = null;
        }
        
        console.log('🧹 Manager de precios limpiado');
    }
}

// ============================================
// INSTANCIA GLOBAL
// ============================================

let preciosManager = null;

// ============================================
// INICIALIZACIÓN
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    preciosManager = new PreciosManager();
    console.log('✅ Sistema de precios inicializado');
});

// ============================================
// FUNCIONES GLOBALES (Compatibilidad)
// ============================================
function mostrarNotificacion(mensaje, tipo = 'info', duracion = 3000) {
    if (typeof Toast !== 'undefined') {
        switch (tipo) {
            case 'success':
                Toast.success(mensaje, duracion);
                break;
            case 'warning':
                Toast.warning(mensaje, duracion);
                break;
            case 'error':
                Toast.error(mensaje, duracion);
                break;
            default:
                Toast.info(mensaje, duracion);
        }
    } else {
        console.log(`[${tipo.toUpperCase()}] ${mensaje}`);
    }
}