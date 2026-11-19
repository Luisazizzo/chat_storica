"""Guardrail temporale: un personaggio non può parlare di ciò che è accaduto dopo la sua morte.

Il controllo è fatto IN CODICE, non nel prompt: i modelli tendono a rispondere comunque.
Convenzione: gli anni avanti Cristo sono numeri negativi (44 a.C. = -44).
"""


def formatta_anno(anno: int) -> str:
    return f"{abs(anno)} a.C." if anno < 0 else str(anno)


def trova_evento(domanda: str, eventi: list):
    """Cerca nella domanda un evento noto tramite parole chiave.

    Ritorna l'evento (dict) oppure None. Se più parole chiave combaciano,
    vince la più lunga (più specifica).
    """
    testo = domanda.lower()
    migliore, lunghezza = None, 0
    for evento in eventi:
        for chiave in evento["parole_chiave"]:
            if chiave in testo and len(chiave) > lunghezza:
                migliore, lunghezza = evento, len(chiave)
    return migliore


def controlla_conoscenza(personaggio: dict, anno_evento: int) -> dict:
    """Decide se il personaggio può conoscere un evento di anno_evento."""
    morte = personaggio["anno_morte"]
    if anno_evento <= morte:
        return {"puo_rispondere": True, "anno_evento": anno_evento}
    return {
        "puo_rispondere": False,
        "anno_evento": anno_evento,
        "anni_dopo_la_morte": anno_evento - morte,
    }


def risposta_fuori_epoca(personaggio: dict, evento: dict, esito: dict) -> str:
    """Risposta fissa 'in carattere' quando il personaggio non può sapere."""
    return personaggio["frase_fuori_epoca"].format(
        evento=evento["nome"],
        anno_morte=formatta_anno(personaggio["anno_morte"]),
        anni_dopo=esito["anni_dopo_la_morte"],
    )


def trova_eventi(domanda: str, eventi: list) -> list:
    """Tutti gli eventi noti citati nella domanda, dal più recente al più antico.

    Serve per domande con più riferimenti (es. 'telescopio e smartphone'):
    se UNO solo è posteriore alla morte del personaggio, il guardrail deve scattare.
    """
    testo = domanda.lower()
    trovati = [e for e in eventi if any(k in testo for k in e["parole_chiave"])]
    return sorted(trovati, key=lambda e: e["anno"], reverse=True)
