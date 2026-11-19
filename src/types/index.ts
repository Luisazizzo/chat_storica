type PersonaggioId = "cesare" | "leonardo" | "galileo" | "dante" | "napoleone";

export interface Personaggio {
  id: PersonaggioId;
  nome: string;
  anno_nascita: number;
  anno_morte: number;
  ruolo: string;
  stile?: string;
  frase_fuori_epoca?: string;
}

type RuoloMessaggio = "utente" | "assistente" | "sistema";

export interface Messaggio {
  ruolo: RuoloMessaggio;
  testo: string;
  timestamp: string;
}

export interface ChatResponse {
  risposta: string;
  session_id: string;
  guardrail?: boolean;
  eventi?: EventoStorico[];
  fonti?: string[];
  latenza_s?: number;
  costo_usd?: number;
}

export interface EventoStorico {
  nome: string;
  anno: number;
  parole_chiave?: string[];
}

export interface StoricoConversazione {
  history: Messaggio[];
}

export type PersonaggioImages = Record<PersonaggioId, string>;

export interface ContactListProps {
  personaggi: Personaggio[];
  selectedPersonaggio: Personaggio | null;
  onSelectPersonaggio: (personaggio: Personaggio) => void;
}

export interface ChatWindowProps {
  personaggio: Personaggio | null;
  messages: Messaggio[];
  onSendMessage: (testo: string) => void;
  onClearConversation: () => void;
  loading: boolean;
}

export interface MessageProps {
  message: Messaggio;
  isUser: boolean;
}

export interface LightboxProps {
  image: string;
  name: string;
  onClose: () => void;
}
