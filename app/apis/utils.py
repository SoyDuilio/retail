# app/apis/utils.py - Sin router, solo lógica de cliente API
import requests
import logging
import os
from fastapi import HTTPException, status
from typing import Optional
from core.config import settings

class ApisNetPe:
    def __init__(self, token: Optional[str] = None):
        self._api_token = token.strip() if token else None
        self._api_url = "https://api.apis.net.pe"
        
        if self._api_token:
            logging.info("ApisNetPe Client configured with token")
        else:
            logging.error("CRITICAL: ApisNetPe Client configured WITHOUT token!")

    def _get(self, path: str, params: dict) -> Optional[dict]:
        print(f"DEBUG: self._api_token = '{self._api_token}'")
        print(f"DEBUG: bool(self._api_token) = {bool(self._api_token)}")
        if not self._api_token:
            logging.error("API Token for apis.net.pe is missing")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="External API service is not configured"
            )
            
        url = f"{self._api_url}{path}"
        headers = {
            "Authorization": f"Bearer {self._api_token}",
        }

        print(f"\n--- API Call to apis.net.pe ---")
        print(f"URL: {url}")
        print(f"PARAMS: {params}")
        print("--------------------------------\n")

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as http_err:
            logging.warning(f"HTTP error from apis.net.pe: {http_err}")
            
            print(f"\n--- API Error Response ---")
            print(f"Status Code: {http_err.response.status_code}")
            print(f"Response: {http_err.response.text}")
            print("--------------------------\n")

            detail = "Error consulting external service"
            try:
                error_response = http_err.response.json()
                detail = error_response.get("message", detail)
            except requests.exceptions.JSONDecodeError:
                detail = http_err.response.text if http_err.response.text else detail

            raise HTTPException(status_code=http_err.response.status_code, detail=detail)
        
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Network error connecting to apis.net.pe: {req_err}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="Could not connect to external service"
            )

    def get_person(self, dni: str) -> Optional[dict]:
        """Consulta un DNI en RENIEC"""
        return self._get("/v2/reniec/dni", {"numero": dni})
        
    def get_company(self, ruc: str) -> Optional[dict]:
        """Consulta un RUC en SUNAT"""
        return self._get("/v2/sunat/ruc", {"numero": ruc})


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
    direccion = company_data.get("direccion")
    estado = company_data.get("estado")
    condicion = company_data.get("condicion")
    
    # Procesar dirección
    if not direccion or direccion.strip() == "-":
        direccion = "Dirección no disponible"
    
    return {
        "razonSocial": nombre_o_razon_social,
        "direccion": direccion,
        "estado": estado,
        "condicion": condicion,
        "valido": True
    }

def procesar_datos_persona(person_data: dict) -> dict:
    """Procesa los datos de la persona obtenidos de la API"""
    if not person_data:
        return None
    
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


# Instancia global del cliente API
api_client = ApisNetPe(token=settings.APIS_NET_PE_TOKEN)