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
     raise Exception(f"HTTP {response.status_code}")

    result = response.json()

    print("=" * 80)
    print("STATUS:", response.status_code)
    print(json.dumps(result, indent=4, ensure_ascii=False))
    print("=" * 80)

    token = None

    if isinstance(result, dict):

       if "result" in result and len(result["result"]) > 0:

         respuesta = result["result"][0]

    print("RESULTADO:", respuesta.get("RESULTADO"))
    print("MENSAJE:", respuesta.get("MENSAJE"))

    if respuesta.get("RESULTADO") == "-1":

        datos = respuesta.get("DATOS", {})

        print("DATOS:", datos)

        token = datos.get("IDSESION")
    if not token:
        raise Exception(f"No se encontró IDSESION.\nRespuesta: {result}")

    return token