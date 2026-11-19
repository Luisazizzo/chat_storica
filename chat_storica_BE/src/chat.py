"""Cuore della chat: guardrail temporale + RAG del personaggio + risposta in carattere.

Flusso di rispondi():
  1. cerca eventi nella domanda (parole chiave); se non ne trova, l'LLM stima l'anno
     dell'eventuale fatto/invenzione citato (SOLO la stima: la decisione è in codice);
  2. guardrail: se un evento è posteriore alla morte del personaggio -> risposta fissa in carattere,
     senza chiamare l'LLM di generazione;
  3. altrimenti RAG sui testi del personaggio + LLM con il prompt del personaggio;
  4. log di tutto in logs/eventi.jsonl.

Le dipendenze (rag, llm) sono passate dal chiamante: così la logica si testa senza OpenAI/Qdrant.
"""
import time
from typing import List

from pydantic import BaseModel, Field

from .guardrail import (controlla_conoscenza, formatta_anno,
                        risposta_fuori_epoca, trova_eventi)
from .osservabilita import log_evento

PRICE_IN, PRICE_OUT = 0.15, 0.60  # gpt-4o-mini, USD per 1M token


# ----------------------------------------------------------------- stima dell'anno (LLM)
class EventoStimato(BaseModel):
    riguarda_fatto_datato: bool = Field(
        description="True se la domanda cita un evento, invenzione, scoperta, persona o concetto collocabile nel tempo")
    nome: str = Field(
        description="Nome in italiano CON articolo, es. 'la stampa a caratteri mobili'. Stringa vuota se non applicabile")
    anno: int = Field(
        description="Anno in cui l'evento accade o l'invenzione nasce (negativo per a.C.). 0 se non applicabile")


PROMPT_STIMA = (
    "Sei un assistente di cronologia storica. Leggi la domanda e individua l'evento, invenzione, scoperta, "
    "persona o concetto più RECENTE che essa cita e che si possa datare. Indica il suo nome e l'anno in cui "
    "accade o nasce (numeri negativi per a.C.). Se la domanda è generica o atemporale (sentimenti, opinioni, "
    "la vita o le opere del personaggio stesso, saluti), imposta riguarda_fatto_datato=false."
)


# ----------------------------------------------------------------- prompt e helper
def costruisci_system_prompt(p: dict) -> str:
    return (
        f"Sei {p['nome']}, {p['ruolo']} (nato nel {formatta_anno(p['anno_nascita'])}, "
        f"morto nel {formatta_anno(p['anno_morte'])}). Stai chattando su WhatsApp con una persona "
        "che vuole conoscerti.\n\n"
        f"STILE: {p['stile']}\n\n"
        "REGOLE:\n"
        "1. Rispondi sempre in italiano, in prima persona, con messaggi brevi da chat (massimo 4-5 frasi).\n"
        "2. Per i fatti sulla tua vita e sulle tue opere usa SOLO le informazioni del CONTESTO. "
        "Se il contesto non basta, dillo restando nel personaggio (es. 'Su questo non ricordo bene...') "
        "senza inventare date, nomi o fatti.\n"
        "3. Non parlare mai di eventi, invenzioni o persone posteriori alla tua morte.\n"
        "4. Non nominare mai il 'contesto' o i 'documenti': parla come se fossero i tuoi ricordi.\n"
        "5. Non chiedere dati personali all'interlocutore."
    )


def formatta_contesto(hits) -> str:
    if not hits:
        return "(nessun ricordo utile trovato)"
    return "\n\n".join(f"[{h.metadata.get('source_file', '?')}]\n{h.text}" for h in hits)


def formatta_storia(storia, n: int = 6) -> str:
    turni = (storia or [])[-n:]
    if not turni:
        return "(inizio della conversazione)"
    return "\n".join(f"{'Interlocutore' if m['role'] == 'user' else 'Tu'}: {m['content']}" for m in turni)


def _token(usage):
    return (getattr(usage, "prompt_tokens", 0) or 0, getattr(usage, "completion_tokens", 0) or 0)


# ----------------------------------------------------------------- la chat
class ChatStorica:
    def __init__(self, personaggi: dict, eventi: list, rag, llm):
        self.personaggi = personaggi
        self.eventi = eventi
        self.rag = rag
        self.llm = llm

    def _stima_evento(self, domanda: str):
        """Fallback quando nessuna parola chiave combacia: l'LLM stima l'anno, il codice decide."""
        res = self.llm.structured_response(
            input=domanda, output_cls=EventoStimato, system_prompt=PROMPT_STIMA, temperature=0)
        s = res.structured_data[0]
        evento = None
        if s.riguarda_fatto_datato and s.anno != 0 and s.nome:
            evento = {"nome": s.nome, "anno": s.anno}
        return evento, _token(getattr(res, "usage", None))

    def rispondi(self, personaggio_id: str, domanda: str, storia: List[dict] = None) -> dict:
        t0 = time.perf_counter()
        p = self.personaggi[personaggio_id]
        tok_in = tok_out = 0

        # 1) eventi citati nella domanda
        eventi = trova_eventi(domanda, self.eventi)
        origine = "parole_chiave" if eventi else None
        if not eventi:
            stimato, (a, b) = self._stima_evento(domanda)
            tok_in += a
            tok_out += b
            if stimato:
                eventi, origine = [stimato], "llm"

        # 2) guardrail temporale (decisione in codice)
        for ev in eventi:  # dal più recente: basta UN evento posteriore alla morte
            esito = controlla_conoscenza(p, ev["anno"])
            if not esito["puo_rispondere"]:
                testo = risposta_fuori_epoca(p, ev, esito)
                return self._chiudi(t0, p, domanda, testo, True, eventi, origine, [], tok_in, tok_out)

        # 3) RAG + risposta in carattere
        hits = self.rag.cerca(personaggio_id, domanda)
        input_str = (
            f"CONTESTO (i tuoi ricordi):\n{formatta_contesto(hits)}\n\n"
            f"CONVERSAZIONE FINORA:\n{formatta_storia(storia)}\n\n"
            f"MESSAGGIO RICEVUTO: {domanda}"
        )
        r = self.llm.invoke(input=input_str, system_prompt=costruisci_system_prompt(p), temperature=0.7)
        a, b = _token(getattr(r, "usage", None))
        fonti = []
        for h in hits:
            f = h.metadata.get("source_file", "?")
            if f not in fonti:
                fonti.append(f)
        return self._chiudi(t0, p, domanda, r.text.strip(), False, eventi, origine, fonti, tok_in + a, tok_out + b)

    def _chiudi(self, t0, p, domanda, testo, guardrail, eventi, origine, fonti, tok_in, tok_out):
        costo = (tok_in * PRICE_IN + tok_out * PRICE_OUT) / 1_000_000
        out = {
            "testo": testo,
            "personaggio": p["id"],
            "guardrail": guardrail,
            "eventi": [{"nome": e["nome"], "anno": e["anno"]} for e in eventi],
            "origine_evento": origine,
            "fonti": fonti,
            "latenza_s": round(time.perf_counter() - t0, 2),
            "token_in": tok_in,
            "token_out": tok_out,
            "costo_usd": round(costo, 6),
        }
        log_evento("turno", domanda=domanda, **{k: v for k, v in out.items() if k != "testo"},
                   risposta=testo)
        return out
