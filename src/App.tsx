import { useState, useEffect, useCallback } from "react";
import ContactList from "./components/ContactList";
import ChatWindow from "./components/ChatWindow";
import {
  getPersonaggi,
  sendMessage,
  waitForBackend,
  getHistory,
  clearHistory,
} from "./services/api";
import type { Messaggio, Personaggio } from "./types";
import cesareLogo from "./assets/giulio_cesare.jpg";
import leonardoLogo from "./assets/leonardo_da_vinci.jpg";
import galileoLogo from "./assets/galileo_galilei.jpg";
import danteLogo from "./assets/dante_alighieri.jpg";
import napoleoneLogo from "./assets/napoleone_buonaparte.jpg";
import "./App.css";

/** Immagini dei personaggi da precaricare */
const personaggioImages = [
  cesareLogo,
  leonardoLogo,
  galileoLogo,
  danteLogo,
  napoleoneLogo,
];

/** Converte lo storico del backend (role/content) nel formato frontend (ruolo/testo) */
const backendToMessaggi = (
  history: Array<{ role: string; content: string }>,
): Messaggio[] =>
  history.map((msg) => ({
    ruolo: msg.role === "user" ? "utente" : "assistente",
    testo: msg.content,
    timestamp: new Date().toISOString(),
  }));

function App(): React.JSX.Element {
  const [personaggi, setPersonaggi] = useState<Personaggio[]>([]);
  const [selectedPersonaggio, setSelectedPersonaggio] =
    useState<Personaggio | null>(null);
  const [messagesByPersonaggio, setMessagesByPersonaggio] = useState<
    Record<string, Messaggio[]>
  >({});
  const [loading, setLoading] = useState<boolean>(false);
  const [sessionId] = useState<string>(() => `session_${Date.now()}`);
  const [backendReady, setBackendReady] = useState<boolean>(false);
  const [showError, setShowError] = useState<boolean>(false);
  const [showOverlay, setShowOverlay] = useState<boolean>(true);

  // I messaggi correnti = quelli del personaggio selezionato
  const messages = selectedPersonaggio
    ? (messagesByPersonaggio[selectedPersonaggio.id] ?? [])
    : [];

  // Rimuovi il loader inline dell'HTML appena React monta
  useEffect(() => {
    const initialLoader = document.getElementById("initial-loader");
    if (initialLoader) {
      initialLoader.remove();
    }

    // Precarica le immagini dei personaggi mentre il backend si avvia
    personaggioImages.forEach((src) => {
      const img = new Image();
      img.src = src;
    });
  }, []);

  // Attendi che il backend sia pronto, poi carica i personaggi
  useEffect(() => {
    let cancelled = false;

    const init = async (): Promise<void> => {
      // Polla l'health endpoint fino a 60 volte (2s = 2 minuti max)
      const ready = await waitForBackend(60, 2000, (attempt, max) => {
        if (!cancelled) {
          console.log(`Attesa backend... tentativo ${attempt}/${max}`);
        }
      });

      if (cancelled) return;

      if (!ready) {
        setShowError(true);
        return;
      }

      try {
        const data = await getPersonaggi();
        setPersonaggi(data);
        setBackendReady(true);
      } catch (error) {
        console.error("Errore nel caricamento personaggi:", error);
        setShowError(true);
      }
    };

    init();

    return () => {
      cancelled = true;
    };
  }, []);

  // Fade-out graduale dell'overlay quando il backend è pronto
  useEffect(() => {
    if (backendReady) {
      const timer = setTimeout(() => setShowOverlay(false), 400);
      return () => clearTimeout(timer);
    }
  }, [backendReady]);

  // Seleziona personaggio: carica storico dal backend se non è ancora in cache
  const handleSelectPersonaggio = useCallback(
    async (personaggio: Personaggio): Promise<void> => {
      setSelectedPersonaggio(personaggio);

      // Se abbiamo già i messaggi in cache, non fare nulla
      if (messagesByPersonaggio[personaggio.id]) return;

      // Prima volta: prova a caricare lo storico dal backend
      try {
        const history = await getHistory(sessionId, personaggio.id);
        if (history.length > 0) {
          const messaggi = backendToMessaggi(history);
          setMessagesByPersonaggio((prev) => ({
            ...prev,
            [personaggio.id]: messaggi,
          }));
        }
      } catch (error) {
        // 404 = nessuna conversazione ancora, è normale
        console.log(`Nessuno storico per ${personaggio.id}:`, error);
      }
    },
    [messagesByPersonaggio, sessionId],
  );

  const handleClearConversation = async (): Promise<void> => {
    if (!selectedPersonaggio) return;

    const personaggioId = selectedPersonaggio.id;

    try {
      await clearHistory(sessionId, personaggioId);
    } catch (error) {
      console.error("Errore nella cancellazione conversazione:", error);
    }

    setMessagesByPersonaggio((prev) => {
      const next = { ...prev };
      delete next[personaggioId];
      return next;
    });
  };

  const handleSendMessage = async (testo: string): Promise<void> => {
    if (!selectedPersonaggio) return;

    const personaggioId = selectedPersonaggio.id;
    const userMessage: Messaggio = {
      ruolo: "utente",
      testo: testo,
      timestamp: new Date().toISOString(),
    };

    // Aggiungi messaggio utente
    setMessagesByPersonaggio((prev) => ({
      ...prev,
      [personaggioId]: [...(prev[personaggioId] ?? []), userMessage],
    }));

    setLoading(true);
    try {
      const response = await sendMessage(sessionId, personaggioId, testo);

      const aiMessage: Messaggio = {
        ruolo: "assistente",
        testo: response.risposta,
        timestamp: new Date().toISOString(),
      };
      setMessagesByPersonaggio((prev) => ({
        ...prev,
        [personaggioId]: [...(prev[personaggioId] ?? []), aiMessage],
      }));
    } catch (error) {
      console.error("Errore nell'invio messaggio:", error);
      const errorMessage: Messaggio = {
        ruolo: "assistente",
        testo: "Mi dispiace, si è verificato un errore. Riprova.",
        timestamp: new Date().toISOString(),
      };
      setMessagesByPersonaggio((prev) => ({
        ...prev,
        [personaggioId]: [...(prev[personaggioId] ?? []), errorMessage],
      }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <ContactList
        personaggi={backendReady ? personaggi : []}
        selectedPersonaggio={selectedPersonaggio}
        onSelectPersonaggio={handleSelectPersonaggio}
      />
      <ChatWindow
        personaggio={selectedPersonaggio}
        messages={messages}
        onSendMessage={handleSendMessage}
        onClearConversation={handleClearConversation}
        loading={loading}
      />

      {showOverlay && (
        <div
          className={`loading-overlay ${backendReady ? "loading-overlay-fadeout" : ""}`}
        >
          <div className="loading-modal">
            <div className="antique-wheel"></div>
            <p>
              {showError
                ? "Impossibile connettersi al server"
                : "Caricamento dei contatti..."}
            </p>
            {showError && (
              <div className="error-box">
                <p>Il backend non risponde.</p>
                <p style={{ fontSize: "14px", fontWeight: "400" }}>
                  Verifica che Docker e il backend siano avviati, poi riprova.
                </p>
                <button onClick={() => window.location.reload()}>
                  Riprova
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
