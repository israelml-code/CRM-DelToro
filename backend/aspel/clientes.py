"""
Conector con la API de Aspel ADM.
"""

import json
import requests

ASPEL_URL = (
    "https://adm.aspel.com.mx/"
    "AspelMovil/amIsapi.dll/"
    "DataSnap/Rest/TMetodosServidor/%22updateSrvCnsClientes%22"
)

CAMPOS = {
    "CAMPO1": "RZNSOCIAL",
    "CAMPO2": "RFC",
    "CAMPO3": "TEL",
    "CAMPO4": "CALLE",
    "CAMPO5": "NOEXT",
    "CAMPO6": "COL",
    "CAMPO7": "LOC",
    "CAMPO8": "MUN",
    "CAMPO9": "EDO",
    "CAMPO10": "PAIS",
    "CAMPO11": "CP",
    "CAMPO12": "NOMBCONTACTO",
    "CAMPO13": "DESCTO",
    "CAMPO14": "DIRELECT",
    "CAMPO15": "MANCRED",
    "CAMPO16": "DCRED",
    "CAMPO17": "LIMCRED",
    "CAMPO18": "VERIFICA",
    "CAMPO19": "NOMCOMERCIAL",
}

HEADERS = {
    "accept": "*/*",
    "accept-language": "es-ES,es;q=0.9",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://adm.aspel.com.mx",
    "referer": "https://adm.aspel.com.mx/principal.html",
    "user-agent": "Mozilla/5.0",
    "x-requested-with": "XMLHttpRequest",
}


def obtener_clientes_aspel(idsesion, pagina=0):

    payload = {
        "IDSESION": idsesion,
        "TAMPAQUETE": 100,
        "NOREGINICIAL": str(pagina * 100),
        "TIPOCONSULTA": "2",
        "CAMPOSCONSULTA": CAMPOS,
        "ORDEN": [
            {
                "CAMPO": "RZNSOCIAL",
                "ORDENAMIENTO": "1"
            }
        ]
    }

    response = requests.put(
        ASPEL_URL,
        headers=HEADERS,
        data=json.dumps(payload),
        timeout=30,
    )

    print(response.status_code)
    print(response.text)

    response.raise_for_status()

    resultado = response.json()

    print(json.dumps(resultado, indent=4, ensure_ascii=False))

    respuesta = resultado["result"][0]

    if respuesta["RESULTADO"] != "-1":
        raise Exception(respuesta["MENSAJE"])

    datos = respuesta["Datos"]

    registros = datos["rows"]

    print("TOTAL:", datos["total_count"])

    # Mostrar el primer cliente completo
    if registros:
        print("=" * 80)
        print(json.dumps(registros[0], indent=4, ensure_ascii=False))
        print("=" * 80)

    return registros

def mapear_cliente_aspel_a_crm(reg: dict) -> dict:
    """
    Convierte un cliente de Aspel ADM al formato del CRM.
    """

    municipio = (reg.get("MUN") or "").strip()
    estado = (reg.get("EDO") or "").strip()

    if municipio and estado:
        ciudad = f"{municipio}, {estado}"
    elif municipio:
        ciudad = municipio
    else:
        ciudad = estado

    return {
        "empresa": (reg.get("RZNSOCIAL") or "").strip(),
        "rfc": (reg.get("RFC") or "").strip(),
        "contacto": (reg.get("NOMBCONTACTO") or "").strip(),
        "puesto": "",
        "telefono": (reg.get("TEL") or "").strip(),
        "email": (reg.get("DIRELECT") or "").strip(),
        "ciudad": ciudad,
        "tipo": "Cliente",
        "giro": "",
        "notas": (
            "Importado desde Aspel ADM. "
            f"Nombre comercial: {(reg.get('NOMCOMERCIAL') or '').strip()}"
        ),
    }


def mapear_cliente_aspel_a_crm(reg):

    datos = reg["data"]

    return {
        "empresa": datos[0].strip() if len(datos) > 0 else "",
        "rfc": datos[1].strip() if len(datos) > 1 else "",
        "telefono": datos[2].strip() if len(datos) > 2 else "",
        "contacto": datos[18].strip() if len(datos) > 18 else "",
        "email": datos[13].strip() if len(datos) > 13 else "",
        "ciudad": datos[7].strip() if len(datos) > 7 else "",
        "puesto": "",
        "tipo": "Cliente",
        "giro": "",
        "notas": "Importado desde Aspel ADM"
    }