"""
Conector con la API de Aspel ADM para facturas.
"""

import json
import requests

ASPEL_URL = (
    "https://adm.aspel.com.mx/"
    "AspelMovil/amIsapi.dll/"
    "DataSnap/Rest/TMetodosServidor/%22updateSrvCnsDoctos%22"
)

CAMPOS = {
    "DOCTOCOMPLETO": "0",
    "CABECERA": {
        "CAMPO1":"CVEDOC","CAMPO2":"CVESER","CAMPO3":"FOLIO",
        "CAMPO4":"FECREG","CAMPO5":"FECHATIMBRE","CAMPO6":"RFC",
        "CAMPO7":"RZNSOCIAL","CAMPO8":"UUIDTIMBRE","CAMPO9":"NUMCERSAT",
        "CAMPO10":"DESGIMP","CAMPO11":"TASDESC","CAMPO12":"TASRETIVA",
        "CAMPO13":"TASISR","CAMPO14":"TASIMPESP1","CAMPO15":"DESCMON",
        "CAMPO16":"SUBTOT","CAMPO17":"TOTDESCU","CAMPO18":"TOTIEPS",
        "CAMPO19":"TOTIVA","CAMPO20":"TOTRETIVA","CAMPO21":"TOTISR",
        "CAMPO22":"TOTIMPESP1","CAMPO23":"EDODOCTO","CAMPO24":"CVEDOCREL",
        "CAMPO25":"EDOCFDI","CAMPO26":"TOT","CAMPO27":"UUID_CLIE",
        "CAMPO28":"CVECONFIRMPAC","CAMPO29":"FORMPAG","CAMPO30":"DESCMETPAGO",
        "CAMPO31":"ACTCXC","CAMPO32":"MENSAJECANCEL","CAMPO33":"EDOCANCEL",
        "CAMPO34":"FECCANCEL","CAMPO35":"DESCEDOCANCEL","CAMPO36":"FACORG",
        "CAMPO37":"MOTIVOCANCEL","CAMPO38":"FOLIOFISCAL"
    }
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

def _fetch_pagina_facturas(idsesion, noreginicial):
    """Llama a Aspel y devuelve las facturas de una página."""
    payload = {
        "IDSESION": idsesion,
        "TAMPAQUETE": 100,
        "NOREGINICIAL": str(noreginicial),
        "TIPOCONSULTA": "2",
        "CVETIPODOC": "F",
        "CAMPOSCONSULTA": CAMPOS,
        "ORDEN": [{"CAMPO":"FECREG","ORDENAMIENTO":"2"}],
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

def obtener_facturas_aspel(idsesion):
    """
    Trae TODAS las facturas de Aspel usando paginación automática.
    Llama a Aspel en páginas de 100 registros hasta que no haya más.
    """
    todas = []
    noreginicial = 0

    while True:
        registros = _fetch_pagina_facturas(idsesion, noreginicial)
        todas.extend(registros)
        print(f"Página Facturas {noreginicial//100 + 1}: {len(registros)} facturas (total acumulado: {len(todas)})")

        if len(registros) < 100:
            break

        noreginicial += 100

        if noreginicial >= 10000:
            print("Límite de seguridad alcanzado (10000 facturas)")
            break

    print(f"Total facturas de Aspel: {len(todas)}")
    return todas

def mapear_factura_aspel_a_crm(reg):
    datos = reg["data"]
    cveser = datos[1].strip() if len(datos) > 1 else ""
    folio = datos[2].strip() if len(datos) > 2 else ""
    
    def parse_float(val):
        try:
            return float(val) if val else 0.0
        except:
            return 0.0

    return {
        "numero": f"{cveser}-{folio}" if cveser else folio,
        "folio": folio,
        "serie": cveser,
        "fecha": datos[3].strip() if len(datos) > 3 else "",
        "rfc_cliente": datos[5].strip() if len(datos) > 5 else "",
        "razon_social": datos[6].strip() if len(datos) > 6 else "",
        "subtotal": parse_float(datos[15] if len(datos) > 15 else 0),
        "descuento": parse_float(datos[16] if len(datos) > 16 else 0),
        "iva": parse_float(datos[18] if len(datos) > 18 else 0),
        "total": parse_float(datos[25] if len(datos) > 25 else 0),
        "estado_doc": datos[22].strip() if len(datos) > 22 else "",
        "forma_pago": datos[28].strip() if len(datos) > 28 else "",
        "metodo_pago": datos[29].strip() if len(datos) > 29 else "",
    }
