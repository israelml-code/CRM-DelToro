"""
Conector con la API interna de Aspel ADM Móvil.
Usa el endpoint updateSrvCnsClientes para traer TODOS los clientes.
"""
import requests

ASPEL_URL = "https://adm.aspel.com.mx/AspelMovil/amIsapi.dll/DataSnap/Rest/TMetodosServidor/%22updateSrvCnsClientes%22"

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
    "CAMPO14": "REF",
    "CAMPO15": "CRUZ1",
    "CAMPO16": "CRUZ2",
    "CAMPO17": "DIRELECT",
    "CAMPO18": "NOINT",
    "CAMPO19": "METODOPAG",
    "CAMPO20": "NUMCTAPAG",
    "CAMPO21": "STAT",
    "CAMPO22": "MANCRED",
    "CAMPO23": "DCRED",
    "CAMPO24": "LIMCRED",
    "CAMPO25": "SALDO",
    "CAMPO26": "CVECOMP",
    "CAMPO27": "NOM",
    "CAMPO28": "VALESQUEMACLIE",
    "CAMPO29": "RESIDENCIAFISCAL",
    "CAMPO30": "NUMREGIDTRIB",
    "CAMPO31": "USOCFDI",
    "CAMPO32": "DESCRESIFIS",
    "CAMPO33": "DESCUSOCFDI",
    "CAMPO34": "RFCCTAORDENANTE",
    "CAMPO35": "NOMBANCOORDEXT",
    "CAMPO36": "CTAORDENANTE",
    "CAMPO37": "CTAPREDIAL",
    "CAMPO38": "USODESGLOSE",
    "CAMPO39": "REGIMFISC",
    "CAMPO40": "CVEPAIS",
    "CAMPO41": "VERIFICA",
    "CAMPO42": "NOMCOMERCIAL",
}

HEADERS = {
    "accept": "*/*",
    "accept-language": "es-ES,es;q=0.9",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://adm.aspel.com.mx",
    "referer": "https://adm.aspel.com.mx/principal.html",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}


def obtener_clientes_aspel(idsesion: str, pagina: int = 0) -> list[dict]:
    """
    Llama al endpoint de Aspel ADM y devuelve todos los clientes.
    
    - idsesion: El JWT que obtienes de DevTools (campo IDSESION)
    - pagina: Para paginación (0 = primeros registros, luego incrementar)
    """
    payload = {
        "IDSESION": idsesion,
        "NOREGINICIAL": str(pagina * 50),
        "TIPOCONSULTA": "1",
        "FILTROS": [],
        "CAMPOSCONSULTA": CAMPOS,
    }

    import json
    response = requests.put(
        ASPEL_URL,
        headers=HEADERS,
        data=json.dumps(payload),
        timeout=30,
    )

    if response.status_code != 200:
        raise Exception(f"Error de Aspel: {response.status_code} - {response.text[:200]}")

    result = response.json()

    # La respuesta de Aspel viene en result[0]["result"]
    # que es una lista de registros
    try:
        registros = result[0]["result"]
        if isinstance(registros, str):
            registros = json.loads(registros)
        return registros if isinstance(registros, list) else []
    except (IndexError, KeyError, TypeError):
        # Intentar otras estructuras de respuesta
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "result" in result:
            r = result["result"]
            return r if isinstance(r, list) else []
        return []


def mapear_cliente_aspel_a_crm(reg: dict) -> dict:
    """
    Convierte un registro de Aspel al formato del CRM Del Toro.
    
    Campos Aspel → Campos CRM:
      RZNSOCIAL → empresa
      RFC       → rfc
      TEL       → telefono
      NOMBCONTACTO → contacto
      DIRELECT  → email
      MUN/EDO   → ciudad
      NOM       → notas (nombre comercial como referencia)
    """
    # Ciudad: municipio + estado
    mun = (reg.get("MUN") or "").strip()
    edo = (reg.get("EDO") or "").strip()
    if mun and edo:
        ciudad = f"{mun}, {edo}"
    elif edo:
        ciudad = edo
    elif mun:
        ciudad = mun
    else:
        ciudad = ""

    return {
        "empresa": (reg.get("RZNSOCIAL") or reg.get("NOM") or "").strip(),
        "rfc": (reg.get("RFC") or "").strip(),
        "contacto": (reg.get("NOMBCONTACTO") or "").strip(),
        "puesto": "",
        "telefono": (reg.get("TEL") or "").strip(),
        "email": (reg.get("DIRELECT") or "").strip(),
        "ciudad": ciudad,
        "tipo": "cliente",
        "giro": "",
        "notas": f"Importado de Aspel ADM. Nombre comercial: {(reg.get('NOM') or '').strip()}".strip(". "),
    }
