import { useState, useEffect, useRef } from "react";
import type { FormEvent } from "react";
import Message from "./Message";
import Lightbox from "./Lightbox";
import { formatPeriodo, formatAnno } from "../utils/dateUtils";
import "./ChatWindow.css";
import cesareLogo from "../assets/giulio_cesare.jpg";
import leonardoLogo from "../assets/leonardo_da_vinci.jpg";
import galileoLogo from "../assets/galileo_galilei.jpg";
import danteLogo from "../assets/dante_alighieri.jpg";
import napoleoneLogo from "../assets/napoleone_buonaparte.jpg";
import type { ChatWindowProps, PersonaggioImages } from "../types";

const personaggioImages: PersonaggioImages = {
  cesare: cesareLogo,
  leonardo: leonardoLogo,
  galileo: galileoLogo,
  dante: danteLogo,
  napoleone: napoleoneLogo,
};

const ChatWindow = ({
  personaggio,
  messages,
  onSendMessage,
  onClearConversation,
  loading,
}: ChatWindowProps): React.JSX.Element => {
  const [inputValue, setInputValue] = useState<string>("");
  const [showLightbox, setShowLightbox] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = (): void => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    if (inputValue.trim() && !loading) {
      onSendMessage(inputValue);
      setInputValue("");
    }
  };

  if (!personaggio) {
    return (
      <div className="chat-window">
        <div className="no-chat-selected">
          <h2>Benvenuto nella Chat Storica</h2>
          <p>Seleziona un personaggio storico per iniziare una conversazione</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-window">
      <div className="chat-header">
        <div
          className="chat-header-avatar clickable"
          onClick={() => setShowLightbox(true)}
          title="Clicca per vedere l'immagine completa"
        >
          <img src={personaggioImages[personaggio.id]} alt={personaggio.nome} />
        </div>
        <div className="chat-header-info">
          <div className="chat-header-name">{personaggio.nome}</div>
          <div className="chat-header-period">
            {formatPeriodo(personaggio.anno_nascita, personaggio.anno_morte)}
          </div>
        </div>
        <button
          className="chat-clear-button"
          onClick={onClearConversation}
          title="Elimina conversazione"
          disabled={messages.length === 0}
        >
          <svg viewBox="0 0 24 24" width="20" height="20">
            <path
              fill="currentColor"
              d="M9 3v1H4v2h1v13a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V6h1V4h-5V3H9zm2 5h2v9h-2V8zm-4 0h2v9H7V8zm8 0h2v9h-2V8z"
            />
          </svg>
        </button>
      </div>

      {showLightbox && (
        <Lightbox
          image={personaggioImages[personaggio.id]}
          name={personaggio.nome}
          onClose={() => setShowLightbox(false)}
        />
      )}

      <div className="chat-messages">
        <div className="chat-messages-content">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <p>Inizia una conversazione con {personaggio.nome}!</p>
              <p className="welcome-hint">
                Ricorda: {personaggio.nome.split(" ")[0]} può rispondere solo su
                eventi accaduti prima del {formatAnno(personaggio.anno_morte)}.
              </p>
            </div>
          ) : (
            messages.map((msg, index) => (
              <Message
                key={index}
                message={msg}
                isUser={msg.ruolo === "utente"}
              />
            ))
          )}
          {loading && (
            <div className="message ai">
              <div className="message-bubble">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="chat-input-container">
        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Scrivi un messaggio..."
            className="chat-input"
            disabled={loading}
          />
          <button
            type="submit"
            className="chat-send-button"
            disabled={!inputValue.trim() || loading}
          >
            <svg viewBox="0 0 24 24" width="24" height="24">
              <path
                fill="currentColor"
                d="M1.101 21.757L23.8 12.028 1.101 2.3l.011 7.912 13.623 1.816-13.623 1.817-.011 7.912z"
              />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatWindow;
