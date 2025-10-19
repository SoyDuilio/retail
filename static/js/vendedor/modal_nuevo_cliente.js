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
        const modal = document.getElementById('modalNuevoCliente');
        
        if (modal) {
            modal.classList.remove('modal-activo');
            modal.classList.add('hidden'); // ✅ Agregar esta línea
        }
        
        document.body.style.overflow = '';
        
        // Resetear formulario
        if (formNuevoCliente) {
            formNuevoCliente.reset();
        }
        
        limpiarTodosLosErrores();
        ocultarDatosValidados();
        
        // Resetear wizard
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
        if (pasoActual === 1) {
            // Validar RUC y DNI
            if (!rucValidado) {
                mostrarNotificacion('Debes validar el RUC', 'error');
                return false;
            }
            if (!dniValidado) {
                mostrarNotificacion('Debes validar el DNI del titular', 'error');
                return false;
            }
            return true;
        }
        
        if (pasoActual === 2) {
            // Validar campos obligatorios del paso 2
            const telefono = document.getElementById('telefono').value.trim();
            const direccion = document.getElementById('direccion').value.trim();
            const departamento = document.getElementById('departamento_sunat').value.trim();
            const provincia = document.getElementById('provincia_sunat').value.trim();
            const distrito = document.getElementById('distrito_sunat').value.trim();
            
            if (!telefono) {
                mostrarNotificacion('El teléfono es obligatorio', 'error');
                document.getElementById('telefono').focus();
                return false;
            }
            
            if (telefono.length !== 9) {
                mostrarNotificacion('El teléfono debe tener 9 dígitos', 'error');
                document.getElementById('telefono').focus();
                return false;
            }
            
            if (!direccion) {
                mostrarNotificacion('La dirección es obligatoria', 'error');
                document.getElementById('direccion').focus();
                return false;
            }
            
            if (!departamento || !provincia || !distrito) {
                mostrarNotificacion('Completa la ubicación (departamento, provincia, distrito)', 'error');
                return false;
            }
            
            return true;
        }
        
        if (pasoActual === 3) {
            // Validar tipo de cliente
            const tipoCliente = document.getElementById('tipo_cliente').value;
            if (!tipoCliente) {
                mostrarNotificacion('Selecciona el tipo de cliente', 'error');
                return false;
            }
            return true;
        }
        
        return true;
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
    
    async function validarRUC() {
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
        
        try {
            const token = localStorage.getItem('auth_token');
            const response = await fetch(`/api/clientes/validar-ruc/${ruc}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            const data = await response.json();

            if (response.ok && data.success) {
                // Llenar campos con datos reales
                document.getElementById('razon_social').value = data.razon_social || '';
                document.getElementById('nombre_comercial').value = data.nombre_comercial || data.razon_social || '';
                
                // ✅ CORREGIR: Usar los IDs correctos del HTML
                const inputDireccion = document.getElementById('direccion');
                const inputDepartamento = document.getElementById('departamento_sunat');  // ✅
                const inputProvincia = document.getElementById('provincia_sunat');        // ✅
                const inputDistrito = document.getElementById('distrito_sunat');          // ✅
                
                // ✅ Verificar si es persona jurídica (tiene dirección y ubicación)
                if (data.direccion && data.departamento) {
                    // Persona jurídica: llenar y bloquear campos
                    if (inputDireccion) {
                        inputDireccion.value = data.direccion;
                        inputDireccion.setAttribute('readonly', 'readonly');
                    }
                    
                    if (inputDepartamento) {
                        inputDepartamento.value = data.departamento;
                        inputDepartamento.setAttribute('readonly', 'readonly');
                    }
                    
                    if (inputProvincia) {
                        inputProvincia.value = data.provincia;
                        inputProvincia.setAttribute('readonly', 'readonly');
                    }
                    
                    if (inputDistrito) {
                        inputDistrito.value = data.distrito;
                        inputDistrito.setAttribute('readonly', 'readonly');
                    }
                    
                } else {
                    // Persona natural: habilitar ingreso manual
                    if (inputDireccion) {
                        inputDireccion.value = '';
                        inputDireccion.removeAttribute('readonly');
                        inputDireccion.placeholder = 'Ingresa la dirección del negocio';
                    }
                    
                    if (inputDepartamento) {
                        inputDepartamento.value = '';
                        inputDepartamento.removeAttribute('readonly');
                        inputDepartamento.placeholder = 'Ej: Lima';
                    }
                    
                    if (inputProvincia) {
                        inputProvincia.value = '';
                        inputProvincia.removeAttribute('readonly');
                        inputProvincia.placeholder = 'Ej: Lima';
                    }
                    
                    if (inputDistrito) {
                        inputDistrito.value = '';
                        inputDistrito.removeAttribute('readonly');
                        inputDistrito.placeholder = 'Ej: Miraflores';
                    }
                    
                    mostrarNotificacion('RUC de persona natural. Ingresa la dirección y ubicación manualmente', 'info');
                }
                
                // Mostrar sección de datos validados
                const datosRuc = document.getElementById('datosRuc');
                if (datosRuc) {
                    datosRuc.classList.remove('hidden');
                }
                
                rucValidado = true;
                mostrarFeedback('feedbackRuc', `✓ ${data.razon_social} - ${data.estado}`, 'success');
                mostrarNotificacion('Datos de SUNAT obtenidos correctamente', 'success');
                
            } else {
                mostrarFeedback('feedbackRuc', data.message || 'RUC no encontrado', 'error');
                mostrarNotificacion('No se pudo validar el RUC', 'error');
                rucValidado = false;
            }
            
        } catch (error) {
            console.error('Error validando RUC:', error);
            mostrarFeedback('feedbackRuc', 'Error al conectar con SUNAT', 'error');
            mostrarNotificacion('Error de conexión', 'error');
            rucValidado = false;
            
        } finally {
            btnValidarRuc.disabled = false;
            btnValidarRuc.innerHTML = `
                <svg class="btn-icon" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                Validar
            `;
        }
    }
    
    
    // ========================================================================
    // VALIDACIÓN AUTOMÁTICA DE DNI (8 DÍGITOS)
    // ========================================================================
    
    async function validarDNI() {
        const dni = document.getElementById('numero_dni').value.trim();
        
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
        
        const btnValidarDni = document.getElementById('btnValidarDni');
        btnValidarDni.disabled = true;
        btnValidarDni.innerHTML = `
            <svg class="btn-icon animate-spin" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Validando...
        `;
        
        try {
            const token = localStorage.getItem('auth_token');
            const response = await fetch(`/api/clientes/validar-dni/${dni}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                // ✅ VERIFICAR IDs correctos del HTML
                const inputNombres = document.getElementById('nombres_titular');
                const inputApPaterno = document.getElementById('apellido_paterno_titular');
                const inputApMaterno = document.getElementById('apellido_materno_titular');
                
                if (inputNombres) inputNombres.value = data.nombres || '';
                if (inputApPaterno) inputApPaterno.value = data.apellido_paterno || '';
                if (inputApMaterno) inputApMaterno.value = data.apellido_materno || '';
                
                // Mostrar datos validados
                const datosDni = document.getElementById('datosDni');
                if (datosDni) {
                    datosDni.classList.remove('hidden');
                }
                
                dniValidado = true;
                mostrarFeedback('feedbackDni', `✓ ${data.nombre_completo}`, 'success');
                mostrarNotificacion('DNI validado correctamente', 'success');
                
            } else {
                // ✅ MANEJAR ERROR
                mostrarFeedback('feedbackDni', data.message || 'DNI no encontrado', 'error');
                mostrarNotificacion('No se pudo validar el DNI', 'error');
                dniValidado = false;
            }
            
        } catch (error) {
            console.error('Error validando DNI:', error);
            mostrarFeedback('feedbackDni', 'Error al conectar con RENIEC', 'error');
            mostrarNotificacion('Error de conexión', 'error');
            dniValidado = false;
            
        } finally {
            btnValidarDni.disabled = false;
            btnValidarDni.innerHTML = `
                <svg class="btn-icon" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                Validar
            `;
        }
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


/*========================================
✅ GRABAR NUEVO CLIENTE - JS
=========================================*/
async function finalizarRegistro() {
    // Validar paso 3
    const tipoCliente = document.getElementById('tipo_cliente').value;
    if (!tipoCliente) {
        mostrarNotificacion('Selecciona el tipo de cliente', 'error');
        return;
    }
    
    // Obtener ubicación del vendedor (GPS)
    if (!navigator.geolocation) {
        mostrarNotificacion('Tu navegador no soporta geolocalización', 'error');
        return;
    }
    
    // Deshabilitar botón mientras procesa
    const btnGuardarCliente = document.getElementById('btnGuardarCliente');
    const textoOriginal = btnGuardarCliente.innerHTML;
    btnGuardarCliente.disabled = true;
    btnGuardarCliente.innerHTML = `
        <svg class="animate-spin" width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
        </svg>
        Guardando...
    `;
    
    // Capturar ubicación GPS
    navigator.geolocation.getCurrentPosition(
        async (position) => {
            try {
                // Construir objeto según ClienteCreate schema
                const nuevoCliente = {
                    // Campos obligatorios de ClienteBase
                    nombre_comercial: document.getElementById('nombre_comercial').value.trim(),
                    razon_social: document.getElementById('razon_social').value.trim(),
                    ruc: document.getElementById('numero_ruc').value.trim(),
                    telefono: document.getElementById('telefono').value.trim(),
                    email: document.getElementById('email').value.trim() || null,
                    direccion_completa: document.getElementById('direccion').value.trim(),
                    referencia: document.getElementById('referencia').value.trim() || null,
                    distrito: document.getElementById('distrito_sunat').value.trim(),
                    provincia: document.getElementById('provincia_sunat').value.trim(),
                    departamento: document.getElementById('departamento_sunat').value.trim(),
                    codigo_postal: null,
                    tipo_cliente_id: parseInt(tipoCliente),
                    
                    // Campos adicionales de ClienteCreate
                    dni_titular: document.getElementById('numero_dni').value.trim() || null,
                    nombres_titular: construirNombreCompleto(),
                    latitud: position.coords.latitude.toFixed(6),
                    longitud: position.coords.longitude.toFixed(6),
                    precision_gps: Math.round(position.coords.accuracy)
                };
                
                console.log('📤 Enviando cliente:', nuevoCliente);
                
                // Enviar al backend
                const token = localStorage.getItem('auth_token');
                const response = await fetch('/api/clientes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(nuevoCliente)
                });
                
                const data = await response.json();
                console.log('📥 Respuesta servidor:', data);
                
                if (response.ok) {
                    mostrarNotificacion(`¡Cliente ${data.codigo_cliente} registrado exitosamente!`, 'success');
                    
                    // Cerrar modal y limpiar
                    cerrarModal();
                    limpiarFormulario();
                    
                    // Si hay callback para seleccionar automáticamente el cliente
                    if (window.onClienteCreado && typeof window.onClienteCreado === 'function') {
                        window.onClienteCreado(data);
                    }
                    
                } else {
                    console.error('❌ Error del servidor:', data);
                    mostrarNotificacion(data.detail || 'Error al registrar cliente', 'error');
                }
                
            } catch (error) {
                console.error('❌ Error de red:', error);
                mostrarNotificacion('Error de conexión al guardar', 'error');
            } finally {
                btnGuardarCliente.disabled = false;
                btnGuardarCliente.innerHTML = textoOriginal;
            }
        },
        (error) => {
            console.error('❌ Error GPS:', error);
            let mensaje = 'No se pudo obtener la ubicación. ';
            
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    mensaje += 'Activa los permisos de ubicación.';
                    break;
                case error.POSITION_UNAVAILABLE:
                    mensaje += 'Activa el GPS de tu dispositivo.';
                    break;
                case error.TIMEOUT:
                    mensaje += 'Tiempo de espera agotado.';
                    break;
            }
            
            mostrarNotificacion(mensaje, 'error');
            btnGuardarCliente.disabled = false;
            btnGuardarCliente.innerHTML = textoOriginal;
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        }
    );
}

// Función auxiliar para construir nombre completo del titular
function construirNombreCompleto() {
    const nombres = document.getElementById('nombres_completos')?.value.trim() || '';
    
    // Si hay un campo "nombres_completos" ya lleno, usarlo
    if (nombres) return nombres;
    
    // Si no, intentar construir desde nombres separados (del DNI validado)
    const nombresInput = document.getElementById('nombres_titular')?.value.trim() || '';
    const apPaterno = document.getElementById('apellido_paterno')?.value.trim() || '';
    const apMaterno = document.getElementById('apellido_materno')?.value.trim() || '';
    
    return `${nombresInput} ${apPaterno} ${apMaterno}`.trim() || null;
}

// Función auxiliar para limpiar formulario
function limpiarFormulario() {
    document.getElementById('formNuevoCliente').reset();
    rucValidado = false;
    dniValidado = false;
    pasoActual = 1;
    mostrarPaso(1);
}
