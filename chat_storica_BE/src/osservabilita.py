"""Log minimale: una riga JSON per evento in logs/eventi.jsonl."""
import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent.parent / "logs" / "eventi.jsonl"


def log_evento(tipo: str, **dati) -> None:
    LOG_FILE.parent.mkdir(exist_ok=True)
    riga = {"ora": datetime.now().isoformat(timespec="seconds"), "tipo": tipo, **dati}
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(riga, ensure_ascii=False) + "\n")
