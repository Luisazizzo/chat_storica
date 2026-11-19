"""FastAPI server per la chat con personaggi storici.

Espone API REST per il frontend React.

Avvio:
    uvicorn api_server:app --reload --port 8000

Endpoints:
    GET  /api/personaggi          - Lista personaggi disponibili
    POST /api/chat                - Invia messaggio e ricevi risposta
    GET  /api/history/{session_id} - Recupera storia conversazione
    DELETE /api/history/{session_id} - Cancella storia
"""
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from src.chat import ChatStorica
from src.rag import RagStorico
from src.dati import carica_eventi, carica_personaggi

# ================================================================
# Modelli Pydantic per request/response
# ================================================================

class ChatRequest(BaseModel):
    """Richiesta di chat."""
    personaggio_id: str
    messaggio: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Risposta della chat."""
    risposta: str
    personaggio: str
    guardrail: bool
    eventi: List[Dict]
    origine_evento: Optional[str]
    fonti: List[str]
    latenza_s: float
    token_in: int
    token_out: int
    costo_usd: float
    session_id: str


class Personaggio(BaseModel):
    """Info su un personaggio."""
    id: str
    nome: str
    anno_nascita: int
    anno_morte: int
    ruolo: str
    stile: str
    periodo: str = ""  # Campo calcolato


class ErrorResponse(BaseModel):
    """Risposta di errore."""
    error: str
    detail: Optional[str] = None


# ================================================================
# Inizializzazione FastAPI
# ================================================================

app = FastAPI(
    title="Chat Storica API",
    description="API per chattare con personaggi storici (Giulio Cesare, Leonardo, Galileo)",
    version="1.0.0",
)

# CORS: permetti richieste dal frontend React (localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================================================
# Stato globale
# ================================================================

# Inizializzato al primo avvio
chat_system: Optional[ChatStorica] = None
personaggi: Dict = {}

# Flag: True dopo che startup_event ha finito di inizializzare il sistema
is_ready: bool = False

# Storia conversazioni per session_id
# In produzione: usa Redis o DB
conversation_history: Dict[str, Dict[str, List[Dict]]] = {}


# ================================================================
# Lifecycle
# ================================================================

@app.on_event("startup")
async def startup_event():
    """Inizializza il sistema al primo avvio."""
    global chat_system, personaggi, is_ready
    
    print("Inizializzazione sistema RAG...")
    rag = RagStorico(reindex=False)
    personaggi = carica_personaggi()
    eventi = carica_eventi()
    chat_system = ChatStorica(personaggi, eventi, rag, rag.llm)
    is_ready = True
    print("Sistema pronto!")


# ================================================================
# Endpoints
# ================================================================

@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "ok",
        "service": "Chat Storica API",
        "version": "1.0.0",
        "ready": is_ready,
    }


@app.get("/api/health")
async def health_check():
    """
    Indica se il backend ha finito l'inizializzazione (RAG, personaggi, ecc.).
    Il frontend polleda questo endpoint prima di caricare i personaggi.
    """
    if not is_ready:
        raise HTTPException(status_code=503, detail="Backend ancora in fase di avvio")
    return {"status": "ready", "ready": True}


@app.get("/api/personaggi", response_model=List[Personaggio])
async def get_personaggi():
    """Lista tutti i personaggi disponibili."""
    return [
        Personaggio(
            id=p["id"],
            nome=p["nome"],
            anno_nascita=p["anno_nascita"],
            anno_morte=p["anno_morte"],
            ruolo=p["ruolo"],
            stile=p["stile"],
            periodo=f"{p['anno_nascita']}-{p['anno_morte']}",
        )
        for p in personaggi.values()
    ]


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Invia un messaggio a un personaggio e ricevi la risposta."""
    
    # Validazione
    if request.personaggio_id not in personaggi:
        raise HTTPException(
            status_code=404,
            detail=f"Personaggio '{request.personaggio_id}' non trovato"
        )
    
    if not request.messaggio.strip():
        raise HTTPException(status_code=400, detail="Messaggio vuoto")
    
    # Session ID (per mantenere la storia)
    session_id = request.session_id or str(uuid.uuid4())
    
    # Recupera o crea storia per questa sessione
    if session_id not in conversation_history:
        conversation_history[session_id] = {p["id"]: [] for p in personaggi.values()}
    
    storia = conversation_history[session_id].get(request.personaggio_id, [])
    
    # Chiama il sistema di chat
    try:
        risultato = chat_system.rispondi(
            request.personaggio_id,
            request.messaggio,
            storia=storia
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nella chat: {str(e)}")
    
    # Aggiorna storia
    conversation_history[session_id][request.personaggio_id].extend([
        {"role": "user", "content": request.messaggio},
        {"role": "assistant", "content": risultato["testo"]}
    ])
    
    # Risposta
    return ChatResponse(
        risposta=risultato["testo"],
        personaggio=risultato["personaggio"],
        guardrail=risultato["guardrail"],
        eventi=risultato["eventi"],
        origine_evento=risultato["origine_evento"],
        fonti=risultato["fonti"],
        latenza_s=risultato["latenza_s"],
        token_in=risultato["token_in"],
        token_out=risultato["token_out"],
        costo_usd=risultato["costo_usd"],
        session_id=session_id,
    )


@app.get("/api/history/{session_id}")
async def get_history(session_id: str, personaggio_id: Optional[str] = None):
    """Recupera la storia conversazionale di una sessione."""
    
    if session_id not in conversation_history:
        raise HTTPException(status_code=404, detail="Session non trovata")
    
    if personaggio_id:
        if personaggio_id not in personaggi:
            raise HTTPException(status_code=404, detail="Personaggio non trovato")
        return {
            "session_id": session_id,
            "personaggio_id": personaggio_id,
            "history": conversation_history[session_id].get(personaggio_id, [])
        }
    
    # Tutta la storia della sessione
    return {
        "session_id": session_id,
        "history": conversation_history[session_id]
    }


@app.delete("/api/history/{session_id}")
async def delete_history(session_id: str, personaggio_id: Optional[str] = None):
    """Cancella la storia conversazionale."""
    
    if session_id not in conversation_history:
        raise HTTPException(status_code=404, detail="Session non trovata")
    
    if personaggio_id:
        # Cancella solo per un personaggio
        if personaggio_id in conversation_history[session_id]:
            conversation_history[session_id][personaggio_id] = []
        return {"status": "ok", "message": f"Storia con {personaggio_id} cancellata"}
    
    # Cancella tutta la sessione
    del conversation_history[session_id]
    return {"status": "ok", "message": "Sessione cancellata"}


@app.get("/api/stats")
async def get_stats():
    """Statistiche del server."""
    total_sessions = len(conversation_history)
    total_messages = sum(
        len(msgs)
        for session in conversation_history.values()
        for msgs in session.values()
    )
    
    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "personaggi_disponibili": len(personaggi),
    }


# ================================================================
# Error handlers
# ================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler per HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "detail": str(exc.status_code)},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
