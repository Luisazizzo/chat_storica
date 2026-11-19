# 🐳 Docker Setup - Progetto Finale

Tutti i file Docker sono organizzati in questa cartella.

## 📁 Struttura

```
docker/
├── docker-compose.yml       # Orchestrazione servizi
├── Dockerfile.backend       # Backend FastAPI
├── Dockerfile.frontend      # Frontend React
├── .dockerignore           # File esclusi dalla build
└── README.md               # Questa guida
```

---

## 🚀 Comandi Quick Start

### Solo Qdrant (minimo)

```powershell
# Dalla root del progetto (chat_storica_BE/)
docker compose -f docker/docker-compose.yml up -d
```

Apri: http://localhost:6336/dashboard

---

### Qdrant + Backend FastAPI

```powershell
docker compose -f docker/docker-compose.yml --profile backend up -d
```

- Qdrant: http://localhost:6336/dashboard
- Backend API: http://localhost:8000/docs

---

### Stack completo (Qdrant + Backend + Frontend)

```powershell
# Prima crea il progetto frontend (se non esiste)
# Vedi ../FRONTEND_REACT.md per le istruzioni

docker compose -f docker/docker-compose.yml --profile full up -d
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Qdrant: http://localhost:6336/dashboard

---

## 🎯 Profili disponibili

Il `docker-compose.yml` usa **profiles** per avviare solo i servizi necessari:

| Comando | Servizi avviati | Quando usarlo |
|---------|----------------|---------------|
| `docker compose -f docker/docker-compose.yml up -d` | Solo Qdrant | Sviluppo Python locale |
| `--profile backend` | Qdrant + Backend | Test API + frontend esterno |
| `--profile frontend` | Qdrant + Backend + Frontend | Demo completa |
| `--profile full` | Tutto | Deploy completo |

---

## 📦 File Docker

### `docker-compose.yml`

Orchestrazione dei servizi:
- **qdrant**: Vector store (sempre attivo)
- **backend**: FastAPI server (profilo `backend` o `full`)
- **frontend**: React app (profilo `frontend` o `full`)

**Rete**: Tutti i servizi comunicano via `chat-network` bridge.

---

### `Dockerfile.backend`

Build del backend FastAPI:
- Base: `python:3.12-slim`
- Installa: requirements.txt
- Espone: porta 8000
- Comando: `uvicorn api_server:app --reload`

---

### `Dockerfile.frontend`

Build del frontend React:
- Base: `node:18-alpine`
- Installa: npm dependencies
- Espone: porta 3000
- Comando: `npm run dev` (dev) o `npm run preview` (prod)

---

### `.dockerignore`

Esclude dalla build:
- `.venv/`, `__pycache__/`, `node_modules/`
- `.env` (secrets)
- `qdrant_storage/`, `logs/`

---

## 🔧 Comandi utili

### Avvio e stop

```powershell
# Avvia (dalla root chat_storica_BE/)
docker compose -f docker/docker-compose.yml up -d

# Avvia con profilo
docker compose -f docker/docker-compose.yml --profile backend up -d

# Stop (mantiene i dati)
docker compose -f docker/docker-compose.yml stop

# Stop e rimuovi container
docker compose -f docker/docker-compose.yml down

# Stop e rimuovi TUTTO (anche volumi)
docker compose -f docker/docker-compose.yml down -v
```

---

### Log

```powershell
# Tutti i log
docker compose -f docker/docker-compose.yml logs

# Solo Qdrant
docker compose -f docker/docker-compose.yml logs qdrant

# Segui log in tempo reale
docker compose -f docker/docker-compose.yml logs -f backend

# Ultimi 50
docker compose -f docker/docker-compose.yml logs --tail=50 qdrant
```

---

### Build e rebuild

```powershell
# Build servizi (senza avviare)
docker compose -f docker/docker-compose.yml build

# Build specifico
docker compose -f docker/docker-compose.yml build backend

# Rebuild forzato (ignora cache)
docker compose -f docker/docker-compose.yml build --no-cache backend

# Build e avvia
docker compose -f docker/docker-compose.yml up -d --build
```

---

### Diagnostica

```powershell
# Lista container attivi
docker compose -f docker/docker-compose.yml ps

# Esegui comando in un container
docker compose -f docker/docker-compose.yml exec backend bash

# Entra in Qdrant
docker compose -f docker/docker-compose.yml exec qdrant sh

# Verifica rete
docker network inspect chat_storica_be_chat-network
```

---

## 🗑️ Pulizia e reset

### Reset solo indice Qdrant

```powershell
# 1. Stop servizi
docker compose -f docker/docker-compose.yml stop

# 2. Cancella dati (dalla root chat_storica_BE/)
rmdir /s /q qdrant_storage

# 3. Riavvia
docker compose -f docker/docker-compose.yml up -d
```

---

### Reset completo progetto

```powershell
# Stop e rimuovi tutto
docker compose -f docker/docker-compose.yml down -v

# Rimuovi dati locali
rmdir /s /q qdrant_storage
rmdir /s /q logs

# Riavvia
docker compose -f docker/docker-compose.yml up -d
```

---

## ⚙️ Variabili d'ambiente

Il file `.env` nella root del progetto viene letto automaticamente:

```env
# .env (nella root chat_storica_BE/)
OPENAI_API_KEY=sk-...
QDRANT_HOST=localhost
QDRANT_PORT=6336
```

**Container override**:
- Dentro i container, `QDRANT_HOST=qdrant` (nome del servizio)
- Fuori dai container, `QDRANT_HOST=localhost`

---

## 🔌 Porte esposte

| Servizio | Porta Host | Porta Container | URL |
|----------|-----------|----------------|-----|
| Qdrant | 6336 | 6333 | http://localhost:6336/dashboard |
| Backend | 8000 | 8000 | http://localhost:8000/docs |
| Frontend | 3000 | 3000 | http://localhost:3000 |

---

## 🎯 Workflow consigliato

### Sviluppo locale (Python + React)

```powershell
# Terminal 1: Solo Qdrant
docker compose -f docker/docker-compose.yml up -d

# Terminal 2: Backend locale
.venv\Scripts\activate
uvicorn api_server:app --reload

# Terminal 3: Frontend locale
cd chat-storica-frontend
npm run dev
```

**Vantaggi:**
- Hot reload immediato
- Debug più facile
- Nessuna build Docker

---

### Demo o deploy

```powershell
# Stack completo containerizzato
docker compose -f docker/docker-compose.yml --profile full up -d --build
```

**Vantaggi:**
- Tutto isolato
- Facile da distribuire
- Pronto per deploy

---

## 🆘 Troubleshooting

### "Port already in use"

```powershell
# Cambia porta in docker-compose.yml
# qdrant:
#   ports:
#     - "6337:6333"  # Usa 6337 invece di 6336
```

---

### "Cannot connect to Docker daemon"

1. Avvia Docker Desktop
2. Aspetta che sia pronto (icona balena nella tray)
3. Riprova

---

### "Backend cannot reach Qdrant"

Verifica network:
```powershell
docker compose -f docker/docker-compose.yml exec backend ping qdrant
```

Se fallisce, ricrea network:
```powershell
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml up -d
```

---

### Build fallisce

```powershell
# Pulisci cache Docker
docker builder prune

# Rebuild senza cache
docker compose -f docker/docker-compose.yml build --no-cache
```

---

## 📋 Cheat Sheet

```powershell
# === COMANDI BASE ===
docker compose -f docker/docker-compose.yml up -d              # Avvia solo Qdrant
docker compose -f docker/docker-compose.yml --profile backend up -d  # + Backend
docker compose -f docker/docker-compose.yml --profile full up -d     # Tutto

# === GESTIONE ===
docker compose -f docker/docker-compose.yml ps                 # Stato
docker compose -f docker/docker-compose.yml logs -f            # Log live
docker compose -f docker/docker-compose.yml stop               # Stop
docker compose -f docker/docker-compose.yml down               # Rimuovi

# === BUILD ===
docker compose -f docker/docker-compose.yml build              # Build
docker compose -f docker/docker-compose.yml up -d --build      # Build + avvia

# === PULIZIA ===
docker compose -f docker/docker-compose.yml down -v            # Tutto
rmdir /s /q qdrant_storage                                     # Indice locale
```

---

## 📚 Riferimenti

- **Docker Compose docs**: https://docs.docker.com/compose/
- **Qdrant docs**: https://qdrant.tech/documentation/
- **FastAPI docs**: https://fastapi.tiangolo.com/
- **Comandi Docker completi**: ../DOCKER_COMMANDS.md

---

**Pronto per partire! 🚀**

Per sviluppo: usa Python + React locali con solo Qdrant in Docker.  
Per demo/deploy: usa `--profile full` per containerizzare tutto.
