"""Caricamento dei dati del progetto (personaggi ed eventi)."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def carica_personaggi() -> dict:
    """Restituisce {id: personaggio}."""
    with open(DATA_DIR / "personaggi.json", encoding="utf-8") as f:
        return {p["id"]: p for p in json.load(f)}


def carica_eventi() -> list:
    with open(DATA_DIR / "eventi.json", encoding="utf-8") as f:
        return json.load(f)
