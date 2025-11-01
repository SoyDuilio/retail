# app/routers/clientes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx
import os
from typing import Optional

from app.database import get_db
from app.models import ClienteModel, TipoClienteModel
from core.auth import get_current_user

router = APIRouter(prefix="/clientes", tags=["clientes"])

# Token de APIsPeru (desde variables de entorno)
APISPERU_TOKEN = os.getenv("APISPERU_TOKEN", "")

# ==========================================
# SCHEMAS
# ==========================================

class ValidarRUCRequest(BaseModel):
    ruc: str

class ValidarDNIRequest(BaseModel):
    dni: str

class CrearClienteRequest(BaseModel):
    ruc: str
    razon_social: str
    nombre_comercial: str
    direccion_completa: str
    referencia: Optional[str] = None
    distrito: str
    provincia: str
    departamento: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    precision_gps: Optional[float] = None
    tipo_cliente_id: int = 1
    contacto_nombre: Optional[str] = None
    contacto_dni: Optional[str] = None

# ==========================================
# ENDPOINTS CON /api/ EN LA RUTA
# ==========================================

@router.post("/api/clientes/validar-ruc")
async def validar_ruc(request: ValidarRUCRequest):
    """Valida RUC con APIsPeru"""
    ruc = request.ruc.strip()
    
    if not ruc.isdigit() or len(ruc) != 11:
        raise HTTPException(400, "RUC debe tener 11 dígitos")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"https://dniruc.apisperu.com/api/v1/ruc/{ruc}"
            params = {"token": APISPERU_TOKEN}
            
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") == False:
                    raise HTTPException(404, data.get("message", "RUC no encontrado"))
                
                return {
                    "success": True,
                    "data": {
                        "ruc": data.get("ruc"),
                        "razon_social": data.get("razonSocial"),
                        "nombre_comercial": data.get("nombreComercial", ""),
                        "estado": data.get("estado"),
                        "condicion": data.get("condicion"),
                        "direccion": data.get("direccion"),
                        "departamento": data.get("departamento"),
                        "provincia": data.get("provincia"),
                        "distrito": data.get("distrito"),
                        "ubigeo": data.get("ubigeo"),
                        "telefonos": data.get("telefonos", [])
                    }
                }
            else:
                raise HTTPException(response.status_code, "Error al consultar RUC")
                
    except httpx.TimeoutException:
        raise HTTPException(408, "Timeout al consultar RUC")
    except httpx.RequestError as e:
        raise HTTPException(500, f"Error de conexión: {str(e)}")


@router.post("/api/clientes/validar-dni")
async def validar_dni(request: ValidarDNIRequest):
    """Valida DNI con APIsPeru"""
    dni = request.dni.strip()
    
    if not dni.isdigit() or len(dni) != 8:
        raise HTTPException(400, "DNI debe tener 8 dígitos")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"https://dniruc.apisperu.com/api/v1/dni/{dni}"
            params = {"token": APISPERU_TOKEN}
            
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") == False:
                    raise HTTPException(404, data.get("message", "DNI no encontrado"))
                
                return {
                    "success": True,
                    "data": {
                        "dni": data.get("dni"),
                        "nombres": data.get("nombres"),
                        "apellido_paterno": data.get("apellidoPaterno"),
                        "apellido_materno": data.get("apellidoMaterno"),
                        "nombre_completo": f"{data.get('nombres')} {data.get('apellidoPaterno')} {data.get('apellidoMaterno')}"
                    }
                }
            else:
                raise HTTPException(response.status_code, "Error al consultar DNI")
                
    except httpx.TimeoutException:
        raise HTTPException(408, "Timeout al consultar DNI")
    except httpx.RequestError as e:
        raise HTTPException(500, f"Error de conexión: {str(e)}")


@router.post("/api/clientes/crear")
async def crear_cliente(
    request: CrearClienteRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Crea un nuevo cliente"""
    # Verificar si RUC ya existe
    cliente_existente = db.query(ClienteModel).filter(
        ClienteModel.ruc == request.ruc
    ).first()
    
    if cliente_existente:
        raise HTTPException(400, "El RUC ya está registrado")
    
    # Generar código de cliente
    ultimo_cliente = db.query(ClienteModel).order_by(
        ClienteModel.id.desc()
    ).first()
    
    if ultimo_cliente and ultimo_cliente.codigo_cliente:
        try:
            ultimo_num = int(ultimo_cliente.codigo_cliente.replace("CLI", ""))
            nuevo_codigo = f"CLI{ultimo_num + 1:04d}"
        except:
            nuevo_codigo = f"CLI{db.query(ClienteModel).count() + 1:04d}"
    else:
        nuevo_codigo = "CLI0001"
    
    # Crear cliente
    nuevo_cliente = ClienteModel(
        codigo_cliente=nuevo_codigo,
        ruc=request.ruc,
        razon_social=request.razon_social,
        nombre_comercial=request.nombre_comercial or request.razon_social,
        direccion_completa=request.direccion_completa,
        referencia=request.referencia,
        distrito=request.distrito,
        provincia=request.provincia,
        departamento=request.departamento,
        telefono=request.telefono,
        email=request.email,
        latitud=request.latitud,
        longitud=request.longitud,
        precision_gps=request.precision_gps,
        tipo_cliente_id=request.tipo_cliente_id,
        activo=True,
        verificado=False
    )
    
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    
    # Si hay datos de contacto, crear contacto
    if request.contacto_nombre or request.contacto_dni:
        from app.models import ContactoClienteModel
        
        contacto = ContactoClienteModel(
            cliente_id=nuevo_cliente.id,
            nombres=request.contacto_nombre or "",
            dni=request.contacto_dni,
            telefono=request.telefono,
            es_principal=True,
            activo=True
        )
        db.add(contacto)
        db.commit()
    
    return {
        "success": True,
        "message": "Cliente registrado exitosamente",
        "data": {
            "id": nuevo_cliente.id,
            "codigo_cliente": nuevo_cliente.codigo_cliente,
            "nombre_comercial": nuevo_cliente.nombre_comercial,
            "ruc": nuevo_cliente.ruc
        }
    }


@router.get("/api/clientes/tipos")
async def obtener_tipos_cliente(db: Session = Depends(get_db)):
    """Obtiene lista de tipos de cliente"""
    tipos = db.query(TipoClienteModel).filter(
        TipoClienteModel.activo == True
    ).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": t.id,
                "nombre": t.nombre,
                "descripcion": t.descripcion
            }
            for t in tipos
        ]
    }