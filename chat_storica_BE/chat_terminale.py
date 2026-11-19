"""Chat da terminale con i personaggi storici.

Uso:
    python chat_terminale.py            # avvio normale (riusa l'indice Qdrant se già creato)
    python chat_terminale.py --reindex  # ricostruisce l'indice (dopo aver cambiato i testi in data/corpus)
"""
import argparse

from dotenv import load_dotenv

load_dotenv()  # PRIMA di importare il resto: legge OPENAI_API_KEY da .env

from src.chat import ChatStorica  # noqa: E402
from src.dati import carica_eventi, carica_personaggi  # noqa: E402
from src.guardrail import formatta_anno  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reindex", action="store_true", help="ricostruisce l'indice dei testi")
    args = ap.parse_args()

    from src.rag import RagStorico  # import qui: richiede datapizza-ai installato

    print("Preparo i ricordi dei personaggi (la prima volta può volerci qualche minuto)...")
    rag = RagStorico(reindex=args.reindex)
    chat = ChatStorica(carica_personaggi(), carica_eventi(), rag, rag.llm)

    contatti = list(chat.personaggi.values())
    storie = {p["id"]: [] for p in contatti}  # una cronologia per contatto = memoria per chat
    corrente = None

    while True:
        if corrente is None:
            print("\nContatti:")
            for i, p in enumerate(contatti, 1):
                print(f"  {i}. {p['nome']}  ({p['ruolo']})")
            scelta = input("Con chi vuoi chattare? (numero, oppure /esci): ").strip()
            if scelta == "/esci":
                break
            if scelta.isdigit() and 1 <= int(scelta) <= len(contatti):
                corrente = contatti[int(scelta) - 1]["id"]
                print(f"\n--- Chat con {chat.personaggi[corrente]['nome']} "
                      "(/contatti per cambiare, /esci per uscire) ---")
            else:
                print("Scelta non valida.")
            continue

        p = chat.personaggi[corrente]
        try:
            domanda = input("\nTu: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not domanda:
            continue
        if domanda == "/esci":
            break
        if domanda == "/contatti":
            corrente = None
            continue

        r = chat.rispondi(corrente, domanda, storie[corrente])
        print(f"\n{p['nome']}: {r['testo']}")
        if r["guardrail"]:
            ev = r["eventi"][0]
            print(f"   [guardrail: {ev['nome']} ({formatta_anno(ev['anno'])}) è dopo la morte "
                  f"di {p['nome']} ({formatta_anno(p['anno_morte'])})]")
        elif r["fonti"]:
            print(f"   [fonti: {', '.join(r['fonti'])}]")
        storie[corrente] += [{"role": "user", "content": domanda},
                             {"role": "assistant", "content": r["testo"]}]


if __name__ == "__main__":
    main()
