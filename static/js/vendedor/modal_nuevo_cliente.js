// ============================================================================
// MODAL NUEVO CLIENTE - WIZARD CARDS FLOTANTES
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    
    // ========================================================================
    // VARIABLES Y ELEMENTOS DEL DOM
    // ========================================================================
    
    const modalNuevoCliente = document.getElementById('modalNuevoCliente');
    const btnAbrirModal = document.getElementById('btnNuevoCliente');
    const btnCerrarModal = document.getElementById('btnCerrarModalCliente');
    const btnCancelarModal = document.getElementById('btnCancelarRegistro');
    const formNuevoCliente = document.getElementById('formNuevoCliente');
    
    // Verificar que los elementos existen
    if (!modalNuevoCliente || !formNuevoCliente) {
        console.warn('Modal de nuevo cliente no encontrado en esta página');
        return;
    }
    
    // Botones de navegación
    const btnSiguiente = document.getElementById('btnSiguiente');
    const btnAnterior = document.getElementById('btnAnterior');
    const btnGuardarCliente = document.getElementById('btnGuardarCliente');
    
    // Botones de validación
    const btnValidarRuc = document.getElementById('btnValidarRuc');
    const btnValidarDni = document.getElementById('btnValidarDni');
    
    // Inputs principales
    const inputRuc = document.getElementById('numero_ruc');
    const inputDni = document.getElementById('numero_dni');
    const inputTelefono = document.getElementById('telefono');
    const selectTipoCliente = document.getElementById('tipo_cliente');
    
    // Selects de ubigeo
    const selectDepartamento = document.getElementById('departamento');
    const selectProvincia = document.getElementById('provincia');
    const selectDistrito = document.getElementById('distrito');
    
    // Cards y steps
    const wizardCards = document.querySelectorAll('.wizard-card');
    const stepItems = document.querySelectorAll('.step-item');
    
    let pasoActual = 1;
    let rucValidado = false;
    let dniValidado = false;
    
    // Datos simulados de políticas por tipo de cliente
    const politicasCliente = {
        '1': { nombre: 'Bodega', limiteCredito: 'S/ 5,000.00', diasCredito: '15 días' },
        '2': { nombre: 'Puesto de Mercado', limiteCredito: 'S/ 3,000.00', diasCredito: '7 días' },
        '3': { nombre: 'Restaurante', limiteCredito: 'S/ 10,000.00', diasCredito: '30 días' },
        '4': { nombre: 'Distribuidor', limiteCredito: 'S/ 20,000.00', diasCredito: '45 días' },
        '5': { nombre: 'Minimarket', limiteCredito: 'S/ 8,000.00', diasCredito: '15 días' },
        '6': { nombre: 'Otros', limiteCredito: 'S/ 2,000.00', diasCredito: '7 días' }
    };
    
    
    // ========================================================================
    // FUNCIONES DE APERTURA Y CIERRE DEL MODAL
    // ========================================================================
    
    function abrirModal() {
        modalNuevoCliente.classList.add('modal-activo');
        document.body.style.overflow = 'hidden';
        pasoActual = 1;
        rucValidado = false;
        dniValidado = false;
        mostrarPaso(1);
    }
    
    function cerrarModal() {
        modalNuevoCliente.classList.remove('modal-activo');
        document.body.style.overflow = '';
        formNuevoCliente.reset();
        limpiarTodosLosErrores();
        ocultarDatosValidados();
        pasoActual = 1;
        rucValidado = false;
        dniValidado = false;
        mostrarPaso(1);
    }
    
    function ocultarDatosValidados() {
        const datosRuc = document.getElementById('datosRuc');
        const datosDni = document.getElementById('datosDni');
        const infoPolitica = document.getElementById('infoPolitica');
        if (datosRuc) datosRuc.classList.add('hidden');
        if (datosDni) datosDni.classList.add('hidden');
        if (infoPolitica) infoPolitica.classList.add('hidden');
    }
    
    
    // ========================================================================
    // NAVEGACIÓN DEL WIZARD
    // ========================================================================
    
    function mostrarPaso(numeroPaso) {
        // Ocultar todas las cards
        wizardCards.forEach(card => {
            card.classList.remove('active');
        });
        
        // Mostrar card actual
        const cardActual = document.querySelector(`.wizard-card[data-step="${numeroPaso}"]`);
        if (cardActual) {
            cardActual.classList.add('active');
        }
        
        // Actualizar indicadores de pasos
        actualizarIndicadores(numeroPaso);
        
        // Actualizar botones de navegación
        actualizarBotones(numeroPaso);
        
        // Actualizar resumen si es paso 3
        if (numeroPaso === 3) {
            actualizarResumen();
        }
    }
    
    function actualizarIndicadores(numeroPaso) {
        stepItems.forEach((item, index) => {
            const stepNum = index + 1;
            
            if (stepNum < numeroPaso) {
                item.classList.remove('active');
                item.classList.add('completed');
            } else if (stepNum === numeroPaso) {
                item.classList.add('active');
                item.classList.remove('completed');
            } else {
                item.classList.remove('active', 'completed');
            }
        });
    }
    
    function actualizarBotones(numeroPaso) {
        if (!btnAnterior || !btnSiguiente || !btnGuardarCliente) return;
        
        btnAnterior.style.display = numeroPaso === 1 ? 'none' : 'inline-flex';
        
        if (numeroPaso === 3) {
            btnSiguiente.style.display = 'none';
            btnGuardarCliente.style.display = 'inline-flex';
        } else {
            btnSiguiente.style.display = 'inline-flex';
            btnGuardarCliente.style.display = 'none';
        }
    }
    
    function siguientePaso() {
        if (validarPasoActual()) {
            if (pasoActual < 3) {
                pasoActual++;
                mostrarPaso(pasoActual);
            }
        }
    }
    
    function anteriorPaso() {
        if (pasoActual > 1) {
            pasoActual--;
            mostrarPaso(pasoActual);
        }
    }
    
    
    // ========================================================================
    // VALIDACIONES POR PASO
    // ========================================================================
    
    function validarPasoActual() {
        limpiarTodosLosErrores();
        
        switch(pasoActual) {
            case 1:
                return validarPaso1();
            case 2:
                return validarPaso2();
            case 3:
                return validarPaso3();
            default:
                return true;
        }
    }
    
    function validarPaso1() {
        let valido = true;
        
        if (!rucValidado) {
            mostrarFeedback('feedbackRuc', 'Debes validar el RUC antes de continuar', 'error');
            valido = false;
        }
        
        if (!dniValidado) {
            mostrarFeedback('feedbackDni', 'Debes validar el DNI del titular antes de continuar', 'error');
            valido = false;
        }
        
        const nombreComercial = document.getElementById('nombre_comercial');
        if (rucValidado && nombreComercial && nombreComercial.value.trim().length < 3) {
            mostrarError(nombreComercial, 'Debe tener al menos 3 caracteres');
            valido = false;
        }
        
        return valido;
    }
    
    function validarPaso2() {
        let valido = true;
        
        const telefono = document.getElementById('telefono');
        const email = document.getElementById('email');
        const direccion = document.getElementById('direccion');
        const departamento = document.getElementById('departamento');
        const provincia = document.getElementById('provincia');
        const distrito = document.getElementById('distrito');
        
        if (!telefono || !telefono.value.trim()) {
            mostrarError(telefono, 'El teléfono es obligatorio');
            valido = false;
        } else if (telefono.value.trim().length < 7) {
            mostrarError(telefono, 'Ingrese un teléfono válido (mínimo 7 dígitos)');
            valido = false;
        }
        
        if (email && email.value.trim()) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email.value.trim())) {
                mostrarError(email, 'Ingrese un email válido');
                valido = false;
            }
        }
        
        if (!direccion || !direccion.value.trim()) {
            mostrarError(direccion, 'La dirección es obligatoria');
            valido = false;
        } else if (direccion.value.trim().length < 10) {
            mostrarError(direccion, 'Ingrese una dirección más completa (mínimo 10 caracteres)');
            valido = false;
        }
        
        if (!departamento || !departamento.value) {
            mostrarError(departamento, 'Seleccione un departamento');
            valido = false;
        }
        
        if (!provincia || !provincia.value) {
            mostrarError(provincia, 'Seleccione una provincia');
            valido = false;
        }
        
        if (!distrito || !distrito.value) {
            mostrarError(distrito, 'Seleccione un distrito');
            valido = false;
        }
        
        return valido;
    }
    
    function validarPaso3() {
        let valido = true;
        
        const tipoCliente = document.getElementById('tipo_cliente');
        
        if (!tipoCliente || !tipoCliente.value) {
            mostrarError(tipoCliente, 'Seleccione un tipo de cliente');
            valido = false;
        }
        
        return valido;
    }
    
    
    // ========================================================================
    // VALIDACIÓN AUTOMÁTICA DE RUC (11 DÍGITOS)
    // ========================================================================
    
    function validarRUC() {
        const ruc = inputRuc.value.trim();
        
        limpiarFeedback('feedbackRuc');
        
        if (!ruc) {
            mostrarFeedback('feedbackRuc', 'Ingrese el RUC', 'error');
            return;
        }
        
        if (ruc.length !== 11) {
            mostrarFeedback('feedbackRuc', 'El RUC debe tener 11 dígitos', 'error');
            return;
        }
        
        if (!/^\d+$/.test(ruc)) {
            mostrarFeedback('feedbackRuc', 'Solo se permiten números', 'error');
            return;
        }
        
        btnValidarRuc.disabled = true;
        btnValidarRuc.innerHTML = `
            <svg class="btn-icon animate-spin" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Validando...
        `;
        
        setTimeout(() => {
            const datosEmpresa = {
                ruc: ruc,
                razonSocial: 'DISTRIBUIDORA COMERCIAL SAC',
                nombreComercial: 'DISCOMERCIAL',
                estado: 'ACTIVO',
                condicion: 'HABIDO',
                direccion: 'AV. INDUSTRIAL 456, LIMA'
            };
            
            document.getElementById('razon_social').value = datosEmpresa.razonSocial;
            document.getElementById('nombre_comercial').value = datosEmpresa.nombreComercial;
            
            const inputDireccion = document.getElementById('direccion');
            if (inputDireccion && !inputDireccion.value.trim()) {
                inputDireccion.value = datosEmpresa.direccion;
            }
            
            const datosRuc = document.getElementById('datosRuc');
            if (datosRuc) {
                datosRuc.classList.remove('hidden');
            }
            
            rucValidado = true;
            
            btnValidarRuc.disabled = false;
            btnValidarRuc.innerHTML = `
                <svg class="btn-icon" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                Validar
            `;
            
            mostrarFeedback('feedbackRuc', 'RUC validado correctamente', 'success');
            mostrarNotificacion('Datos de SUNAT obtenidos correctamente', 'success');
            
        }, 1500);
    }
    
    
    // ========================================================================
    // VALIDACIÓN AUTOMÁTICA DE DNI (8 DÍGITOS)
    // ========================================================================
    
    function validarDNI() {
        const dni = inputDni.value.trim();
        
        limpiarFeedback('feedbackDni');
        
        if (!dni) {
            mostrarFeedback('feedbackDni', 'Ingrese el DNI', 'error');
            return;
        }
        
        if (dni.length !== 8) {
            mostrarFeedback('feedbackDni', 'El DNI debe tener 8 dígitos', 'error');
            return;
        }
        
        if (!/^\d+$/.test(dni)) {
            mostrarFeedback('feedbackDni', 'Solo se permiten números', 'error');
            return;
        }
        
        btnValidarDni.disabled = true;
        btnValidarDni.innerHTML = `
            <svg class="btn-icon animate-spin" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Validando...
        `;
        
        setTimeout(() => {
            const datosPersona = {
                dni: dni,
                nombres: 'JUAN',
                apellidoPaterno: 'PEREZ',
                apellidoMaterno: 'LOPEZ'
            };
            
            const nombreCompleto = `${datosPersona.nombres} ${datosPersona.apellidoPaterno} ${datosPersona.apellidoMaterno}`;
            
            document.getElementById('nombres_titular').value = nombreCompleto;
            
            const datosDni = document.getElementById('datosDni');
            if (datosDni) {
                datosDni.classList.remove('hidden');
            }
            
            dniValidado = true;
            
            btnValidarDni.disabled = false;
            btnValidarDni.innerHTML = `
                <svg class="btn-icon" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                Validar
            `;
            
            mostrarFeedback('feedbackDni', 'DNI validado correctamente', 'success');
            mostrarNotificacion('Datos de RENIEC obtenidos correctamente', 'success');
            
        }, 1500);
    }
    
    
    // ========================================================================
    // AUTO-VALIDACIÓN AL COMPLETAR DÍGITOS
    // ========================================================================
    
    if (inputRuc) {
        inputRuc.addEventListener('input', function(e) {
            this.value = this.value.replace(/\D/g, '');
            limpiarFeedback('feedbackRuc');
            rucValidado = false;
            
            if (this.value.length === 11) {
                validarRUC();
            }
        });
    }
    
    if (inputDni) {
        inputDni.addEventListener('input', function(e) {
            this.value = this.value.replace(/\D/g, '');
            limpiarFeedback('feedbackDni');
            dniValidado = false;
            
            if (this.value.length === 8) {
                validarDNI();
            }
        });
    }
    
    
    // ========================================================================
    // FORMATO AUTOMÁTICO PARA TELÉFONO
    // ========================================================================
    
    if (inputTelefono) {
        inputTelefono.addEventListener('input', function(e) {
            this.value = this.value.replace(/\D/g, '');
        });
    }
    
    
    // ========================================================================
    // TIPO DE CLIENTE - MOSTRAR POLÍTICA
    // ========================================================================
    
    if (selectTipoCliente) {
        selectTipoCliente.addEventListener('change', function() {
            const infoPolitica = document.getElementById('infoPolitica');
            const tipoSeleccionado = this.value;
            
            if (tipoSeleccionado && politicasCliente[tipoSeleccionado]) {
                const politica = politicasCliente[tipoSeleccionado];
                
                document.getElementById('limiteCreditoMax').textContent = politica.limiteCredito;
                document.getElementById('diasCreditoMax').textContent = politica.diasCredito;
                
                if (infoPolitica) {
                    infoPolitica.classList.remove('hidden');
                }
            } else {
                if (infoPolitica) {
                    infoPolitica.classList.add('hidden');
                }
            }
            
            actualizarResumen();
        });
    }
    
    
    // ========================================================================
    // UBIGEO - CARGA DINÁMICA
    // ========================================================================
    
    const ubigeoData = {
        'Lima': {
            'Lima': ['Cercado de Lima', 'Miraflores', 'San Isidro', 'Surco', 'La Molina', 'San Borja', 'Chorrillos', 'Barranco'],
            'Callao': ['Callao', 'Bellavista', 'La Perla', 'Ventanilla', 'Carmen de la Legua'],
            'Cañete': ['San Vicente de Cañete', 'Imperial', 'Mala', 'Asia', 'Cerro Azul']
        },
        'Arequipa': {
            'Arequipa': ['Arequipa', 'Cayma', 'Cerro Colorado', 'Yanahuara', 'Miraflores'],
            'Camaná': ['Camaná', 'Samuel Pastor', 'Ocoña', 'Quilca']
        },
        'Cusco': {
            'Cusco': ['Cusco', 'Wanchaq', 'San Sebastián', 'Santiago', 'San Jerónimo'],
            'Urubamba': ['Urubamba', 'Ollantaytambo', 'Machupicchu', 'Yucay']
        }
    };
    
    function cargarProvincias() {
        if (!selectDepartamento || !selectProvincia || !selectDistrito) return;
        
        const departamento = selectDepartamento.value;
        
        selectProvincia.innerHTML = '<option value="">Seleccionar</option>';
        selectDistrito.innerHTML = '<option value="">Seleccionar</option>';
        selectProvincia.disabled = true;
        selectDistrito.disabled = true;
        
        if (departamento && ubigeoData[departamento]) {
            const provincias = Object.keys(ubigeoData[departamento]);
            
            provincias.forEach(provincia => {
                const option = document.createElement('option');
                option.value = provincia;
                option.textContent = provincia;
                selectProvincia.appendChild(option);
            });
            
            selectProvincia.disabled = false;
        }
    }
    
    function cargarDistritos() {
        if (!selectDepartamento || !selectProvincia || !selectDistrito) return;
        
        const departamento = selectDepartamento.value;
        const provincia = selectProvincia.value;
        
        selectDistrito.innerHTML = '<option value="">Seleccionar</option>';
        selectDistrito.disabled = true;
        
        if (departamento && provincia && ubigeoData[departamento][provincia]) {
            const distritos = ubigeoData[departamento][provincia];
            
            distritos.forEach(distrito => {
                const option = document.createElement('option');
                option.value = distrito;
                option.textContent = distrito;
                selectDistrito.appendChild(option);
            });
            
            selectDistrito.disabled = false;
        }
    }
    
    
    // ========================================================================
    // RESUMEN FINAL
    // ========================================================================
    
    function actualizarResumen() {
        const resumenRuc = document.getElementById('resumenRuc');
        if (resumenRuc) {
            resumenRuc.textContent = inputRuc.value || '-';
        }
        
        const resumenRazon = document.getElementById('resumenRazon');
        const razonSocial = document.getElementById('razon_social');
        if (resumenRazon && razonSocial) {
            resumenRazon.textContent = razonSocial.value || '-';
        }
        
        const resumenNombre = document.getElementById('resumenNombre');
        const nombreComercial = document.getElementById('nombre_comercial');
        if (resumenNombre && nombreComercial) {
            resumenNombre.textContent = nombreComercial.value || '-';
        }
        
        const resumenTitular = document.getElementById('resumenTitular');
        const nombresTitular = document.getElementById('nombres_titular');
        if (resumenTitular && nombresTitular) {
            resumenTitular.textContent = nombresTitular.value || '-';
        }
        
        const resumenTelefono = document.getElementById('resumenTelefono');
        const telefono = document.getElementById('telefono');
        if (resumenTelefono && telefono) {
            resumenTelefono.textContent = telefono.value || '-';
        }
        
        const resumenDireccion = document.getElementById('resumenDireccion');
        const direccion = document.getElementById('direccion');
        const distrito = document.getElementById('distrito');
        if (resumenDireccion && direccion) {
            const dir = direccion.value || '';
            const dist = distrito.value ? `, ${distrito.value}` : '';
            resumenDireccion.textContent = dir + dist || '-';
        }
        
        const resumenTipoCliente = document.getElementById('resumenTipoCliente');
        const tipoCliente = document.getElementById('tipo_cliente');
        if (resumenTipoCliente && tipoCliente && tipoCliente.value) {
            const tipoSeleccionado = politicasCliente[tipoCliente.value];
            resumenTipoCliente.textContent = tipoSeleccionado ? tipoSeleccionado.nombre : '-';
        }
    }
    
    
    // ========================================================================
    // GUARDAR CLIENTE
    // ========================================================================
    
    function guardarCliente(event) {
        event.preventDefault();
        
        if (!validarPaso3()) {
            return;
        }
        
        const datosCliente = {
            ruc: document.getElementById('numero_ruc')?.value.trim(),
            dni_titular: document.getElementById('numero_dni')?.value.trim(),
            razon_social: document.getElementById('razon_social')?.value.trim(),
            nombre_comercial: document.getElementById('nombre_comercial')?.value.trim(),
            nombres_titular: document.getElementById('nombres_titular')?.value.trim(),
            telefono: document.getElementById('telefono')?.value.trim(),
            email: document.getElementById('email')?.value.trim(),
            direccion: document.getElementById('direccion')?.value.trim(),
            referencia: document.getElementById('referencia')?.value.trim(),
            departamento: document.getElementById('departamento')?.value,
            provincia: document.getElementById('provincia')?.value,
            distrito: document.getElementById('distrito')?.value,
            tipo_cliente_id: document.getElementById('tipo_cliente')?.value
        };
        
        btnGuardarCliente.disabled = true;
        btnGuardarCliente.innerHTML = `
            <svg class="btn-icon animate-spin" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Guardando...
        `;
        
        setTimeout(() => {
            console.log('Datos a guardar:', datosCliente);
            
            btnGuardarCliente.disabled = false;
            btnGuardarCliente.innerHTML = `
                <svg class="btn-icon" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                Registrar Cliente
            `;
            
            mostrarNotificacion('✅ Cliente registrado exitosamente', 'success');
            
            agregarClienteAlSelect(datosCliente);
            
            setTimeout(() => {
                cerrarModal();
            }, 1000);
            
        }, 1500);
    }
    
    function agregarClienteAlSelect(cliente) {
        const selectCliente = document.getElementById('cliente');
        if (selectCliente && cliente.ruc && cliente.nombre_comercial) {
            const option = document.createElement('option');
            option.value = cliente.ruc;
            option.textContent = `${cliente.ruc} - ${cliente.nombre_comercial}`;
            option.selected = true;
            selectCliente.appendChild(option);
            
            selectCliente.dispatchEvent(new Event('change'));
        }
    }
    
    
    // ========================================================================
    // FUNCIONES DE FEEDBACK Y ERRORES
    // ========================================================================
    
    function mostrarFeedback(feedbackId, mensaje, tipo) {
        const feedback = document.getElementById(feedbackId);
        if (!feedback) return;
        
        feedback.textContent = mensaje;
        feedback.className = `input-feedback ${tipo}`;
    }
    
    function limpiarFeedback(feedbackId) {
        const feedback = document.getElementById(feedbackId);
        if (feedback) {
            feedback.textContent = '';
            feedback.className = 'input-feedback';
        }
    }
    
    function mostrarError(input, mensaje) {
        if (!input) return;
        
        const grupo = input.closest('.form-group-modern');
        if (!grupo) return;
        
        grupo.classList.add('campo-error');
        
        let mensajeError = grupo.querySelector('.mensaje-error');
        if (!mensajeError) {
            mensajeError = document.createElement('div');
            mensajeError.className = 'mensaje-error';
            grupo.appendChild(mensajeError);
        }
        mensajeError.textContent = mensaje;
    }
    
    function limpiarTodosLosErrores() {
        const camposError = document.querySelectorAll('.campo-error');
        camposError.forEach(campo => {
            campo.classList.remove('campo-error');
            const mensajeError = campo.querySelector('.mensaje-error');
            if (mensajeError) {
                mensajeError.remove();
            }
        });
    }
    
    function limpiarErrorCampo(input) {
        if (!input) return;
        const grupo = input.closest('.form-group-modern');
        if (grupo) {
            grupo.classList.remove('campo-error');
            const mensajeError = grupo.querySelector('.mensaje-error');
            if (mensajeError) {
                mensajeError.remove();
            }
        }
    }
    
    
    // ========================================================================
    // NOTIFICACIONES
    // ========================================================================
    
    function mostrarNotificacion(mensaje, tipo = 'success') {
        const notificacion = document.createElement('div');
        notificacion.className = `notificacion notificacion-${tipo}`;
        notificacion.innerHTML = `
            <i class="fas fa-${tipo === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${mensaje}</span>
        `;
        
        document.body.appendChild(notificacion);
        
        setTimeout(() => {
            notificacion.classList.add('notificacion-visible');
        }, 100);
        
        setTimeout(() => {
            notificacion.classList.remove('notificacion-visible');
            setTimeout(() => {
                notificacion.remove();
            }, 300);
        }, 3000);
    }
    
    
    // ========================================================================
    // EVENT LISTENERS
    // ========================================================================
    
    if (btnAbrirModal) {
        btnAbrirModal.addEventListener('click', abrirModal);
    }
    
    if (btnCerrarModal) {
        btnCerrarModal.addEventListener('click', cerrarModal);
    }
    
    if (btnCancelarModal) {
        btnCancelarModal.addEventListener('click', cerrarModal);
    }
    
    if (btnSiguiente) {
        btnSiguiente.addEventListener('click', siguientePaso);
    }
    
    if (btnAnterior) {
        btnAnterior.addEventListener('click', anteriorPaso);
    }
    
    if (btnGuardarCliente) {
        btnGuardarCliente.addEventListener('click', guardarCliente);
    }
    
    if (btnValidarRuc) {
        btnValidarRuc.addEventListener('click', validarRUC);
    }
    
    if (btnValidarDni) {
        btnValidarDni.addEventListener('click', validarDNI);
    }
    
    if (selectDepartamento) {
        selectDepartamento.addEventListener('change', cargarProvincias);
    }
    
    if (selectProvincia) {
        selectProvincia.addEventListener('change', cargarDistritos);
    }
    
    stepItems.forEach((step, index) => {
        step.addEventListener('click', function() {
            const stepNum = index + 1;
            if (stepNum <= pasoActual || this.classList.contains('completed')) {
                pasoActual = stepNum;
                mostrarPaso(stepNum);
            }
        });
    });
    
    const todosLosCampos = formNuevoCliente.querySelectorAll('input, select, textarea');
    todosLosCampos.forEach(campo => {
        campo.addEventListener('input', function() {
            limpiarErrorCampo(this);
        });
    });
    
    modalNuevoCliente.addEventListener('click', function(e) {
        if (e.target === modalNuevoCliente) {
            cerrarModal();
        }
    });
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modalNuevoCliente.classList.contains('modal-activo')) {
            cerrarModal();
        }
    });
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        .animate-spin {
            animation: spin 1s linear infinite;
        }
    `;
    document.head.appendChild(style);
    
});