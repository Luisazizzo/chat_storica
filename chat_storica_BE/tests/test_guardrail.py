"""Test del guardrail. Lancio: python tests/test_guardrail.py (dalla cartella chat_storica)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.dati import carica_eventi, carica_personaggi
from src.guardrail import (controlla_conoscenza, formatta_anno,
                           risposta_fuori_epoca, trova_evento, trova_eventi)

P = carica_personaggi()
E = carica_eventi()


def test_cesare_non_conosce_la_seconda_guerra_mondiale():
    ev = trova_evento("Cosa pensi della seconda guerra mondiale?", E)
    assert ev is not None and ev["anno"] == 1939
    assert controlla_conoscenza(P["cesare"], ev["anno"])["puo_rispondere"] is False


def test_leonardo_conosce_la_stampa_ma_cesare_no():
    ev = trova_evento("Cosa ne pensi della stampa a caratteri mobili?", E)
    assert controlla_conoscenza(P["leonardo"], ev["anno"])["puo_rispondere"] is True
    assert controlla_conoscenza(P["galileo"], ev["anno"])["puo_rispondere"] is True
    assert controlla_conoscenza(P["cesare"], ev["anno"])["puo_rispondere"] is False


def test_galileo_conosce_il_telescopio_leonardo_no():
    ev = trova_evento("Parlami del telescopio", E)
    assert controlla_conoscenza(P["galileo"], ev["anno"])["puo_rispondere"] is True
    assert controlla_conoscenza(P["leonardo"], ev["anno"])["puo_rispondere"] is False


def test_evento_sconosciuto_restituisce_none():
    assert trova_evento("Qual è il tuo colore preferito?", E) is None


def test_anno_a_c_e_risposta_in_carattere():
    assert formatta_anno(-44) == "44 a.C."
    ev = trova_evento("Hai mai usato uno smartphone?", E)
    esito = controlla_conoscenza(P["cesare"], ev["anno"])
    testo = risposta_fuori_epoca(P["cesare"], ev, esito)
    assert "44 a.C." in testo and "lo smartphone" in testo


def test_trova_eventi_ordina_dal_piu_recente():
    anni = [e["anno"] for e in trova_eventi("telescopio, stampa a caratteri mobili e smartphone", E)]
    assert anni == sorted(anni, reverse=True) and len(anni) == 3


if __name__ == "__main__":
    test = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in test:
        t()
        print("OK ", t.__name__)
    print(f"\n{len(test)} test passati")
