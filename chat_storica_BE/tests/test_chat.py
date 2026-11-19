"""Test dell'orchestrazione con finti LLM e RAG (nessuna chiamata a OpenAI/Qdrant).
Lancio: python tests/test_chat.py (dalla cartella chat_storica)."""
import json
import sys
import tempfile
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:  # se pydantic non è installato uso un finto modulo, solo per questo test
    import pydantic  # noqa: F401
except ImportError:
    stub = types.ModuleType("pydantic")

    class _BaseModel:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    stub.BaseModel = _BaseModel
    stub.Field = lambda *a, **k: None
    sys.modules["pydantic"] = stub

from src import osservabilita  # noqa: E402
from src.chat import ChatStorica, EventoStimato  # noqa: E402
from src.dati import carica_eventi, carica_personaggi  # noqa: E402
from src.guardrail import trova_eventi  # noqa: E402

LOG_TMP = Path(tempfile.mkdtemp()) / "eventi.jsonl"
osservabilita.LOG_FILE = LOG_TMP


class Usage:
    prompt_tokens, completion_tokens = 100, 50


class Risp:
    def __init__(self, text):
        self.text, self.usage = text, Usage()


class Hit:
    def __init__(self, text, src):
        self.text, self.metadata = text, {"source_file": src}


class FakeRag:
    def __init__(self):
        self.chiamate = 0

    def cerca(self, pid, domanda, k=3):
        self.chiamate += 1
        return [Hit("Nacque a Roma nel 100 a.C.", "biografia.md")]


class FakeLLM:
    def __init__(self, stima=None):
        self.stima, self.invoke_calls, self.struct_calls = stima, [], 0

    def invoke(self, input, system_prompt, temperature=0):
        self.invoke_calls.append((system_prompt, input))
        return Risp("Risposta finta")

    def structured_response(self, input, output_cls, system_prompt, temperature=0):
        self.struct_calls += 1
        s = self.stima or EventoStimato(riguarda_fatto_datato=False, nome="", anno=0)
        return types.SimpleNamespace(structured_data=[s], usage=Usage())


def nuova_chat(stima=None):
    rag, llm = FakeRag(), FakeLLM(stima)
    return ChatStorica(carica_personaggi(), carica_eventi(), rag, llm), rag, llm


def test_guardrail_per_parola_chiave_non_chiama_llm_ne_rag():
    chat, rag, llm = nuova_chat()
    r = chat.rispondi("cesare", "Cosa pensi della seconda guerra mondiale?")
    assert r["guardrail"] is True and r["origine_evento"] == "parole_chiave"
    assert "44 a.C." in r["testo"]
    assert llm.struct_calls == 0 and llm.invoke_calls == [] and rag.chiamate == 0


def test_domanda_nel_suo_tempo_usa_rag_e_llm():
    chat, rag, llm = nuova_chat()
    r = chat.rispondi("leonardo", "Cosa pensi della stampa a caratteri mobili?")
    assert r["guardrail"] is False and r["testo"] == "Risposta finta"
    assert rag.chiamate == 1 and len(llm.invoke_calls) == 1
    assert r["fonti"] == ["biografia.md"]


def test_guardrail_con_anno_stimato_dal_llm():
    stima = EventoStimato(riguarda_fatto_datato=True, nome="TikTok", anno=2016)
    chat, rag, llm = nuova_chat(stima)
    r = chat.rispondi("galileo", "Cosa ne pensi di TikTok?")
    assert r["guardrail"] is True and r["origine_evento"] == "llm"
    assert llm.struct_calls == 1 and llm.invoke_calls == [] and rag.chiamate == 0


def test_domanda_generica_prosegue_normalmente():
    chat, rag, llm = nuova_chat()  # il finto LLM dice: nessun fatto datato
    r = chat.rispondi("cesare", "Come ti senti oggi?")
    assert r["guardrail"] is False and llm.struct_calls == 1 and len(llm.invoke_calls) == 1


def test_piu_eventi_basta_uno_posteriore():
    ev = carica_eventi()
    nomi = [e["nome"] for e in trova_eventi("Hai usato il telescopio o lo smartphone?", ev)]
    assert nomi == ["lo smartphone", "il telescopio"]
    chat, _, _ = nuova_chat()
    assert chat.rispondi("galileo", "Hai usato il telescopio o lo smartphone?")["guardrail"] is True


def test_prompt_di_sistema_e_storia():
    chat, _, llm = nuova_chat()
    storia = [{"role": "user", "content": "Ciao"}, {"role": "assistant", "content": "Salve!"}]
    chat.rispondi("cesare", "Parlami della Gallia", storia)
    system, inp = llm.invoke_calls[0]
    assert "Giulio Cesare" in system and "44 a.C." in system
    assert "Interlocutore: Ciao" in inp and "Tu: Salve!" in inp and "Nacque a Roma" in inp


def test_log_scritto():
    righe = [json.loads(r) for r in LOG_TMP.read_text(encoding="utf-8").splitlines()]
    assert righe and all(r["tipo"] == "turno" for r in righe)
    assert any(r["guardrail"] for r in righe) and any(not r["guardrail"] for r in righe)
    assert "costo_usd" in righe[0] and "latenza_s" in righe[0]


if __name__ == "__main__":
    test = [v for k, v in globals().items() if k.startswith("test_")]  # ordine di definizione
    for t in test:
        t()
        print("OK ", t.__name__)
    print(f"\n{len(test)} test passati")
