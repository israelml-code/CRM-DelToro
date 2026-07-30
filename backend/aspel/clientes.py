"""
Conector con la API de Aspel ADM.
Obtiene todos los clientes y los convierte al formato del CRM.
"""

import json
import requests

ASPEL_URL = "https://adm.aspel.com.mx/AspelMovil/amIsapi.dll/DataSnap/Rest/TMetodosServidor/updateSrvCnsClientes"

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
    "user-agent": "Mozilla/5.0",
    "x-requested-with": "XMLHttpRequest",
}


def obtener_clientes_aspel(idsesion: str, pagina: int = 0) -> list[dict]:

    payload = {
        "IDSESION": idsesion,
        "NOREGINICIAL": str(pagina * 50),
        "TIPOCONSULTA": "1",
        "FILTROS": [],
        "CAMPOSCONSULTA": CAMPOS,
    }

    response = requests.put(
        ASPEL_URL,
        headers=HEADERS,
        data=json.dumps(payload),
        timeout=30,
    )

    if response.status_code not in (200, 201):
        raise Exception(
            f"Error de Aspel: {response.status_code}\n{response.text}"
        )

    result = response.json()

    print("=" * 80)
    print("RESPUESTA CLIENTES")
    print(json.dumps(result, indent=4, ensure_ascii=False))
    print("=" * 80)

    if "result" not in result:
        raise Exception("Aspel devolvió una respuesta inválida.")

    respuesta = result["result"][0]

    if respuesta.get("RESULTADO") != "-1":
        raise Exception(respuesta.get("MENSAJE"))

    registros = respuesta.get("REGISTROS", [])

    print(f"TOTAL CLIENTES: {len(registros)}")

    return registros


def mapear_cliente_aspel_a_crm(reg: dict) -> dict:

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
            f"Nombre comercial: {(reg.get('NOMCOMERCIAL') or reg.get('NOM') or '').strip()}"
        ),
    }