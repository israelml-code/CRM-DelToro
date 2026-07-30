"""
Login automático con Aspel ADM Móvil.
Llama a SrvIniciaSesion para obtener el token JWT de sesión.
"""
import requests
import json

ASPEL_LOGIN_URL = "https://adm.aspel.com.mx/AspelMovil/amIsapi.dll/DataSnap/Rest/TMetodosServidor/SrvIniciaSesion"

HEADERS_LOGIN = {
    "accept": "*/*",
    "accept-language": "es-ES,es;q=0.9",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://adm.aspel.com.mx",
    "referer": "https://adm.aspel.com.mx/login.html",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}


def login_aspel(rfc: str, usuario: str, contrasenia: str) -> str:
    """
    Inicia sesión en Aspel ADM y devuelve el token IDSESION (JWT).
    
    Parámetros:
      rfc         - RFC de la empresa (ej: VAGA760428AK8)
      usuario     - Nombre de usuario de Aspel (ej: Administrador)
      contrasenia - Contraseña de Aspel
    
    Devuelve:
      El token JWT (IDSESION) listo para usar en las demás llamadas.
    """
    payload = {
        "RFC": rfc.strip().upper(),
        "CVEUSR": usuario.strip(),
        "CONTRASENIA": contrasenia,
        "ADMGRATUITO": "0",
        "STAT_INICIO": "",
        "TAMPAQUETE": "50",
        "VERSIONCLIE": "1.00.01",
        "TIPOCLIE": "2",
        "SONAVEG": "Chrome",
        "VERSONAVEG": "150.0.0.0",
        "DIRIP": "127.0.0.1",
    }

    response = requests.put(
        ASPEL_LOGIN_URL,
        headers=HEADERS_LOGIN,
        data=json.dumps(payload),
        timeout=30,
    )

    if response.status_code not in (200, 201):
        raise Exception(f"Error al conectar con Aspel: HTTP {response.status_code}")

    result = response.json()

    # La respuesta de Aspel viene en distintas formas según la versión
    # Intentamos extraer el IDSESION de donde sea que esté
    token = None

    # Forma 1: result[0]["result"] es el token directamente
    if isinstance(result, list) and len(result) > 0:
        r0 = result[0]
        if isinstance(r0, dict):
            token = r0.get("result") or r0.get("IDSESION") or r0.get("TOKEN")
        elif isinstance(r0, str):
            token = r0

    # Forma 2: result es un dict con "result"
    if not token and isinstance(result, dict):
        token = result.get("result") or result.get("IDSESION") or result.get("TOKEN")

    # Forma 3: buscar recursivamente en cualquier dict/lista
    if not token:
        token = _buscar_token(result)

    if not token:
        raise Exception(
            f"No se pudo extraer el token de la respuesta de Aspel. "
            f"Respuesta: {str(result)[:300]}"
        )

    # El token debe empezar con 'ey' (es un JWT)
    if not str(token).startswith("ey"):
        raise Exception(
            f"Credenciales incorrectas o empresa no encontrada. "
            f"Respuesta de Aspel: {str(result)[:300]}"
        )

    return str(token)


def _buscar_token(obj, depth=0):
    """Busca recursivamente un valor que parezca un JWT."""
    if depth > 5:
        return None
    if isinstance(obj, str) and obj.startswith("ey") and len(obj) > 50:
        return obj
    if isinstance(obj, list):
        for item in obj:
            found = _buscar_token(item, depth + 1)
            if found:
                return found
    if isinstance(obj, dict):
        for val in obj.values():
            found = _buscar_token(val, depth + 1)
            if found:
                return found
    return None