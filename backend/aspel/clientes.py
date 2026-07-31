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


def _fetch_pagina(idsesion, noreginicial):
    """Llama a Aspel y devuelve los registros de una página."""
    payload = {
        "IDSESION": idsesion,
        "TAMPAQUETE": 100,
        "NOREGINICIAL": str(noreginicial),
        "TIPOCONSULTA": "2",
        "CAMPOSCONSULTA": CAMPOS,
        "ORDEN": [{"CAMPO": "RZNSOCIAL", "ORDENAMIENTO": "1"}],
    }
    response = requests.put(
        ASPEL_URL,
        headers=HEADERS,
        data=json.dumps(payload),
        timeout=30,
    )
    response.raise_for_status()
    resultado = response.json()
    respuesta = resultado["result"][0]
    if respuesta["RESULTADO"] != "-1":
        raise Exception(respuesta["MENSAJE"])
    return respuesta["Datos"]["rows"]


def obtener_clientes_aspel(idsesion, pagina=0):
    """
    Trae TODOS los clientes de Aspel usando paginación automática.
    Llama a Aspel en páginas de 100 registros hasta que no haya más.
    """
    todos = []
    noreginicial = 0

    while True:
        registros = _fetch_pagina(idsesion, noreginicial)
        todos.extend(registros)
        print(f"Página {noreginicial//100 + 1}: {len(registros)} clientes (total acumulado: {len(todos)})")

        # Si devolvió menos de 100, es la última página
        if len(registros) < 100:
            break

        noreginicial += 100

        # Seguro máximo: no más de 5000 clientes (50 páginas)
        if noreginicial >= 5000:
            print("Límite de seguridad alcanzado (5000 clientes)")
            break

    print(f"Total clientes de Aspel: {len(todos)}")
    return todos


def mapear_cliente_aspel_a_crm(reg):
    datos = reg["data"]
    return {
        "empresa": datos[0].strip() if len(datos) > 0 else "",
        "rfc":     datos[1].strip() if len(datos) > 1 else "",
        "telefono":datos[2].strip() if len(datos) > 2 else "",
        "contacto":datos[18].strip() if len(datos) > 18 else "",
        "email":   datos[13].strip() if len(datos) > 13 else "",
        "ciudad":  datos[7].strip() if len(datos) > 7 else "",
        "puesto":  "",
        "tipo":    "cliente",
        "giro":    "",
        "notas":   "Importado desde Aspel ADM",
    }