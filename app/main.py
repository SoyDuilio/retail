# 1. IMPORTS CORRECTOS AL INICIO DEL ARCHIVO:
# Reemplaza los imports que tienes por estos:

from sqlalchemy import and_, or_
from fastapi import FastAPI, HTTPException, Depends, status, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta, timezone
import requests
import re
import os
from sqlalchemy.sql import text
from google.cloud import speech
from google.oauth2 import service_account
from app.apis.utils import api_client, validar_formato_ruc, validar_formato_dni, procesar_datos_empresa, procesar_datos_persona
from app.apis.vfp import rutas_vfp
from app.routers.admin import panel_sync 
from app.routers import pricing
from app.routers.vendedor import credito
from api.endpoints import clientes, ubicaciones, vfp_test

# --- CONSTRUCCIÓN DE RUTA ABSOLUTA PARA CREDENCIALES (VERSIÓN CORREGIDA) ---
# 1. Obtiene la ruta del directorio donde se encuentra este archivo (main.py)
#    Esto probablemente sea C:\PEDIDOS\app
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Navega "un nivel hacia arriba" para llegar al directorio raíz del proyecto (C:\PEDIDOS)
BASE_DIR = os.path.dirname(APP_DIR)

# 3. Define el nombre de tu archivo de credenciales
CREDENTIALS_FILENAME = "google-speech-credentials-PEDIDOS.json"

# 4. Construye la ruta correcta: [Directorio Raíz] + [core] + [nombre_archivo]
#    Ej: C:\PEDIDOS + \core\ + google-speech-credentials-PEDIDOS.json
GOOGLE_CREDENTIALS_PATH = os.path.join(BASE_DIR, "core", CREDENTIALS_FILENAME)

if os.path.exists(GOOGLE_CREDENTIALS_PATH):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDENTIALS_PATH
    print(f"✅ Credenciales de Google cargadas desde: {GOOGLE_CREDENTIALS_PATH}")
else:
    print(f"❌ ALERTA: No se encontró el archivo de credenciales de Google en la ruta esperada: {GOOGLE_CREDENTIALS_PATH}")
    print("   El endpoint de Google Speech-to-Text fallará.")

# Agregar imports faltantes:
from core.auth import create_access_token, verify_token
#from app.schemas import ConversacionVozCreate, TranscripcionCreate, CalificacionCreate #, MensajeCreate
from app.schemas.common_schemas import Mensaje  # o definirlo si no existe
import json

from decimal import Decimal
import uuid
#from app.models.user_models import SesionActivaModel as SesionActiva, VendedorModel as Vendedor, EvaluadorModel as Evaluador, SupervisorModel as Supervisor
from app.schemas.common_schemas import Response, PaginatedResponse, CalculoPrecio, ResultadoPrecio, FiltrosPedidos, KDSPedido, CalificacionUpdate, DashboardMetricas, RankingVendedor
from starlette.websockets import WebSocket, WebSocketDisconnect 
# Para ResultadoPrecio: definir en common_schemas.py o usar ProductoPrecio

# Imports de tu aplicación - CORREGIDOS
from app.database import get_db, engine, Base
from app.websocket_manager import ConnectionManager

# Core imports - CORREGIDOS
from core.config import settings
from core.auth import (
    authenticate_user,
    create_user_session,
    get_current_user,
    get_current_vendedor,
    get_current_evaluador, 
    get_current_supervisor,
    hash_password
)

# Schema imports - CORREGIDOS
from app.schemas.common_schemas import (
    # Enums
    RolUsuario, TipoUsuario, EstadoPedido, TipoMensaje, CategoriaProducto,
    UnidadMedida, TipoCliente,
    # Responses
    BaseResponse, DataResponse, ListResponse, ErrorResponse,
    # Auth
    LoginRequest, LoginResponse, TokenInfo,
    # Filtros
    PaginationParams, FiltrosProductos,
    # API Models
    #Vendedor, Evaluador, Supervisor, Cliente, ProductoPrecio, PedidoCreate,
    # Utilidades
    HealthCheck, Coordenadas
)

# User schemas
from app.schemas.user_schemas import (
    VendedorCreate, VendedorUpdate, VendedorResponse,
    EvaluadorCreate, EvaluadorUpdate, EvaluadorResponse,
    SupervisorCreate, SupervisorUpdate, SupervisorResponse
)

# CRUD imports - CORREGIDOS  
from crud.crud_user import (
    crud_vendedor, crud_evaluador, crud_supervisor, crud_sesion_activa
)
from crud.crud_client import crud_cliente

# Model imports
# Reemplazar tus importaciones actuales por:
from app.models import VendedorModel, ProductoModel, ClienteModel, EvaluadorModel, SupervisorModel, TipoClienteModel, CategoriaModel, CalificacionModel

from contextlib import asynccontextmanager

# ============================================
# PARA LAS ESTADÍSTICAS
# ============================================
#from app.routers import auth, utils
#from app.routers.vendedor import operaciones as vendedor_ops
from app.routers.vendedor import estadisticas as vendedor_stats
from app.routers.vendedor import estadisticas as vendedor_estadisticas
from app.routers.evaluador import evaluaciones
from app.routers.evaluador import websocket as evaluador_ws
#from app.routers.compartido import clientes, productos, pedidos
from api.v1 import rutas_pedidos

# Función auxiliar para obtener la hora actual en UTC
def get_utc_now():
    return datetime.now(timezone.utc)

class CalificacionCreate(BaseModel):
    pedido_id: int
    estado: str
    monto_solicitado: float

# Y crear las clases temporales que faltan:
class ProductoPrecio(BaseModel):
    producto_id: int
    codigo_producto: str
    nombre: str
    precio_unitario: float
    precio_mayorista: Optional[float] = None
    stock_disponible: int

class ConversacionVozCreate(BaseModel):
    vendedor_id: int
    cliente_id: int
    duracion_segundos: float
    archivo_audio_url: str

class TranscripcionCreate(BaseModel):
    archivo_audio_url: str
    idioma_origen: str = "es"

class PedidoCreate(BaseModel):
    cliente_id: int
    items: List[Dict[str, Any]] = Field(..., min_items=1)
    observaciones: Optional[str] = None
    coordenadas_entrega: Optional[Dict[str, Any]] = None

# Modelos para el procesamiento de texto
class ProcesarTextoRequest(BaseModel):
    texto: str
    es_voz: Optional[bool] = False

class ProductoDetectado(BaseModel):
    producto_id: Optional[int] = None
    nombre: str
    cantidad: float
    unidad: str
    variante: Optional[str] = None
    precio_unitario: Optional[float] = None
    precio_total: Optional[float] = None
    encontrado: bool = False

class BuscarClienteRequest(BaseModel):
    texto: str

# ACTUALIZADO según tu ClienteModel
class ClienteEncontrado(BaseModel):
    cliente_id: int
    ruc: str
    razon_social: str
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    whatsapp: Optional[str] = None
    direccion: Optional[str] = None
    contacto_nombres: Optional[str] = None  # Quien hace el pedido
    limite_credito: Optional[float] = None
    credito_disponible: Optional[float] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Iniciando servidor...")
    try:
        from app.database import engine
        with engine.connect() as conn:

            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        print("✅ BD conectada")
    except Exception as e:
        print(f"❌ Error BD: {e}")
    
    yield
    
    # Shutdown (opcional)
    print("🔴 Cerrando servidor...")

# =============================================
# CONFIGURACIÓN FASTAPI
# =============================================

app = FastAPI(
    title="Sistema de Distribución con Evaluación Crediticia",
    description="Sistema completo para vendedores de campo con evaluación en tiempo real",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Archivos estáticos y templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Security
security = HTTPBearer()
manager = ConnectionManager()


# ==================
# ROUTERS
# ==================
#app.include_router(auth.router)
#app.include_router(vendedor_ops.router)
app.include_router(vendedor_stats.router)
app.include_router(vendedor_estadisticas.router)
app.include_router(rutas_pedidos.router)
app.include_router(evaluaciones.router)
app.include_router(evaluador_ws.router)
app.include_router(rutas_vfp.router)
app.include_router(panel_sync.router)
app.include_router(clientes.router,tags=["clientes"])
app.include_router(ubicaciones.router, tags=["ubicaciones"])
app.include_router(vfp_test.router, tags=["VFP Testing"])
app.include_router(pricing.router, prefix="/api")
app.include_router(credito.router, prefix="/api/vendedor", tags=["vendedor-credito"])
# =============================================
# FUNCIONES AUXILIARES  
# =============================================
# En main.py, cerca de tus otras funciones de ayuda

@app.get("/api/utils/ruc/{ruc}")
async def validar_ruc(ruc: str):
    """Endpoint para validar RUC y obtener datos de la empresa"""
    
    print(f"\n===> Validando RUC: {ruc}")
    
    # Validación de formato usando función auxiliar
    if not validar_formato_ruc(ruc):
        print(f"!!! Error: Formato de RUC inválido: '{ruc}'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Formato de RUC inválido. Debe tener 11 dígitos y comenzar con 10 o 20"
        )
    
    print("===> Formato de RUC válido")

    try:
        # Consultar API externa
        company_data = api_client.get_company(ruc=ruc)
        print(f"===> Datos recibidos: {company_data}")
        
        # Procesar datos usando función auxiliar
        processed_data = procesar_datos_empresa(company_data)
        
        if not processed_data:
            print("!!! No se encontraron datos para el RUC")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="RUC no encontrado en SUNAT"
            )
        
        # Agregar RUC a la respuesta
        response_data = {"ruc": ruc, **processed_data}
        print(f"===> Respuesta exitosa: {response_data}")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"!!! Excepción inesperada: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno al procesar la solicitud"
        )


@app.get("/api/utils/dni/{dni}")
async def validar_dni(dni: str):
    """Endpoint para validar DNI y obtener datos de la persona"""
    
    print(f"\n===> Validando DNI: {dni}")
    
    # Validación de formato usando función auxiliar
    if not validar_formato_dni(dni):
        print(f"!!! Error: Formato de DNI inválido: '{dni}'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de DNI inválido. Debe tener 8 dígitos"
        )
    
    print("===> Formato de DNI válido")

    try:
        # Consultar API externa
        person_data = api_client.get_person(dni=dni)
        print(f"===> Datos recibidos: {person_data}")
        
        # Procesar datos usando función auxiliar
        processed_data = procesar_datos_persona(person_data)
        
        if not processed_data:
            print("!!! No se encontraron datos para el DNI")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="DNI no encontrado en RENIEC"
            )
        
        # Agregar DNI a la respuesta
        response_data = {"dni": dni, **processed_data}
        print(f"===> Respuesta exitosa: {response_data}")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"!!! Excepción inesperada: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno al procesar la solicitud"
        )


from typing import Dict, Any

@app.post("/api/vendedor/ubicacion")
async def guardar_ubicacion(
    ubicacion: Dict[str, Any],
    current_vendedor: VendedorModel = Depends(get_current_vendedor),
    db: Session = Depends(get_db)
):
    """
    Guarda la ubicación actual del vendedor.
    Puede usarse para registro de ruta o validación de visitas.
    """
    try:
        latitud = ubicacion.get('latitud')
        longitud = ubicacion.get('longitud')
        precision = ubicacion.get('precision')
        timestamp = ubicacion.get('timestamp')
        
        print(f"📍 Ubicación vendedor {current_vendedor.vendedor_id}: {latitud}, {longitud}")
        
        # Si tienes una tabla de ubicaciones, guárdala aquí
        # Ejemplo:
        # nueva_ubicacion = UbicacionVendedorModel(
        #     vendedor_id=current_vendedor.vendedor_id,
        #     latitud=latitud,
        #     longitud=longitud,
        #     precision=precision,
        #     timestamp=timestamp
        # )
        # db.add(nueva_ubicacion)
        # db.commit()
        
        return DataResponse(
            success=True,
            message="Ubicación registrada correctamente",
            data={
                "latitud": latitud,
                "longitud": longitud,
                "timestamp": timestamp
            }
        )
        
    except Exception as e:
        print(f"❌ Error guardando ubicación: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# FUNCIONES DE AYUDA PARA PROCESAMIENTO DE PEDIDOS
# =============================================

def normalizar_texto_pedido(texto: str) -> str:
    """Limpia y estandariza el texto de un pedido para facilitar su procesamiento."""
    
    texto = texto.lower()
    # --- AÑADIDO: Reemplazar guiones por espacios ---
    texto = texto.replace('-', ' ')
    
    # Mapeo de números-palabra a dígitos
    numeros = {
        "un": "1", "una": "1", "uno": "1",
        "dos": "2", "tres": "3", "cuatro": "4", "cinco": "5",
        "seis": "6", "siete": "7", "ocho": "8", "nueve": "9", "diez": "10",
        "media docena": "6", "docena": "12"
    }
    
    # Mapeo de correcciones y abreviaturas comunes
    correcciones = {
        "inca": "inca kola",
        "gloria": "leche gloria", # Si la palabra "gloria" sola suele ser leche
        "kilo": "kg",
        # Puedes añadir más correcciones aquí
    }
    
    # Palabras de relleno a eliminar que confunden a los patrones
    stop_words = ["quiero", "dame", "deme", "unidades de", "unidad de", "de", "por favor", "y"]

    # Aplicar reemplazos
    for palabra, digito in numeros.items():
        texto = texto.replace(f" {palabra} ", f" {digito} ") # Con espacios para evitar reemplazar dentro de otras palabras
        if texto.startswith(palabra + " "):
            texto = digito + texto[len(palabra):]

    for incorrecta, correcta in correcciones.items():
        texto = texto.replace(incorrecta, correcta)
        
    # Reemplazar comas y "y" por un separador estándar para múltiples items
    texto = texto.replace(' y ', ' , ').replace(',', ' , ')

    # Eliminar stop words
    palabras = texto.split()
    palabras_filtradas = [palabra for palabra in palabras if palabra not in stop_words]
    
    return " ".join(palabras_filtradas)


# =============================================
# ENDPOINT DE PROCESAMIENTO DE PEDIDOS (MOTOR INTERNO MEJORADO)
# =============================================

@app.post("/api/pedidos/procesar-texto")
async def procesar_texto_pedido(
    request: ProcesarTextoRequest,
    current_vendedor: VendedorModel = Depends(get_current_vendedor),
    db: Session = Depends(get_db)
):
    print(f"=== INICIO PROCESAR TEXTO (Motor Interno) ===")
    print(f"Texto original: '{request.texto}'")

    if not request.texto or not request.texto.strip():
        return DataResponse[List](success=False, message="El texto está vacío.", data=[])

    # --- PASO 1: Usamos la nueva función de normalización ---
    texto_normalizado = normalizar_texto_pedido(request.texto)
    print(f"Texto Normalizado: '{texto_normalizado}'")
    
    # Separamos por comas para procesar múltiples items
    items_texto = [item.strip() for item in texto_normalizado.split(',') if item.strip()]
    productos_detectados: List[ProductoDetectado] = []

    try:
        # Patrones ordenados de más específico a más general
        patrones = [
            # 1. Cantidad + unidad + producto (ej: "2 cajas coca cola 500ml")
            re.compile(r"^(?P<cantidad>\d+(?:\.\d+)?)\s*(?P<unidad>cajas?|docenas?|unidades?|litros?|kilos?|kg|paquetes?|bolsas?)\s*(?P<producto>.+)", re.IGNORECASE),
            # 2. Cantidad + producto (ej: "2 leches gloria")
            re.compile(r"^(?P<cantidad>\d+(?:\.\d+)?)\s*(?P<producto>.+)", re.IGNORECASE),
            # 3. Solo producto (asume cantidad 1)
            re.compile(r"^(?P<producto>[a-zA-Z\s\d./-]+)$", re.IGNORECASE)
        ]

        # Procesamos cada item de texto por separado
        for texto_item in items_texto:
            print(f"-- Procesando item: '{texto_item}'")
            match_encontrado = None
            
            for patron in patrones:
                match = patron.match(texto_item)
                if match:
                    match_encontrado = match
                    print(f"   Match con patrón: {patron.pattern}")
                    break

            if match_encontrado:
                partes = match_encontrado.groupdict()
                cantidad = float(partes.get("cantidad", 1.0))
                unidad = (partes.get("unidad") or "unidades").lower()
                producto_texto = partes.get("producto", "").strip()

                print(f"   Extraído -> Cantidad: {cantidad}, Unidad: {unidad}, Producto: '{producto_texto}'")
                
                palabras_busqueda = [palabra for palabra in producto_texto.split() if len(palabra) > 1]
                if not palabras_busqueda:
                    continue

                # Búsqueda en la base de datos
                producto_query = db.query(ProductoModel).filter(
                    ProductoModel.activo == True,
                    # Ahora busca productos que contengan CUALQUIERA de las palabras clave
                    or_(*[ProductoModel.nombre.ilike(f"%{palabra}%") for palabra in palabras_busqueda])
                ).first()

                if producto_query:
                    print(f"   ✅ Producto encontrado en BD: {producto_query.nombre}")
                    producto_detectado = ProductoDetectado(
                        producto_id=producto_query.id,
                        nombre=producto_query.nombre,
                        cantidad=cantidad,
                        unidad=unidad.rstrip('s'),
                        precio_unitario=float(producto_query.precio_unitario),
                        precio_total=float(producto_query.precio_unitario) * cantidad,
                        encontrado=True
                    )
                    productos_detectados.append(producto_detectado)
                else:
                    print(f"   ❌ Producto NO encontrado en BD: '{producto_texto}'")
                    producto_detectado = ProductoDetectado(
                        nombre=producto_texto,
                        cantidad=cantidad,
                        unidad=unidad,
                        encontrado=False
                    )
                    productos_detectados.append(producto_detectado)
            else:
                 print(f"   No se encontró patrón para: '{texto_item}'")

        if not productos_detectados:
            return DataResponse[List](
                success=False,
                message="No se pudieron identificar productos en el texto.",
                data=[]
            )

        print(f"=== FIN PROCESAR TEXTO: {len(productos_detectados)} producto(s) detectado(s) ===")
        return DataResponse[List[ProductoDetectado]](
            success=True,
            message=f"Se identificaron {len(productos_detectados)} producto(s)",
            data=productos_detectados
        )

    except Exception as e:
        print(f"Error procesando texto: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno al procesar el texto: {e}")





def generar_numero_pedido_diario(db: Session) -> str:
    """Genera un número de pedido único y secuencial para el día."""
    from app.models.order_models import PedidoModel # Importación local para evitar importación circular
    from datetime import date
    
    hoy = date.today()
    # Contamos los pedidos ya creados hoy
    cantidad_hoy = db.query(PedidoModel).filter(PedidoModel.fecha == hoy).count()
    # Formato: PED-YYYYMMDD-0001
    return f"PED-{hoy.strftime('%Y%m%d')}-{cantidad_hoy + 1:04d}"

# =============================================
# AUTENTICACIÓN Y SESIONES
# =============================================

@app.get("/api/test-db")
async def test_db():
    """Test de conexión a base de datos"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f" 🔥🎈🌟🌩Resultado test DB: {result.fetchone()}")
            return {"success": True, "message": "DB conectada OK"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    print("🟦 INICIO login endpoint")
    try:
        print(f"🟦 Datos: {login_data}")
        print(f"🟦 Buscando {login_data.tipo_usuario} con DNI: {login_data.usuario}")
        
        user_data = None
        
        if login_data.tipo_usuario == "vendedor":
            print("🟦 Entrando a buscar vendedor")
            vendedor = db.query(VendedorModel).filter(
                VendedorModel.dni == login_data.usuario,
                VendedorModel.activo == True
            ).first()
            print(f"🟦 Vendedor encontrado: {vendedor}")
            
            if vendedor:
                print("🟦 Verificando password")
                password_ok = vendedor.check_password(login_data.clave)
                print(f"🟦 Password OK: {password_ok}")
                
                if password_ok:
                    user_data = {
                        "id": vendedor.vendedor_id,
                        "tipo": "vendedor",
                        "nombre": f"{vendedor.nombre} {vendedor.apellidos}",
                        "dni": vendedor.dni,
                        "redirect_url": f"/vendedor/ventas-externas/{vendedor.vendedor_id}"
                    }
                    print(f"🟦 User data creado: {user_data}")
        
        elif login_data.tipo_usuario == "evaluador":
            print("🟦 Entrando a buscar evaluador")
            evaluador = db.query(EvaluadorModel).filter(
                EvaluadorModel.dni == login_data.usuario,
                EvaluadorModel.activo == True
            ).first()
            print(f"🟦 Evaluador encontrado: {evaluador}")
            
            if evaluador:
                print("🟦 Verificando password del evaluador")
                password_ok = evaluador.check_password(login_data.clave)
                print(f"🟦 Password OK: {password_ok}")
                
                if password_ok:
                    user_data = {
                        "id": evaluador.evaluador_id,
                        "tipo": "evaluador", 
                        "nombre": f"{evaluador.nombre} {evaluador.apellidos}",
                        "dni": evaluador.dni,
                        "redirect_url": f"/evaluador/dashboard/{evaluador.evaluador_id}"
                    }
                    print(f"🟦 User data creado: {user_data}")
        
        elif login_data.tipo_usuario == "supervisor":
            print("🟦 Entrando a buscar supervisor")
            supervisor = db.query(SupervisorModel).filter(
                SupervisorModel.dni == login_data.usuario,
                SupervisorModel.activo == True
            ).first()
            print(f"🟦 Supervisor encontrado: {supervisor}")
            
            if supervisor:
                print("🟦 Verificando password del supervisor")
                password_ok = supervisor.check_password(login_data.clave)
                print(f"🟦 Password OK: {password_ok}")
                
                if password_ok:
                    user_data = {
                        "id": supervisor.supervisor_id,
                        "tipo": "supervisor",
                        "nombre": f"{supervisor.nombre} {supervisor.apellidos}",
                        "dni": supervisor.dni,
                        "redirect_url": f"/supervisor/dashboard/{supervisor.supervisor_id}"
                    }
                    print(f"🟦 User data creado: {user_data}")
        
        else:
            print(f"🟦 Tipo de usuario no válido: {login_data.tipo_usuario}")
        
        print(f"🟦 User data final: {user_data}")
        
        if not user_data:
            print("🟦 Lanzando HTTPException por credenciales")
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        print("🟦 Creando token")
        token = create_access_token(user_data)
        print(f"🟦 Token creado: {token[:20]}...")
        
        print("🟦 FIN - devolviendo respuesta")
        return LoginResponse(
            success=True,
            token=token,
            access_token=token,
            usuario_id=user_data["id"],
            usuario_tipo=login_data.tipo_usuario,
            nombre_completo=user_data["nombre"],
            token_type="bearer",
            expires_in=3600 * 8,
            user_info=user_data,
            session_id=str(uuid.uuid4())
        )
        
    except Exception as e:
        print(f"🟦 ERROR: {e}")
        raise HTTPException(status_code=422, detail=str(e))

@app.post("/api/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Cerrar sesión"""
    # Invalidar token y sesión
    return {"success": True, "message": "Sesión cerrada correctamente"}


# =============================================
# DASGHBOARD VENDEDOR
# ============================================= 
@app.get("/vendedor/ventas-externas/{vendedor_id}", response_class=HTMLResponse)
async def vendedor_ventas_externas(request: Request, vendedor_id: int):
    return templates.TemplateResponse("vendedor/ventas_externas.html", {"request": request})


# =============================================
# PRODUCTOS Y CATÁLOGO
# =============================================

@app.get("/api/productos", response_model=List[ProductoPrecio])
async def obtener_productos(
    filtros: FiltrosProductos = Depends(),
    db: Session = Depends(get_db)
):
    """Obtener productos con precios según tipo de cliente"""
    # Implementar consulta con filtros
    query = """
    SELECT * FROM v_productos_precios 
    WHERE 1=1
    """
    
    # Agregar filtros dinámicamente
    params = {}
    if filtros.categoria_id:
        query += " AND categoria_id = :categoria_id"
        params["categoria_id"] = filtros.categoria_id
    
    if filtros.tipo_cliente_id:
        query += " AND tipo_cliente_id = :tipo_cliente_id"
        params["tipo_cliente_id"] = filtros.tipo_cliente_id
    
    if filtros.buscar:
        query += " AND (producto_nombre ILIKE :buscar OR codigo ILIKE :buscar)"
        params["buscar"] = f"%{filtros.buscar}%"
    
    if filtros.stock_bajo:
        query += " AND estado_stock = 'STOCK_BAJO'"
    
    query += f" LIMIT {filtros.size} OFFSET {(filtros.page - 1) * filtros.size}"
    
    # Ejecutar consulta
    # resultado = db.execute(query, params)
    # return [ProductoPrecio(**row) for row in resultado]
    
    # Mock data por ahora
    return []

@app.post("/api/productos/calcular-precio", response_model=ResultadoPrecio)
async def calcular_precio(
    calculo: CalculoPrecio,
    db: Session = Depends(get_db)
):
    """Calcular precio con descuentos por volumen"""
    # Obtener precio del producto para el tipo de cliente
    # Aplicar descuentos por volumen según cantidad
    # Retornar precio final calculado
    
    # Mock implementation
    return ResultadoPrecio(
        precio_unitario=10.50,
        descuento_aplicado=5.0,
        precio_final=9.98,
        subtotal=99.80,
        total=99.80,
        descuento_por_volumen=True,
        nivel_descuento=1
    )

# =============================================
# PEDIDOS
# =============================================

@app.post("/api/pedidos/crear")
async def crear_pedido(
    request: Dict[str, Any],
    current_vendedor: VendedorModel = Depends(get_current_vendedor),
    db: Session = Depends(get_db)
):
    from app.models.order_models import PedidoModel, TipoVentaEnum,TipoPagoEnum, PedidoItemModel
    """Crea un nuevo pedido"""
    try:
        # Generar número de pedido
        fecha_actual = datetime.now()
        numero_pedido = f"PED-{fecha_actual.strftime('%Y%m%d')}-{current_vendedor.vendedor_id:03d}-{int(fecha_actual.timestamp()) % 1000:03d}"
        
        # Crear el pedido
        nuevo_pedido = PedidoModel(
            numero_pedido=numero_pedido,
            fecha=fecha_actual.date(),
            hora=fecha_actual.time(),
            vendedor_id=current_vendedor.vendedor_id,
            cliente_id=request['cliente_id'],
            tipo_venta=TipoVentaEnum.externa,  # Ajustar según tu enum
            tipo_pago=TipoPagoEnum.credito if 'credito' in request.get('modalidad_pago', '').lower() else TipoPagoEnum.efectivo,
            latitud_pedido=request.get('ubicacion', {}).get('latitud'),
            longitud_pedido=request.get('ubicacion', {}).get('longitud'),
            observaciones=request.get('observaciones', '')
        )
        
        db.add(nuevo_pedido)
        db.flush()  # Para obtener el ID
        
        # Agregar items del pedido
        for item_data in request['productos']:
            item = PedidoItemModel(
                pedido_id=nuevo_pedido.id,
                producto_id=item_data['producto_id'],
                cantidad=item_data['cantidad'],
                precio_unitario=item_data['precio_unitario'],
                subtotal=item_data['subtotal'],
                total=item_data['subtotal']  # Ajustar si hay descuentos
            )
            db.add(item)
        
        # Calcular totales
        nuevo_pedido.calcular_totales()
        
        db.commit()
        db.refresh(nuevo_pedido)
        
        return DataResponse(
            success=True,
            message="Pedido creado exitosamente",
            data={
                "numero_pedido": numero_pedido,
                "pedido_id": str(nuevo_pedido.id),
                "total": float(nuevo_pedido.total),
                "estado": "pendiente"
            }
        )
        
    except Exception as e:
        db.rollback()
        print(f"Error creando pedido: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pedidos", response_model=DataResponse, status_code=status.HTTP_201_CREATED)
async def crear_pedido(
    pedido_in: PedidoCreate, 
    db: Session = Depends(get_db),
    current_vendedor: VendedorModel = Depends(get_current_vendedor)
):
    """
    Crea un nuevo pedido con cálculo de precios y totales desde el backend.
    """
    # Importamos los modelos y schemas específicos que usaremos en esta función
    from app.models.client_models import ClienteModel
    from app.models.product_models import ProductoModel, PrecioModel
    from app.models.order_models import PedidoModel, PedidoItemModel
    from app.schemas.order_schemas import KDSPedido
    # --- 1. VALIDACIONES DE NEGOCIO ---
    # Busca al cliente en la base de datos
    cliente = db.query(ClienteModel).filter(ClienteModel.id == pedido_in.cliente_id).first()
    if not cliente or not cliente.activo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cliente con ID {pedido_in.cliente_id} no encontrado o está inactivo.")

    if not cliente.tipo_cliente_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El cliente '{cliente.nombre_comercial}' no tiene un tipo de cliente asignado. No se pueden calcular los precios.")

    # --- 2. PROCESAMIENTO DE ITEMS Y CÁLCULO DE PRECIOS SEGURO ---
    items_para_la_bd = []
    subtotal_calculado = Decimal('0.0')
    descuento_total_calculado = Decimal('0.0')
    total_calculado = Decimal('0.0')
    
    # Importamos los modelos de producto aquí para claridad
    from app.models.product_models import ProductoModel, PrecioModel

    for item_recibido in pedido_in.items:
        producto = db.query(ProductoModel).filter(ProductoModel.id == item_recibido.producto_id).first()
        if not producto or not producto.activo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Producto con ID {item_recibido.producto_id} no encontrado o está inactivo.")

        # --- Lógica de Precios ---
        # Determina qué tarifa de precios usar: la del item si viene, o la del cliente por defecto.
        tipo_cliente_para_precio_id = item_recibido.override_tipo_cliente_id or cliente.tipo_cliente_id
        
        # Busca el precio específico en la tabla `precios`
        precio_db = db.query(PrecioModel).filter(
            PrecioModel.producto_id == producto.id,
            PrecioModel.tipo_cliente_id == tipo_cliente_para_precio_id
        ).first()

        if not precio_db:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No se encontró un precio definido para el producto '{producto.nombre}' y la tarifa de precios seleccionada.")
        
        # El precio unitario final lo define el backend, no el frontend.
        precio_unitario_final = precio_db.precio
        
        # Aquí puedes añadir tu lógica de descuento por volumen que tienes en PrecioClienteBase
        descuento_aplicado = Decimal('0.0') # Por ahora lo dejamos en 0

        # Crea el objeto del modelo PedidoItemModel
        item_bd = PedidoItemModel(
            producto_id=item_recibido.producto_id,
            cantidad=item_recibido.cantidad,
            precio_unitario=precio_unitario_final,
            descuento_aplicado=descuento_aplicado
        )
        # Usa tu propio método para calcular los totales del item
        item_bd.calcular_totales()
        items_para_la_bd.append(item_bd)
        
        # Acumula los totales del pedido
        total_calculado += Decimal(item_bd.total)
        subtotal_calculado += Decimal(item_bd.subtotal)
        descuento_total_calculado += Decimal(item_bd.descuento_monto)

    # --- 3. CREACIÓN DEL OBJETO PEDIDO ---
    from app.models.order_models import PedidoModel # Importación local

    now = datetime.now()
    nuevo_pedido_db = PedidoModel(
        # Usamos tu modelo PedidoModel de order_models.py
        numero_pedido=generar_numero_pedido_diario(db),
        fecha=now.date(),
        hora=now.time(),
        vendedor_id=current_vendedor.vendedor_id,
        cliente_id=cliente.id,
        tipo_venta=pedido_in.tipo_venta,
        tipo_pago=pedido_in.tipo_pago,
        latitud_pedido=pedido_in.latitud_pedido,
        longitud_pedido=pedido_in.longitud_pedido,
        observaciones=pedido_in.observaciones,
        subtotal=subtotal_calculado,
        descuento_total=descuento_total_calculado,
        total=total_calculado,
        items=items_para_la_bd
    )
    
    # --- 4. PERSISTENCIA EN LA BASE DE DATOS ---
    try:
        db.add(nuevo_pedido_db)
        db.commit()
        db.refresh(nuevo_pedido_db)
    except Exception as e:
        db.rollback()
        # En producción, loggear el error `e`
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al guardar el pedido en la base de datos: {str(e)}")

    # --- 5. ACCIONES POST-CREACIÓN (Notificaciones) ---
    # Ahora que el pedido está creado y tiene un ID, podemos notificar
    # (Esto se podría mover a una tarea en segundo plano en el futuro)
    try:
        # Preparamos los datos para la notificación del KDS del evaluador
        kds_data = KDSPedido(
            pedido_id=nuevo_pedido_db.id,
            numero_pedido=nuevo_pedido_db.numero_pedido,
            fecha=nuevo_pedido_db.fecha,
            hora=nuevo_pedido_db.hora,
            vendedor_nombre=f"{current_vendedor.nombre} {current_vendedor.apellidos}",
            vendedor_dni=current_vendedor.dni,
            cliente_nombre=cliente.nombre_comercial,
            cliente_ruc=cliente.ruc,
            tipo_cliente=cliente.tipo_cliente.nombre if cliente.tipo_cliente else "N/A",
            total=nuevo_pedido_db.total,
            tiempo_espera=0, # Acaba de ser creado
            prioridad=nuevo_pedido_db.prioridad,
            items_resumen=nuevo_pedido_db.items_resumen,
            observaciones=nuevo_pedido_db.observaciones,
            tipo_venta=nuevo_pedido_db.tipo_venta,
            credito_disponible=cliente.credito_disponible
        )
        
        # Usamos tu ConnectionManager para notificar a todos los evaluadores
        await manager.broadcast_to_role("evaluador", {
            "type": "pedido_nuevo",
            "data": kds_data.model_dump_json() # Usamos model_dump_json para Pydantic v2
        })
    except Exception as e:
        # Si la notificación falla, no deshacemos la creación del pedido,
        # pero sí es importante registrar el error.
        print(f"ALERTA: El pedido {nuevo_pedido_db.numero_pedido} se creó, pero falló la notificación por WebSocket: {str(e)}")

    # --- 6. RESPUESTA EXITOSA ---
    # Usamos tu schema de respuesta DataResponse para ser consistentes
    return DataResponse(
        success=True,
        message="Pedido creado exitosamente",
        data={
            "pedido_id": nuevo_pedido_db.id,
            "numero_pedido": nuevo_pedido_db.numero_pedido,
            "estado": nuevo_pedido_db.estado,
            "total": float(nuevo_pedido_db.total)
        }
    )

@app.get("/api/pedidos", response_model=PaginatedResponse)
async def obtener_pedidos(
    filtros: FiltrosPedidos = Depends(),
    db: Session = Depends(get_db)
):
    """Obtener pedidos con filtros"""
    # Implementar consulta paginada con filtros
    return PaginatedResponse(
        success=True,
        data=[],
        total=0,
        page=filtros.page,
        size=filtros.size,
        pages=0
    )

# =============================================
# EVALUACIÓN DE CRÉDITOS
# =============================================

@app.get("/api/evaluacion/pendientes", response_model=List[KDSPedido])
async def obtener_pedidos_pendientes(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtener pedidos pendientes de evaluación para KDS"""
    user_data = verify_token(credentials.credentials)
    if not user_data or user_data["tipo"] not in ["evaluador", "supervisor"]:
        raise HTTPException(status_code=403, detail="Sin permisos")
    
    # Mock data
    return []

@app.put("/api/evaluacion/{pedido_id}", response_model=Response)
async def evaluar_pedido(
    pedido_id: str,
    evaluacion: CalificacionUpdate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Evaluar/aprobar/rechazar pedido"""
    try:
        user_data = verify_token(credentials.credentials)
        if not user_data or user_data["tipo"] not in ["evaluador", "supervisor"]:
            raise HTTPException(status_code=403, detail="Sin permisos")
        
        # Actualizar calificación
        # Notificar al vendedor
        await manager.notify_vendedor(user_data["id"], {
            "type": "pedido_evaluado",
            "data": {
                "pedido_id": pedido_id,
                "estado": evaluacion.estado,
                "monto_aprobado": str(evaluacion.monto_aprobado or 0)
            }
        })
        
        return Response(
            success=True,
            message="Pedido evaluado correctamente"
        )
        
    except Exception as e:
        return Response(
            success=False,
            message=f"Error al evaluar pedido: {str(e)}"
        )

# =============================================
# DASHBOARD Y MÉTRICAS
# =============================================

@app.get("/api/dashboard/metricas", response_model=DashboardMetricas)
async def obtener_metricas_dashboard(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtener métricas para dashboard"""
    user_data = verify_token(credentials.credentials)
    if not user_data:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Consultar vista de métricas
    # SELECT * FROM v_dashboard_metricas
    
    return DashboardMetricas(
        pedidos_hoy=15,
        pedidos_ayer=12,
        ventas_hoy=15420.50,
        ventas_ayer=13280.30,
        evaluaciones_pendientes=3,
        aprobaciones_hoy=8,
        rechazos_hoy=1,
        vendedores_activos_hoy=5,
        productos_stock_bajo=7
    )

@app.get("/api/dashboard/ranking-vendedores", response_model=List[RankingVendedor])
async def obtener_ranking_vendedores(
    dias: int = 7,
    db: Session = Depends(get_db)
):
    """Ranking de vendedores por período"""
    # Mock data
    return []

# =============================================
# MENSAJERÍA Y NOTIFICACIONES
# =============================================

@app.post("/api/mensajes", response_model=Response)
async def enviar_mensaje(
    mensaje: dict, #MensajeCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Enviar mensaje push"""
    # Crear mensaje en BD
    # Enviar via WebSocket
    await manager.send_notification(
        mensaje.destinatario_id,
        mensaje.destinatario_tipo,
        {
            "titulo": mensaje.titulo,
            "contenido": mensaje.contenido,
            "tipo": mensaje.tipo_mensaje
        }
    )
    
    return Response(success=True, message="Mensaje enviado")

@app.get("/api/mensajes/no-leidos", response_model=List[Mensaje])
async def obtener_mensajes_no_leidos(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Obtener mensajes no leídos del usuario"""
    user_data = verify_token(credentials.credentials)
    # Consultar mensajes no leídos
    return []

# =============================================
# CHAT DE VOZ
# =============================================

@app.post("/api/chat-voz/iniciar", response_model=Response)
async def iniciar_conversacion_voz(
    conversacion: ConversacionVozCreate,
    db: Session = Depends(get_db)
):
    """Iniciar conversación de voz"""
    # Crear registro de conversación
    return Response(success=True, message="Conversación iniciada")

@app.post("/api/chat-voz/transcribir", response_model=Response)
async def agregar_transcripcion(
    transcripcion: TranscripcionCreate,
    db: Session = Depends(get_db)
):
    """Agregar transcripción de audio"""
    # Guardar transcripción
    return Response(success=True, message="Transcripción guardada")

# =============================================
# WEBSOCKETS
# =============================================

@app.websocket("/ws/{user_type}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_type: str,
    user_id: int
):
    """WebSocket para notificaciones en tiempo real"""
    await manager.connect(websocket, user_id, user_type)
    try:
        while True:
            # Mantener conexión viva
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
            
    except WebSocketDisconnect:
        manager.disconnect(user_id, user_type)

# =============================================
# RUTAS DE TEMPLATES (FRONTEND)
# =============================================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Página de inicio/login"""
    return templates.TemplateResponse("login.html", {"request": {}})

@app.get("/ventas/externas/{vendedor_id}", response_class=HTMLResponse)
async def ventas_externas(vendedor_id: int):
    """PWA para vendedores externos"""
    return templates.TemplateResponse("vendedor_externo.html", {
        "request": {},
        "vendedor_id": vendedor_id
    })

@app.get("/ventas/internas/{vendedor_id}", response_class=HTMLResponse)
async def ventas_internas(vendedor_id: int):
    """App para vendedores internos"""
    return templates.TemplateResponse("vendedor_interno.html", {
        "request": {},
        "vendedor_id": vendedor_id
    })

@app.get("/evaluacion/dashboard/{evaluador_id}", response_class=HTMLResponse)
async def dashboard_evaluador(evaluador_id: int):
    """Dashboard KDS para evaluadores"""
    return templates.TemplateResponse("evaluador_kds.html", {
        "request": {},
        "evaluador_id": evaluador_id
    })

"""
@app.get("/supervisor/dashboard/{supervisor_id}", response_class=HTMLResponse)
async def dashboard_supervisor(supervisor_id: int):
    ""Dashboard para supervisores""
    return templates.TemplateResponse("supervisor/supervisor.html", {
        "request": {},
        "supervisor_id": supervisor_id
    })
"""
@app.get("/ventas/clientes/{cliente_id}", response_class=HTMLResponse)
async def portal_cliente(cliente_id: int):
    """Portal para clientes/bodegueros"""
    return templates.TemplateResponse("cliente_portal.html", {
        "request": {},
        "cliente_id": cliente_id
    })

@app.get("/ceo/dashboard", response_class=HTMLResponse)
async def dashboard_ceo():
    """Dashboard ejecutivo para CEO"""
    return templates.TemplateResponse("ceo_dashboard.html", {"request": {}})

# =============================================
# SALUD Y MONITOREO
# =============================================

@app.get("/health")
async def health_check():
    """Health check para monitoreo"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/system/stats")
async def system_stats(db: Session = Depends(get_db)):
    """Estadísticas del sistema"""
    return {
        "conexiones_activas": len(manager.active_connections),
        "pedidos_pendientes": 0,  # Consultar BD
        "usuarios_online": 0,     # Consultar sesiones activas
        "uptime": "24h 15m"
    }


# AGREGAR ESTOS ENDPOINTS AL MAIN.PY

# =============================================
# ENDPOINTS PARA DASHBOARD VENDEDOR
# =============================================

@app.get("/vendedor/dashboard/{vendedor_id}", response_class=HTMLResponse)
async def vendedor_dashboard(request: Request, vendedor_id: int):
    """Dashboard principal del vendedor"""
    return templates.TemplateResponse("vendedor/dashboard.html", {"request": request})

@app.get("/api/vendedor/estadisticas")
async def get_vendedor_estadisticas(
    current_vendedor: VendedorModel = Depends(get_current_vendedor),
    db: Session = Depends(get_db)
):
    """Obtiene estadísticas del vendedor para el dashboard"""
    
    print(f"=== ENDPOINT estadísticas ===")
    print(f"Vendedor: {current_vendedor.vendedor_id} - {current_vendedor.nombre}")
    
    try:
        from datetime import date
        
        hoy = date.today()
        vendedor_id = current_vendedor.vendedor_id
        
        # Estadísticas del día actual
        estadisticas = {
            "pedidos_hoy": 5,  # Simulado
            "ventas_hoy": 1250.50,  # Simulado
            "clientes_atendidos": 8,  # Simulado
            "pedidos_pendientes": 2  # Simulado
        }
        
        print(f"✅ Estadísticas generadas: {estadisticas}")
        
        return DataResponse[Dict](
            success=True,
            message="Estadísticas obtenidas",
            data=estadisticas
        )
        
    except Exception as e:
        print(f"❌ Error en estadísticas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vendedor/pedidos-recientes")
async def get_pedidos_recientes(
    request: Request,  # Agregar esto para debug
    current_vendedor: VendedorModel = Depends(get_current_vendedor),
    db: Session = Depends(get_db)
):
    """Obtiene pedidos recientes del vendedor"""
    # DEBUG: Imprimir headers
    print("=== DEBUG PEDIDOS RECIENTES ===")
    print(f"Headers: {dict(request.headers)}")
    print(f"Authorization header: {request.headers.get('authorization', 'NO EXISTE')}")
    print(f"Current vendedor: {current_vendedor}")
    print("===============================")
    try:
        # Por ahora devuelvo datos simulados
        pedidos = [
            {
                "pedido_id": 1,
                "numero_pedido": "PED-001",
                "cliente_nombre": "Bodega San Martin",
                "total": 450.00,
                "estado": "confirmado",
                "fecha": "2025-01-15T10:30:00"
            },
            {
                "pedido_id": 2,
                "numero_pedido": "PED-002", 
                "cliente_nombre": "Minimarket Los Andes",
                "total": 780.50,
                "estado": "pendiente",
                "fecha": "2025-01-15T14:15:00"
            }
        ]
        
        return DataResponse[List](
            success=True,
            message="Pedidos obtenidos",
            data=pedidos
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# ENDPOINTS PARA PROCESAMIENTO INTELIGENTE DE PEDIDOS
# =============================================

class ProcesarPedidoRequest(BaseModel):
    texto: str
    audio_url: Optional[str] = None
    es_voz: bool = False

class ProductoIdentificado(BaseModel):
    producto_id: int
    nombre: str
    codigo_producto: str
    cantidad: int
    unidad: str
    precio_unitario: float
    subtotal: float
    variantes: List[str] = []
    confianza: float = 0.95  # Nivel de confianza en la identificacion

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import re
from typing import List

router = APIRouter()


@app.post("/api/pedidos/procesar-texto-google")
async def procesar_texto_google(
    audio_file: UploadFile = File(...),
    current_vendedor: VendedorModel = Depends(get_current_vendedor),
    db: Session = Depends(get_db)
):
    """
    Procesa un archivo de audio usando la API de Google Speech-to-Text
    y luego lo pasa al motor de procesamiento de pedidos.
    """
    print(f"=== INICIO PROCESAR TEXTO (Motor Google) ===")
    
    # --- 1. INICIALIZACIÓN EXPLÍCITA DE CREDENCIALES ---
    try:
        if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
            print(f"ERROR CRÍTICO: El archivo de credenciales no existe en {GOOGLE_CREDENTIALS_PATH}")
            raise HTTPException(status_code=500, detail="Error de configuración del servidor: no se encuentran las credenciales de Google.")

        credentials = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH)
        client = speech.SpeechClient(credentials=credentials)
        print("Cliente de Google Speech inicializado con credenciales explícitas.")
    except Exception as e:
        print(f"Error al inicializar el cliente de Google con las credenciales: {e}")
        raise HTTPException(status_code=500, detail=f"Error de configuración de credenciales de Google: {e}")

    # --- 2. LECTURA DE AUDIO Y LLAMADA A LA API DE GOOGLE ---
    content = await audio_file.read()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        sample_rate_hertz=48000,
        language_code="es-PE",
        speech_contexts=[speech.SpeechContext(
            phrases=["cajas", "docenas", "inca kola", "leche gloria", "jabón camay"],
            boost=15.0
        )]
    )
    
    try:
        print("Enviando audio a Google API...")
        response = client.recognize(config=config, audio=audio)
        print("Respuesta de Google recibida.")
        
        if not response.results or not response.results[0].alternatives:
            raise HTTPException(status_code=400, detail="Google API no pudo transcribir el audio.")
            
        texto_transcrito = response.results[0].alternatives[0].transcript
        print(f"Texto Transcrito por Google: '{texto_transcrito}'")

    except Exception as e:
        print(f"Error con Google API: {e}")
        raise HTTPException(status_code=500, detail=f"Error al comunicarse con la API de Google: {e}")

    # --- 3. REUTILIZACIÓN DEL MOTOR DE PROCESAMIENTO INTERNO ---
    texto_normalizado = normalizar_texto_pedido(texto_transcrito)
    print(f"Texto Normalizado: '{texto_normalizado}'")
    
    items_texto = [item.strip() for item in texto_normalizado.split(',') if item.strip()]
    productos_detectados: List[ProductoDetectado] = []
    
    # --- Lógica de procesamiento de productos (idéntica a la del otro endpoint) ---
    patrones = [
        re.compile(r"^(?P<cantidad>\d+(?:\.\d+)?)\s*(?P<unidad>cajas?|docenas?|unidades?|litros?|kilos?|kg|paquetes?|bolsas?)\s*(?P<producto>.+)", re.IGNORECASE),
        re.compile(r"^(?P<cantidad>\d+(?:\.\d+)?)\s*(?P<producto>.+)", re.IGNORECASE),
        re.compile(r"^(?P<producto>[a-zA-Z\s\d./-]+)$", re.IGNORECASE)
    ]

    for texto_item in items_texto:
        match_encontrado = None
        for patron in patrones:
            match = patron.match(texto_item)
            if match:
                match_encontrado = match
                break
        
        if match_encontrado:
            partes = match_encontrado.groupdict()
            cantidad = float(partes.get("cantidad", 1.0))
            unidad = (partes.get("unidad") or "unidades").lower()
            producto_texto = partes.get("producto", "").strip()

            palabras_busqueda = [palabra for palabra in producto_texto.split() if len(palabra) > 1]
            if not palabras_busqueda:
                continue

            producto_query = db.query(ProductoModel).filter(
                ProductoModel.activo == True,
                or_(*[ProductoModel.nombre.ilike(f"%{palabra}%") for palabra in palabras_busqueda])
            ).first()

            if producto_query:
                producto_detectado = ProductoDetectado(
                    producto_id=producto_query.id,
                    nombre=producto_query.nombre,
                    cantidad=cantidad,
                    unidad=unidad.rstrip('s'),
                    precio_unitario=float(producto_query.precio_unitario),
                    precio_total=float(producto_query.precio_unitario) * cantidad,
                    encontrado=True
                )
                productos_detectados.append(producto_detectado)
            else:
                producto_detectado = ProductoDetectado(
                    nombre=producto_texto,
                    cantidad=cantidad,
                    unidad=unidad,
                    encontrado=False
                )
                productos_detectados.append(producto_detectado)

    # --- 4. RESPUESTA FINAL ---
    return DataResponse[List[ProductoDetectado]](
        success=True,
        message=f"Google transcribió: '{texto_transcrito}'",
        data=productos_detectados
    )


async def identificar_productos_en_texto(db: Session, texto: str) -> List[ProductoIdentificado]:
    """
    Algoritmo para identificar productos en texto natural
    """
    from app.models.product_models import ProductoModel
    import re
    
    # Patrones para extraer cantidades y unidades
    patron_cantidad = r'(\d+)\s*(cajas?|docenas?|unidades?|kg|kilos?|litros?|ml|piezas?)?'
    
    # Palabras clave de productos conocidos
    productos_conocidos = {
        'coca cola': ['coca', 'cola'],
        'sprite': ['sprite'],
        'jabon': ['jabon', 'jabón'],
        'leche': ['leche'],
        'arroz': ['arroz'],
        'aceite': ['aceite'],
        'detergente': ['detergente']
    }
    
    productos_identificados = []
    
    # Buscar productos en la base de datos que coincidan
    productos_bd = db.query(ProductoModel).filter(ProductoModel.activo == True).all()
    
    # Algoritmo simple de matching
    for producto in productos_bd:
        nombre_producto = producto.nombre.lower()
        
        # Verificar si el nombre del producto aparece en el texto
        for palabra_clave in productos_conocidos.keys():
            if palabra_clave in texto and palabra_clave in nombre_producto:
                # Extraer cantidad del contexto
                matches = re.findall(patron_cantidad, texto)
                cantidad = 1
                unidad = 'unidad'
                
                if matches:
                    cantidad = int(matches[0][0]) if matches[0][0] else 1
                    unidad = matches[0][1] if matches[0][1] else 'unidad'
                
                # Mapear unidades
                if unidad in ['cajas', 'caja']:
                    cantidad = cantidad * 12  # Asumiendo 12 unidades por caja
                    unidad = 'unidad'
                elif unidad in ['docenas', 'docena']:
                    cantidad = cantidad * 12
                    unidad = 'unidad'
                
                productos_identificados.append(ProductoIdentificado(
                    producto_id=producto.producto_id,
                    nombre=producto.nombre,
                    codigo_producto=producto.codigo_producto,
                    cantidad=cantidad,
                    unidad=unidad,
                    precio_unitario=float(producto.precio_unitario),
                    subtotal=float(producto.precio_unitario * cantidad),
                    variantes=[f"{producto.unidad_medida}"],
                    confianza=0.85
                ))
                break
    
    return productos_identificados

# =============================================
# ENDPOINTS PARA BÚSQUEDA Y GESTIÓN DE CLIENTES
# =============================================
class BuscarClienteVozRequest(BaseModel):
    texto: str
    es_voz: bool = False


@app.get("/api/productos/buscar")
async def buscar_productos(
    q: str,
    tipo_cliente_id: Optional[int] = None,  # ✅ Acepta None o vacío
    current_vendedor: VendedorModel = Depends(get_current_vendedor),
    db: Session = Depends(get_db)
):
    """Endpoint para búsqueda de productos por nombre o código"""
    try:
        print(f"🔍 Buscando productos con: '{q}', tipo_cliente_id: {tipo_cliente_id}")
        
        # Query sin join con categoría
        productos = db.query(ProductoModel).filter(
            and_(
                ProductoModel.activo == True,
                or_(
                    ProductoModel.nombre.ilike(f"%{q}%"),
                    ProductoModel.codigo_producto.ilike(f"%{q}%")
                )
            )
        ).limit(20).all()
        
        print(f"📦 Encontrados: {len(productos)} productos")
        
        productos_data = []
        for producto in productos:
            # Manejo seguro de categoría
            categoria_nombre = None
            if producto.categoria_id:
                try:
                    categoria = db.query(CategoriaModel).filter(
                        CategoriaModel.categoria_id == producto.categoria_id
                    ).first()
                    categoria_nombre = categoria.nombre if categoria else None
                except Exception as e:
                    print(f"Error obteniendo categoría: {e}")
            
            # ✅ NUEVO: Obtener precio según tipo de cliente
            precio_mostrar = float(producto.precio_unitario)  # Precio por defecto
            
            if tipo_cliente_id:
                try:
                    # Buscar precio crédito (por defecto)
                    precio_query = db.execute(
                        text("""
                            SELECT precio 
                            FROM precios_cliente 
                            WHERE producto_id = :pid 
                              AND tipo_cliente_id = :tid
                              AND tipo_pago = 'credito'
                              AND activo = true
                            LIMIT 1
                        """),
                        {"pid": producto.id, "tid": tipo_cliente_id}
                    ).first()
                    
                    if precio_query:
                        precio_mostrar = float(precio_query[0])
                        print(f"   ✅ Precio para tipo {tipo_cliente_id}: S/ {precio_mostrar}")
                    else:
                        print(f"   ⚠️ Sin precio específico para tipo {tipo_cliente_id}, usando precio base")
                        
                except Exception as e:
                    print(f"   ❌ Error obteniendo precio específico: {e}")
            
            productos_data.append({
                "id": producto.id,
                "codigo_producto": producto.codigo_producto,
                "nombre": producto.nombre,
                "precio_unitario": precio_mostrar,
                "categoria": categoria_nombre,
                "stock_disponible": producto.stock_disponible if hasattr(producto, 'stock_disponible') else 0  # ✅ NUEVO
            })
        
        return DataResponse(
            success=True,
            message=f"Se encontraron {len(productos_data)} producto(s)",
            data=productos_data
        )
        
    except Exception as e:
        print(f"❌ Error en búsqueda de productos: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint para obtener detalles de un producto específico
@app.get("/api/productos/{producto_id}")
async def get_producto_detalle(
    producto_id: int,
    current_vendedor: VendedorModel = Depends(get_current_vendedor),
    db: Session = Depends(get_db)
):
    """Obtiene detalles completos de un producto"""
    try:
        # BÚSQUEDA ACTUALIZADA
        producto = db.query(ProductoModel).filter(
            and_(
                ProductoModel.id == producto_id,
                ProductoModel.activo == True
            )
        ).first()
        
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        # CAMPOS ACTUALIZADOS según tu estructura
        producto_data = {
            "producto_id": producto.id,  # TU CAMPO CORRECTO
            "nombre": producto.nombre,
            "descripcion": producto.descripcion,
            "codigo": producto.codigo,
            "precio_venta": float(producto.precio_base),  # TU CAMPO CORRECTO
            "precio_compra": None,  # Tu modelo no tiene este campo
            "stock": producto.stock_actual,  # TU CAMPO CORRECTO
            "unidad_medida": producto.unidad_medida.nombre if producto.unidad_medida else None,
            "categoria": producto.categoria.nombre if producto.categoria else None,
            "activo": producto.activo,
            "fecha_creacion": producto.created_at.isoformat() if producto.created_at else None,
            "estado_stock": producto.estado_stock,  # Tu propiedad personalizada
            "stock_disponible": producto.stock_disponible  # Tu propiedad personalizada
        }
        
        return DataResponse[Dict](
            success=True,
            message="Producto encontrado",
            data=producto_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clientes/buscar-por-voz")
async def buscar_cliente_por_voz(
    request: BuscarClienteVozRequest,
    current_vendedor: VendedorModel = Depends(get_current_vendedor),
    db: Session = Depends(get_db)
):
    """
    Busca clientes procesando texto natural o voz
    Ejemplo: 'bodega san martin lima', 'ruc 20123456789'
    """
    try:
        texto = request.texto.lower().strip()
        
        # Extraer información del texto
        info_extraida = extraer_info_cliente_de_texto(texto)
        
        from app.models.client_models import ClienteModel
        query = db.query(ClienteModel).filter(ClienteModel.activo == True)
        
        # Aplicar filtros basados en la información extraída
        if info_extraida.get('ruc'):
            query = query.filter(ClienteModel.ruc.ilike(f"%{info_extraida['ruc']}%"))
        
        if info_extraida.get('nombre'):
            nombre_termino = f"%{info_extraida['nombre']}%"
            query = query.filter(
                or_(
                    ClienteModel.nombre_comercial.ilike(nombre_termino),
                    ClienteModel.razon_social.ilike(nombre_termino)
                )
            )
        
        if info_extraida.get('ubicacion'):
            ubicacion_termino = f"%{info_extraida['ubicacion']}%"
            query = query.filter(
                or_(
                    ClienteModel.distrito.ilike(ubicacion_termino),
                    ClienteModel.provincia.ilike(ubicacion_termino)
                )
            )
        
        clientes = query.limit(5).all()
        
        resultados = [
            {
                "cliente_id": c.cliente_id,
                "nombre_comercial": c.nombre_comercial,
                "razon_social": c.razon_social,
                "ruc": c.ruc,
                "telefono": c.telefono,
                "distrito": c.distrito,
                "direccion_completa": c.direccion_completa,
                "tipo_cliente": c.tipo_cliente
            }
            for c in clientes
        ]
        
        return DataResponse[List](
            success=True,
            message=f"Encontrados {len(resultados)} clientes",
            data=resultados
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def extraer_info_cliente_de_texto(texto: str) -> Dict[str, str]:
    """Extrae información de cliente del texto natural"""
    import re
    
    info = {}
    
    # Extraer RUC (11 dígitos)
    ruc_match = re.search(r'\b(\d{11})\b', texto)
    if ruc_match:
        info['ruc'] = ruc_match.group(1)
    
    # Extraer posibles nombres (palabras después de 'bodega', 'minimarket', etc.)
    nombre_patterns = [
        r'bodega\s+([a-zA-Z\s]+)',
        r'minimarket\s+([a-zA-Z\s]+)',
        r'market\s+([a-zA-Z\s]+)'
    ]
    
    for pattern in nombre_patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            info['nombre'] = match.group(1).strip()
            break
    
    # Si no encuentra patrón específico, tomar las primeras palabras
    if 'nombre' not in info:
        palabras = texto.split()
        if len(palabras) >= 2:
            info['nombre'] = ' '.join(palabras[:3])
    
    # Detectar ubicaciones comunes
    distritos_conocidos = ['lima', 'san juan', 'villa', 'los olivos', 'ate', 'surco']
    for distrito in distritos_conocidos:
        if distrito in texto:
            info['ubicacion'] = distrito
            break
    
    return info

# =============================================
# ENDPOINTS PARA CONFIRMACIÓN DE PEDIDOS
# =============================================

class ConfirmarPedidoRequest(BaseModel):
    productos: List[Dict[str, Any]]
    cliente_id: int
    modalidad_pago: str = "credito_15_dias"
    plazo_pago: int = 15
    observaciones: Optional[str] = None
    coordenadas: Optional[Dict[str, float]] = None

@app.post("/api/pedidos/confirmar")
async def confirmar_pedido(
    request: ConfirmarPedidoRequest,
    current_vendedor: VendedorModel = Depends(get_current_vendedor),
    db: Session = Depends(get_db)
):
    """
    Confirma y envía pedido a supervisores/analistas de crédito
    """
    try:
        # Calcular totales
        subtotal = sum(item['subtotal'] for item in request.productos)
        total = subtotal  # Agregar impuestos si es necesario
        
        # Crear pedido (simulado por ahora)
        pedido_data = {
            "vendedor_id": current_vendedor.vendedor_id,
            "cliente_id": request.cliente_id,
            "productos": request.productos,
            "subtotal": subtotal,
            "total": total,
            "modalidad_pago": request.modalidad_pago,
            "plazo_pago": request.plazo_pago,
            "estado": "pendiente_aprobacion",
            "observaciones": request.observaciones,
            "fecha_pedido": get_utc_now,
            "coordenadas": request.coordenadas
        }
        
        # Generar número de pedido
        numero_pedido = f"PED-{datetime.now().strftime('%Y%m%d')}-{current_vendedor.vendedor_id:03d}-{int(datetime.now().timestamp()) % 1000:03d}"
        
        # Notificar a evaluadores/supervisores vía WebSocket
        notificacion_data = {
            "type": "pedido_nuevo",
            "pedido_id": numero_pedido,
            "vendedor_nombre": current_vendedor.nombre_completo,
            "cliente_id": request.cliente_id,
            "total": total,
            "productos_count": len(request.productos),
            "modalidad_pago": request.modalidad_pago,
            "timestamp": get_utc_now.isoformat()
        }
        
        # Enviar notificación (implementar manager.notify_evaluadores)
        # await manager.notify_evaluadores(notificacion_data)
        
        return DataResponse[Dict](
            success=True,
            message="Pedido enviado para aprobación",
            data={
                "numero_pedido": numero_pedido,
                "estado": "pendiente_aprobacion",
                "total": total,
                "fecha_envio": get_utc_now.isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# ENDPOINTS PARA MODALIDADES DE PAGO
# =============================================

@app.get("/api/modalidades-pago")
async def get_modalidades_pago():
    """Obtiene las modalidades de pago disponibles"""
    modalidades = [
        {"codigo": "efectivo_cash", "nombre": "Efectivo - CASH", "plazo": 0},
        {"codigo": "efectivo_yape", "nombre": "Efectivo - Yape", "plazo": 0},
        {"codigo": "efectivo_plin", "nombre": "Efectivo - Plin", "plazo": 0},
        {"codigo": "credito_15_dias", "nombre": "Crédito 15 días", "plazo": 15},
        {"codigo": "credito_30_dias", "nombre": "Crédito 30 días", "plazo": 30},
        {"codigo": "credito_45_dias", "nombre": "Crédito 45 días", "plazo": 45}
    ]
    
    return DataResponse[List](
        success=True,
        message="Modalidades de pago obtenidas",
        data=modalidades
    )

# =============================================
# IMPORTS ADICIONALES NECESARIOS
# =============================================

# Agregar estos imports al inicio del archivo main.py:

# Función temporal para probar sin autenticación (SOLO PARA DEBUG)
@app.get("/api/vendedor/estadisticas-debug")
async def get_vendedor_estadisticas_debug():
    """Estadísticas sin autenticación - SOLO PARA DEBUG"""
    return {
        "success": True,
        "message": "Debug OK",
        "data": {
            "pedidos_hoy": 5,
            "ventas_hoy": 1250.50,
            "clientes_atendidos": 8,
            "pedidos_pendientes": 2
        }
    }


#============================================ 💪👈🌟💲💰🤑👈🙏👍🚀✔=========================================
# Endpoints de API para el evaluador:
#============================================
# Agregar a main.py

# Agregar a main.py - Endpoints para todos los dashboards

from datetime import datetime, timedelta, date
from typing import Optional, Dict, List, Any
import json

# =============================================
# ENDPOINTS EVALUADOR
# =============================================

@app.get("/api/evaluador/perfil")
async def get_perfil_evaluador(
    current_evaluador: EvaluadorModel = Depends(get_current_evaluador),
    db: Session = Depends(get_db)
):
    """Obtiene perfil del evaluador"""
    try:
        return DataResponse[Dict](
            success=True,
            message="Perfil obtenido",
            data={
                "evaluador_id": current_evaluador.evaluador_id,
                "nombre": current_evaluador.nombre,
                "apellidos": current_evaluador.apellidos,
                "nombre_completo": f"{current_evaluador.nombre} {current_evaluador.apellidos}",
                "codigo_evaluador": current_evaluador.codigo_evaluador,
                "email": current_evaluador.email
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evaluador/limite-aprobacion")
async def get_limite_aprobacion_evaluador(
    current_evaluador: EvaluadorModel = Depends(get_current_evaluador),
    db: Session = Depends(get_db)
):
    """Obtiene límite de aprobación del evaluador"""
    try:
        # Por ahora valor simulado - debería venir de configuración
        limite = 5000.00
        
        return DataResponse[Dict](
            success=True,
            message="Límite obtenido",
            data={"limite": limite}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evaluador/pedidos-pendientes")
async def get_pedidos_pendientes(
    estado: str = "pendiente",
    current_evaluador: EvaluadorModel = Depends(get_current_evaluador),
    db: Session = Depends(get_db)
):
    """Obtiene pedidos pendientes de evaluación"""
    try:
        # Datos simulados por ahora
        pedidos = [
            {
                "id": 1,
                "numero_pedido": "PED-2025-001",
                "cliente": {
                    "id": 1,
                    "ruc": "20123456789",
                    "nombre_comercial": "Bodega Central",
                    "razon_social": "Comercial Central SAC",
                    "credito_usado": 2500.00,
                    "limite_credito": 10000.00
                },
                "vendedor": {
                    "id": 1,
                    "nombre": "Juan Pérez",
                    "nombre_completo": "Juan Pérez García"
                },
                "total": 3500.00,
                "estado": "pendiente",
                "modalidad_pago": "credito_30_dias",
                "plazo_pago": "30 días",
                "created_at": (datetime.now() - timedelta(minutes=45)).isoformat(),
                "items": [
                    {
                        "producto_nombre": "Coca Cola 500ml",
                        "cantidad": 24,
                        "precio_unitario": 2.50,
                        "subtotal": 60.00
                    }
                ]
            }
        ]
        
        return DataResponse[List](
            success=True,
            message=f"Se encontraron {len(pedidos)} pedidos",
            data=pedidos
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evaluador/pedido/{pedido_id}")
async def get_detalle_pedido(
    pedido_id: int,
    current_evaluador: EvaluadorModel = Depends(get_current_evaluador),
    db: Session = Depends(get_db)
):
    """Obtiene detalles completos de un pedido"""
    try:
        # Datos simulados
        pedido = {
            "id": pedido_id,
            "numero_pedido": f"PED-2025-{pedido_id:03d}",
            "cliente": {
                "id": 1,
                "ruc": "20123456789",
                "nombre_comercial": "Bodega Central",
                "razon_social": "Comercial Central SAC",
                "direccion": "Av. Principal 123, Lima",
                "telefono": "987654321",
                "tipo_cliente": {"nombre": "Bodega Barrio"}
            },
            "vendedor": {
                "id": 1,
                "nombre_completo": "Juan Pérez García"
            },
            "total": 3500.00,
            "modalidad_pago": "credito_30_dias",
            "created_at": datetime.now().isoformat(),
            "items": [
                {
                    "producto_nombre": "Coca Cola 500ml",
                    "cantidad": 24,
                    "precio_unitario": 2.50,
                    "subtotal": 60.00
                }
            ]
        }
        
        return DataResponse[Dict](
            success=True,
            message="Pedido encontrado",
            data=pedido
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evaluador/historial-cliente/{cliente_id}")
async def get_historial_cliente(
    cliente_id: int,
    current_evaluador: EvaluadorModel = Depends(get_current_evaluador),
    db: Session = Depends(get_db)
):
    """Obtiene historial crediticio del cliente"""
    try:
        historial = {
            "limite_credito": 10000.00,
            "credito_usado": 2500.00,
            "credito_disponible": 7500.00,
            "compras_ultimos_30_dias": 5,
            "promedio_dias_pago": 28,
            "historial_pagos": [
                {"fecha": "2025-01-10", "monto": 1500.00, "estado": "pagado"},
                {"fecha": "2025-01-05", "monto": 2000.00, "estado": "pagado"}
            ]
        }
        
        return DataResponse[Dict](
            success=True,
            message="Historial obtenido",
            data=historial
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/evaluador/evaluar-pedido")
async def evaluar_pedido(
    request: dict,
    current_evaluador: EvaluadorModel = Depends(get_current_evaluador),
    db: Session = Depends(get_db)
):
    """Evalúa un pedido (aprobar/rechazar/escalar)"""
    try:
        pedido_id = request.get("pedido_id")
        decision = request.get("decision")  # aprobado, rechazado, escalado
        monto_aprobado = request.get("monto_aprobado", 0)
        observaciones = request.get("observaciones", "")
        
        # Aquí iría la lógica de evaluación real
        # Por ahora solo simulamos la respuesta
        
        return DataResponse[Dict](
            success=True,
            message=f"Pedido {decision} exitosamente",
            data={
                "pedido_id": pedido_id,
                "decision": decision,
                "monto_aprobado": monto_aprobado,
                "evaluador_id": current_evaluador.evaluador_id
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# ENDPOINTS SUPERVISOR
# =============================================

@app.get("/api/supervisor/perfil")
async def get_perfil_supervisor(
    current_supervisor: SupervisorModel = Depends(get_current_supervisor),
    db: Session = Depends(get_db)
):
    """Obtiene perfil del supervisor"""
    try:
        return DataResponse[Dict](
            success=True,
            message="Perfil obtenido",
            data={
                "supervisor_id": current_supervisor.supervisor_id,
                "nombre": current_supervisor.nombre,
                "apellidos": current_supervisor.apellidos,
                "nombre_completo": f"{current_supervisor.nombre} {current_supervisor.apellidos}",
                "codigo_supervisor": current_supervisor.codigo_supervisor
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/supervisor/pedidos-escalados")
async def get_pedidos_escalados(
    prioridad: str = "todas",
    current_supervisor: SupervisorModel = Depends(get_current_supervisor),
    db: Session = Depends(get_db)
):
    """Obtiene pedidos escalados al supervisor"""
    try:
        # Datos simulados
        pedidos = [
            {
                "id": 1,
                "numero_pedido": "PED-2025-001",
                "cliente": {
                    "nombre_comercial": "Bodega Central",
                    "ruc": "20123456789"
                },
                "evaluador": {
                    "nombre_completo": "Ana López"
                },
                "total": 15000.00,
                "motivo_escalacion": "Monto superior al límite",
                "comentario_evaluador": "Cliente con buen historial pero monto alto",
                "fecha_escalacion": (datetime.now() - timedelta(hours=2)).isoformat()
            }
        ]
        
        return DataResponse[List](
            success=True,
            message=f"Se encontraron {len(pedidos)} pedidos escalados",
            data=pedidos
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/supervisor/politicas-credito")
async def get_politicas_credito(
    current_supervisor: SupervisorModel = Depends(get_current_supervisor),
    db: Session = Depends(get_db)
):
    """Obtiene políticas de crédito configuradas"""
    try:
        politicas = {
            "tipos_cliente": [
                {
                    "id": 1,
                    "nombre": "Bodega Barrio",
                    "limite_maximo": 10000.00,
                    "limite_defecto": 5000.00,
                    "dias_gracia": 5
                },
                {
                    "id": 2,
                    "nombre": "Mini Market",
                    "limite_maximo": 25000.00,
                    "limite_defecto": 15000.00,
                    "dias_gracia": 3
                }
            ],
            "limites_evaluadores": [
                {
                    "id": 1,
                    "nombre": "Ana",
                    "nombre_completo": "Ana López Méndez",
                    "codigo": "EVAL001",
                    "limite_aprobacion": 5000.00
                }
            ],
            "plazos_credito": [
                {"id": 1, "dias": 15, "descripcion": "Pago Quincenal", "activo": True},
                {"id": 2, "dias": 30, "descripcion": "Pago Mensual", "activo": True},
                {"id": 3, "dias": 45, "descripcion": "Pago Mes y Medio", "activo": False}
            ]
        }
        
        return DataResponse[Dict](
            success=True,
            message="Políticas obtenidas",
            data=politicas
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/supervisor/metricas")
async def get_metricas_supervisor(
    periodo: str = "mes",
    current_supervisor: SupervisorModel = Depends(get_current_supervisor),
    db: Session = Depends(get_db)
):
    """Obtiene métricas y KPIs del supervisor"""
    try:
        metricas = {
            "total_pedidos": 127,
            "tasa_aprobacion": 85.2,
            "tiempo_promedio": 25,  # minutos
            "monto_total": 450000.00,
            "ranking_vendedores": [
                {
                    "vendedor_id": 1,
                    "nombre_completo": "Juan Pérez García",
                    "pedidos": 15,
                    "aprobados": 13,
                    "tasa": 86.7,
                    "monto_total": 45000.00
                }
            ]
        }
        
        return DataResponse[Dict](
            success=True,
            message="Métricas obtenidas",
            data=metricas
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# ENDPOINTS CEO
# =============================================

@app.get("/api/ceo/datos-generales")
async def get_datos_generales_ceo(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene datos generales para el header del CEO"""
    try:
        datos = {
            "ventas_hoy": 25000.00,
            "pedidos_activos": 45,
            "vendedores_online": 8
        }
        
        return DataResponse[Dict](
            success=True,
            message="Datos generales obtenidos",
            data=datos
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ceo/resumen-ejecutivo")
async def get_resumen_ejecutivo(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene resumen ejecutivo principal"""
    try:
        resumen = {
            "ingresos_mes": 1250000.00,
            "cambio_ingresos": 12.5,
            "pedidos_mes": 384,
            "cambio_pedidos": 8.3,
            "clientes_activos": 156,
            "cambio_clientes": 15.2,
            "tasa_conversion": 78.5,
            "cambio_conversion": 3.1,
            
            "ventas_periodo": {
                "labels": ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
                "valores": [850000, 920000, 980000, 1100000, 1180000, 1250000]
            },
            
            "top_productos": {
                "labels": ["Coca Cola", "Agua", "Cerveza", "Snacks", "Otros"],
                "valores": [35, 25, 20, 15, 5]
            },
            
            "ranking_vendedores": [
                {
                    "vendedor_id": 1,
                    "nombre_completo": "Juan Pérez García",
                    "pedidos_mes": 28,
                    "ventas_mes": 85000.00
                },
                {
                    "vendedor_id": 2,
                    "nombre_completo": "María González",
                    "pedidos_mes": 25,
                    "ventas_mes": 72000.00
                }
            ],
            
            "alertas": [
                {
                    "tipo": "critical",
                    "titulo": "Stock Crítico",
                    "descripcion": "5 productos con stock por debajo del mínimo"
                },
                {
                    "tipo": "warning",
                    "titulo": "Pagos Vencidos",
                    "descripcion": "12 clientes con pagos vencidos por más de 15 días"
                },
                {
                    "tipo": "info",
                    "titulo": "Nuevos Clientes",
                    "descripcion": "8 nuevos clientes registrados esta semana"
                }
            ]
        }
        
        return DataResponse[Dict](
            success=True,
            message="Resumen ejecutivo obtenido",
            data=resumen
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ceo/analisis-ventas")
async def get_analisis_ventas(
    periodo: str = "30d",
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene análisis detallado de ventas"""
    try:
        analisis = {
            "tendencia": {
                "labels": ["Sem 1", "Sem 2", "Sem 3", "Sem 4"],
                "valores": [280000, 310000, 295000, 365000]
            },
            "categorias": {
                "labels": ["Bebidas", "Snacks", "Lácteos", "Limpieza", "Otros"],
                "valores": [45, 25, 15, 10, 5]
            },
            "ticket_promedio": 3250.00,
            "frecuencia_compra": 15,
            "valor_cliente_promedio": 8500.00
        }
        
        return DataResponse[Dict](
            success=True,
            message="Análisis de ventas obtenido",
            data=analisis
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ceo/gestion-personal")
async def get_gestion_personal(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene información de gestión de personal"""
    try:
        personal = {
            "vendedores": [
                {
                    "vendedor_id": 1,
                    "nombre": "Juan",
                    "nombre_completo": "Juan Pérez García",
                    "codigo_vendedor": "VEND001",
                    "online": True
                },
                {
                    "vendedor_id": 2,
                    "nombre": "María",
                    "nombre_completo": "María González López",
                    "codigo_vendedor": "VEND002",
                    "online": False
                }
            ],
            "evaluadores": [
                {
                    "evaluador_id": 1,
                    "nombre": "Ana",
                    "nombre_completo": "Ana López Méndez",
                    "codigo_evaluador": "EVAL001",
                    "online": True
                }
            ],
            "desempeno": {
                "labels": ["Vendedores", "Evaluadores", "Supervisores"],
                "valores": [85, 92, 88]
            }
        }
        
        return DataResponse[Dict](
            success=True,
            message="Gestión de personal obtenida",
            data=personal
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ceo/productos-stock")
async def get_productos_stock(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene información de productos y stock"""
    try:
        productos_data = {
            "alertas": {
                "critico": 5,
                "bajo": 12,
                "optimo": 180,
                "total": 197
            },
            "productos": [
                {
                    "id": 1,
                    "nombre": "Coca Cola 500ml",
                    "codigo_producto": "CC500",
                    "stock_actual": 45,
                    "stock_minimo": 50,
                    "precio_unitario": 2.50,
                    "estado_stock": "BAJO"
                },
                {
                    "id": 2,
                    "nombre": "Agua San Luis 625ml",
                    "codigo_producto": "ASL625",
                    "stock_actual": 120,
                    "stock_minimo": 100,
                    "precio_unitario": 1.80,
                    "estado_stock": "OPTIMO"
                }
            ]
        }
        
        return DataResponse[Dict](
            success=True,
            message="Productos y stock obtenidos",
            data=productos_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ceo/gestion-creditos")
async def get_gestion_creditos(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene información de gestión de créditos"""
    try:
        creditos = {
            "credito_total": 2500000.00,
            "credito_usado": 1850000.00,
            "credito_disponible": 650000.00,
            "credito_vencido": 125000.00,
            "tasa_morosidad": 6.8,
            
            "evolucion_morosidad": {
                "labels": ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
                "valores": [5.2, 4.8, 6.1, 7.3, 6.9, 6.8]
            }
        }
        
        return DataResponse[Dict](
            success=True,
            message="Gestión de créditos obtenida",
            data=creditos
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ceo/enviar-push")
async def enviar_notificacion_push(
    request: dict,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Envía notificación push a usuarios"""
    try:
        tipo_destinatario = request.get("tipo_destinatario")
        titulo = request.get("titulo")
        mensaje = request.get("mensaje")
        
        # Aquí iría la lógica real de envío de push notifications
        # Por ahora simulamos el envío
        
        destinatarios_map = {
            "todos": 45,
            "vendedores": 12,
            "evaluadores": 5,
            "supervisores": 3,
            "clientes": 25
        }
        
        destinatarios = destinatarios_map.get(tipo_destinatario, 0)
        
        return DataResponse[Dict](
            success=True,
            message="Notificación enviada exitosamente",
            data={
                "destinatarios": destinatarios,
                "tipo": tipo_destinatario,
                "titulo": titulo
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================
# DEPENDENCIES PARA AUTENTICACIÓN
# =============================================

async def get_current_evaluador(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> EvaluadorModel:
    """Dependency para obtener evaluador actual"""
    
    if current_user["tipo_usuario"] != "evaluador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso solo permitido para evaluadores"
        )
    
    evaluador = db.query(EvaluadorModel).filter(
        EvaluadorModel.evaluador_id == current_user["user_id"],
        EvaluadorModel.activo == True
    ).first()
    
    if not evaluador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluador no encontrado"
        )
    
    return evaluador

async def get_current_supervisor(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SupervisorModel:
    """Dependency para obtener supervisor actual"""
    
    if current_user["tipo_usuario"] != "supervisor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso solo permitido para supervisores"
        )
    
    supervisor = db.query(SupervisorModel).filter(
        SupervisorModel.supervisor_id == current_user["user_id"],
        SupervisorModel.activo == True
    ).first()
    
    if not supervisor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supervisor no encontrado"
        )
    
    return supervisor

# =============================================
# ENDPOINTS DE NAVEGACIÓN
# =============================================

@app.get("/evaluador/dashboard/{evaluador_id}", response_class=HTMLResponse)
async def evaluador_dashboard(request: Request, evaluador_id: int):
    return templates.TemplateResponse("evaluador/evaluador.html", {"request": request})

@app.get("/supervisor/dashboard/{supervisor_id}", response_class=HTMLResponse)
async def supervisor_dashboard(request: Request, supervisor_id: int):
    return templates.TemplateResponse("supervisor/supervisor.html", {"request": request})

@app.get("/ceo/dashboard", response_class=HTMLResponse)
async def ceo_dashboard(request: Request):
    return templates.TemplateResponse("ceo/ceo.html", {"request": request})
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)