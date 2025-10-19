# app/apis/utils.py - Sin router, solo lógica de cliente API
import requests
import logging
import os
from fastapi import HTTPException, status
from typing import Optional
from core.config import settings

class ApisNetPe:  # Mantén el nombre de la clase por compatibilidad
    def __init__(self, token: Optional[str] = None):
        self._api_token = token.strip() if token else None
        # ✅ CAMBIAR URL:
        self._api_url = "https://dniruc.apisperu.com/api/v1"
        
        if self._api_token:
            logging.info("APISPeru Client configured with token")
        else:
            logging.error("CRITICAL: APISPeru Client configured WITHOUT token!")

    def _get(self, path: str, params: dict = None) -> Optional[dict]:
        if not self._api_token:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="External API service is not configured"
            )
            
        # ✅ CAMBIAR URL y usar token en query param:
        url = f"{self._api_url}{path}"
        
        # APISPeru usa token en query string, no en headers
        if params is None:
            params = {}
        params['token'] = self._api_token

        print(f"\n--- API Call to apisperu.com ---")
        print(f"URL: {url}")
        print(f"PARAMS: {params}")
        print("--------------------------------\n")

        try:
            # Sin headers de Authorization
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as http_err:
            logging.warning(f"HTTP error from apisperu: {http_err}")
            
            detail = "Error consulting external service"
            try:
                error_response = http_err.response.json()
                detail = error_response.get("message", detail)
            except requests.exceptions.JSONDecodeError:
                detail = http_err.response.text if http_err.response.text else detail

            raise HTTPException(status_code=http_err.response.status_code, detail=detail)
        
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Network error connecting to apisperu: {req_err}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="Could not connect to external service"
            )

    def get_person(self, dni: str) -> Optional[dict]:
        """Consulta un DNI en RENIEC"""
        # ✅ CAMBIAR PATH:
        return self._get(f"/dni/{dni}")
        
    def get_company(self, ruc: str) -> Optional[dict]:
        """Consulta un RUC en SUNAT"""
        # ✅ CAMBIAR PATH:
        return self._get(f"/ruc/{ruc}")


# Funciones auxiliares para validación
def validar_formato_ruc(ruc: str) -> bool:
    """Valida el formato del RUC"""
    return (ruc.isdigit() and 
            len(ruc) == 11 and 
            (ruc.startswith('10') or ruc.startswith('20')))

def validar_formato_dni(dni: str) -> bool:
    """Valida el formato del DNI"""
    return dni.isdigit() and len(dni) == 8

def procesar_datos_empresa(company_data: dict) -> dict:
    """Procesa los datos de la empresa obtenidos de la API"""
    if not company_data:
        return None
    
    nombre_o_razon_social = company_data.get("nombre") or company_data.get("razonSocial")
    nombre_comercial = company_data.get("nombreComercial", "")
    direccion_raw = company_data.get("direccion", "")
    estado = company_data.get("estado", "")
    condicion = company_data.get("condicion", "")
    
    # ✅ La API de apisperu YA retorna estos campos por separado
    distrito = company_data.get("distrito", "")
    provincia = company_data.get("provincia", "")
    departamento = company_data.get("departamento", "")
    
    # ✅ Limpiar dirección: quitar ubicación del final SI está presente
    direccion = None
    if direccion_raw and direccion_raw.strip() != "-":
        # Si la API retorna ubicación en la dirección, quitarla
        if departamento and provincia and distrito:
            # Construir sufijo a remover (puede tener mayúsculas/minúsculas)
            sufijo = f"{departamento} {provincia} {distrito}".upper()
            direccion_upper = direccion_raw.upper()
            
            if direccion_upper.endswith(sufijo):
                # Quitar el sufijo del final
                direccion = direccion_raw[:-(len(sufijo))].strip()
            else:
                # No tiene sufijo o formato diferente, dejar como está
                direccion = direccion_raw
        else:
            direccion = direccion_raw
    
    return {
        "razonSocial": nombre_o_razon_social,
        "nombreComercial": nombre_comercial,
        "direccion": direccion,
        "distrito": distrito,
        "provincia": provincia,
        "departamento": departamento,
        "estado": estado,
        "condicion": condicion,
        "valido": True
    }

def procesar_datos_persona(person_data: dict) -> dict:
    """Procesa los datos de la persona obtenidos de la API"""
    if not person_data:
        return None
    
    # ✅ apisperu.com retorna: { "nombres": "...", "apellidoPaterno": "...", "apellidoMaterno": "..." }
    nombres = person_data.get("nombres", "")
    apellido_paterno = person_data.get("apellidoPaterno", "")
    apellido_materno = person_data.get("apellidoMaterno", "")
    
    return {
        "nombres": nombres,
        "apellidoPaterno": apellido_paterno,
        "apellidoMaterno": apellido_materno,
        "nombreCompleto": f"{nombres} {apellido_paterno} {apellido_materno}".strip(),
        "valido": True
    }

# ✅ CAMBIAR: Usar APISPERU_TOKEN en lugar de APIS_NET_PE_TOKEN
api_client = ApisNetPe(token=settings.APISPERU_TOKEN)

# Instancia global del cliente API
#api_client = ApisNetPe(token=settings.APIS_NET_PE_TOKEN)