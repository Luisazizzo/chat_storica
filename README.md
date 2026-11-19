# Chat Storica

**Chat Storica** è un'applicazione web che permette di conversare con alcuni dei più importanti personaggi della storia, attraverso un'interfaccia ispirata a WhatsApp.

## Funzionalità

Il progetto permette di:

- **Conversare con personaggi storici** come Giulio Cesare, Leonardo da Vinci, Galileo Galilei, Dante Alighieri e Napoleone Bonaparte.
- **Ricevere risposte in carattere**, generate utilizzando testi e fonti associati a ciascun personaggio.
- **Consultare conoscenze storiche tramite RAG**, che recupera le informazioni dai documenti disponibili.
- **Rispettare la cronologia storica**: ogni personaggio non può conoscere o parlare di eventi successivi alla propria morte. Questo controllo è gestito da un guardrail implementato direttamente nel codice.
- **Visualizzare le conversazioni** attraverso un'interfaccia grafica con elenco dei personaggi e cronologia dei messaggi.
- **Registrare gli eventi delle conversazioni** per facilitare il monitoraggio e l'analisi del funzionamento del sistema.

## Tecnologie utilizzate

| Componente       | Tecnologia                 |
| ---------------- | -------------------------- |
| Frontend         | React 19, TypeScript, Vite |
| Backend          | Python, FastAPI, Uvicorn   |
| RAG              | datapizza-ai, Qdrant       |
| Modello AI       | GPT-4o-mini                |
| Embeddings       | text-embedding-3-small     |
| Elaborazione PDF | Docling                    |
| Container        | Docker                     |

## Prerequisiti

Prima di avviare il progetto è necessario avere installato:

- Docker Desktop (avviato).
- Python 3.12 o superiore.
- Node.js 18 o superiore.
- Una chiave API OpenAI.

## Installazione e configurazione

### 1. Installazione frontend

Dalla cartella principale del progetto, eseguire:

```powershell
npm install
```

### 2. Installazione backend

Accedere alla cartella del backend e creare l'ambiente virtuale Python:

```powershell
cd chat_storica_BE

python -m venv .venv

.venv\Scripts\activate

pip install -r requirements.txt

deactivate

cd ..
```

### 3. Configurazione API OpenAI

Creare o verificare la presenza del file `.env` all'interno della cartella `chat_storica_BE/`.

Inserire la propria chiave API:

```env
OPENAI_API_KEY=la_tua_chiave_api
```

## Avvio del progetto

### Avvio completo (consigliato)

Dalla cartella principale del progetto, eseguire:

```powershell
npm run start:all
```

Il comando avvia automaticamente:

- **Qdrant**, tramite Docker, sulla porta `6336`.
- **Backend FastAPI**, sulla porta `8000`.
- **Frontend React**, sulla porta `5173`.

Il frontend attende automaticamente che il backend sia pronto prima di iniziare a comunicare con esso.

Una volta completato l'avvio, l'applicazione è disponibile all'indirizzo:

**http://localhost:5173**

### Comandi alternativi

È possibile avviare separatamente i diversi componenti:

| Comando               | Funzione                                                  |
| --------------------- | --------------------------------------------------------- |
| `npm start`           | Avvia backend e frontend (Qdrant deve essere già attivo). |
| `npm run docker`      | Avvia Qdrant tramite Docker.                              |
| `npm run docker:stop` | Arresta Qdrant.                                           |
| `npm run backend`     | Avvia solamente il backend.                               |
| `npm run dev`         | Avvia solamente il frontend.                              |
| `npm run build`       | Genera la build di produzione del frontend.               |

## Chat da terminale (opzionale)

Il progetto mette a disposizione anche una versione utilizzabile direttamente dal terminale.

Per avviarla:

```powershell
cd chat_storica_BE
.venv\Scripts\activate
python chat_terminale.py
```

Al primo avvio vengono indicizzati i testi utilizzati dal sistema RAG.

Per aggiornare l'indice dopo aver modificato o aggiunto dei documenti:

```powershell
python chat_terminale.py --reindex
```

Comandi disponibili durante la conversazione:

- `/contatti`: cambia personaggio.
- `/esci`: termina la chat.

## Test

Per eseguire i test del backend:

```powershell
cd chat_storica_BE
.venv\Scripts\activate

python tests/test_guardrail.py
python tests/test_chat.py
```

I test verificano il funzionamento della chat e del guardrail temporale.

**Nota:** per eseguire questi test non sono necessarie né una chiave API OpenAI né Docker.

## Struttura del progetto

```text
chat_storica_progetto_finale/
│
├── src/                      # Frontend React
│   ├── components/            # Componenti dell'interfaccia
│   ├── services/              # Comunicazione con le API
│   ├── types/                 # Tipi TypeScript
│   ├── utils/                 # Funzioni di supporto
│   ├── assets/                # Immagini dei personaggi
│   ├── App.tsx
│   └── main.tsx
│
├── chat_storica_BE/           # Backend Python
│   ├── src/                   # Logica della chat e RAG
│   ├── data/                  # Personaggi, eventi e documenti
│   ├── docker/                # Configurazione Docker
│   ├── tests/                 # Test automatici
│   ├── api_server.py
│   ├── chat_terminale.py
│   ├── requirements.txt
│   └── .env
│
├── package.json
├── tsconfig.json
├── vite.config.js
└── index.html
```

## Aggiungere un nuovo personaggio

Per aggiungere un personaggio storico:

1. Inserire i suoi dati nel file `chat_storica_BE/data/personaggi.json`.
2. Creare una cartella dedicata in `chat_storica_BE/data/corpus/` e inserirvi i documenti in formato `.md` o `.pdf`.
3. Aggiungere la relativa immagine in `src/assets/`.
4. Aggiornare la mappa `personaggioImages` nei componenti `ContactList.tsx` e `ChatWindow.tsx`.
5. Aggiornare l'indice RAG eseguendo:

```powershell
cd chat_storica_BE
.venv\Scripts\activate
python chat_terminale.py --reindex
```

## Aggiungere nuove fonti

È possibile ampliare le conoscenze dei personaggi aggiungendo nuovi documenti nella rispettiva cartella all'interno di `chat_storica_BE/data/corpus/`.

Ad esempio, è possibile salvare pagine di Wikipedia in formato PDF e successivamente aggiornare l'indice RAG con il comando `--reindex`.

Quando si utilizzano contenuti provenienti da Wikipedia, è necessario indicare la fonte e la data di consultazione, nel rispetto della licenza CC BY-SA.

## Endpoint API

| Metodo | Endpoint                    | Descrizione                                 |
| ------ | --------------------------- | ------------------------------------------- |
| GET    | `/api/health`               | Verifica lo stato del backend.              |
| GET    | `/api/personaggi`           | Restituisce i personaggi disponibili.       |
| POST   | `/api/chat`                 | Invia un messaggio e riceve una risposta.   |
| GET    | `/api/history/{session_id}` | Recupera la cronologia della conversazione. |
| DELETE | `/api/history/{session_id}` | Cancella la cronologia della conversazione. |
| GET    | `/api/stats`                | Restituisce statistiche sul server.         |

## Link utili

| Servizio                     | Indirizzo                       |
| ---------------------------- | ------------------------------- |
| Applicazione web             | http://localhost:5173           |
| Backend API                  | http://localhost:8000           |
| Documentazione API (Swagger) | http://localhost:8000/docs      |
| Dashboard Qdrant             | http://localhost:6336/dashboard |

## Note

I testi presenti in `data/corpus/` sono sintesi realizzate per il progetto a partire da conoscenze storiche generali. È consigliabile verificarli e, ove possibile, affiancarli a fonti pubbliche e citabili, come Wikipedia, Wikisource e opere di pubblico dominio.

Il progetto non richiede né salva dati personali degli utenti.
