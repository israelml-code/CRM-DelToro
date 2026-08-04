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


def _fetch_pagina_facturas(idsesion, noreginicial, rfc="", usuario="", doctocompleto=0, tampaquete=100):
    """Llama a Aspel y devuelve las facturas de una página."""
    campos_dinamicos = dict(CAMPOS)
    campos_dinamicos["DOCTOCOMPLETO"] = str(doctocompleto)
    if doctocompleto == 1:
        campos_dinamicos["PARTIDAS"] = {"CAMPO1": "DESCART"}
    elif "PARTIDAS" in campos_dinamicos:
        del campos_dinamicos["PARTIDAS"]

    payload = {
        "IDSESION": idsesion,
        "TAMPAQUETE": tampaquete,
        "NOREGINICIAL": str(noreginicial),
        "TIPOCONSULTA": "2",
        "CVETIPODOC": "F",
        "CAMPOSCONSULTA": campos_dinamicos,
        "ORDEN": [{"CAMPO": "FECREG", "ORDENAMIENTO": "2"}],
    }
    # Incluir cookies de sesión igual que el navegador
    cookies = {}
    if rfc:     cookies["frc"]     = rfc
    if usuario: cookies["usuario"] = usuario

    response = requests.put(
        ASPEL_URL,
        headers=HEADERS,
        data=json.dumps(payload),
        cookies=cookies if cookies else None,
        timeout=120,
    )
    response.raise_for_status()
    resultado = response.json()
    respuesta = resultado["result"][0]
    if respuesta["RESULTADO"] != "-1":
        raise Exception(respuesta["MENSAJE"])
    return respuesta["Datos"]["rows"]


def obtener_facturas_aspel(idsesion, rfc="", usuario=""):
    """
    Trae TODAS las facturas de Aspel usando paginación automática con paracaídas.
    Intenta traer partidas (DOCTOCOMPLETO=1) de 50 en 50.
    Si falla, reintenta esa misma página sin partidas (DOCTOCOMPLETO=0) para evitar que se congele.
    """
    todas = []
    noreginicial = 0
    tampaquete = 50

    while True:
        try:
            registros = _fetch_pagina_facturas(idsesion, noreginicial, rfc=rfc, usuario=usuario, doctocompleto=1, tampaquete=tampaquete)
        except Exception as e:
            print(f"⚠️ Error al obtener facturas con artículos (página {noreginicial//tampaquete + 1}). Abriendo paracaídas... Error: {e}")
            # Paracaídas: Reintentar sin artículos
            registros = _fetch_pagina_facturas(idsesion, noreginicial, rfc=rfc, usuario=usuario, doctocompleto=0, tampaquete=tampaquete)

        todas.extend(registros)
        print(f"Página Facturas {noreginicial//tampaquete + 1}: {len(registros)} (total: {len(todas)})")

        if len(registros) < tampaquete:
            break

        noreginicial += tampaquete

        if noreginicial >= 10000:
            print("Límite de seguridad alcanzado (10000 facturas)")
            break

    print(f"Total facturas de Aspel: {len(todas)}")
    return todas


def _normalizar_fecha(raw):
    """Convierte cualquier formato de fecha de Aspel a YYYY-MM-DD."""
    if not raw:
        return ""
    raw = str(raw).strip()[:10]
    from datetime import datetime
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except:
            continue
    return raw  # Si no se puede parsear, devolver como está


def mapear_factura_aspel_a_crm(reg):
    datos = reg["data"]
    cveser = datos[1].strip() if len(datos) > 1 else ""
    folio  = datos[2].strip() if len(datos) > 2 else ""

    def parse_float(val):
        try:
            if not val and val != 0:
                return 0.0
            # Aspel envía números con coma de miles: "1,190.74" → limpiar antes de convertir
            cleaned = str(val).replace(',', '').strip()
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0

    resultado = {
        "numero":      f"{cveser}-{folio}" if cveser else folio,
        "folio":       folio,
        "serie":       cveser,
        # ← Fecha normalizada a YYYY-MM-DD para comparación y frontend
        "fecha":       _normalizar_fecha(datos[3] if len(datos) > 3 else ""),
        "rfc_cliente": datos[5].strip() if len(datos) > 5 else "",
        "razon_social":datos[6].strip() if len(datos) > 6 else "",
        "subtotal":    parse_float(datos[15] if len(datos) > 15 else 0),
        "descuento":   parse_float(datos[16] if len(datos) > 16 else 0),
        "iva":         parse_float(datos[18] if len(datos) > 18 else 0),
        "total":       parse_float(datos[25] if len(datos) > 25 else 0),
        "estado_doc":  datos[22].strip() if len(datos) > 22 else "",
        "forma_pago":  datos[28].strip() if len(datos) > 28 else "",
        "metodo_pago": datos[29].strip() if len(datos) > 29 else "",
    }
    
    # Extraer conceptos de manera robusta
    partidas_raw = reg.get("PARTIDAS") or reg.get("partidas") or []
    conceptos_list = []
    for p in partidas_raw:
        if isinstance(p, dict) and "data" in p and len(p["data"]) > 0:
            val = p["data"][0]
            if val and str(val).strip():
                conceptos_list.append(str(val).strip())
        elif isinstance(p, list) and len(p) > 0:
            val = p[0]
            if val and str(val).strip():
                conceptos_list.append(str(val).strip())
    
    resultado["conceptos"] = ", ".join(conceptos_list)
    return resultado

