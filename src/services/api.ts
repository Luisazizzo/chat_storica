import axios, { type AxiosResponse } from "axios";
import type { ChatResponse, Personaggio } from "../types";

const API_BASE_URL = "http://localhost:8000/api";

/** Corpo della richiesta POST /chat */
interface ChatRequestBody {
  session_id: string;
  personaggio_id: string;
  messaggio: string;
}

/**
 * Verifica se il backend ha finito l'inizializzazione.
 * GET /api/health — ritorna 200 quando pronto, 503 se ancora in avvio.
 * @returns true se il backend è pronto, false altrimenti
 */
export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const response: AxiosResponse<{ status: string; ready: boolean }> =
      await axios.get(`${API_BASE_URL}/health`, { timeout: 3000 });
    return response.data.ready === true;
  } catch {
    return false;
  }
};

/**
 * Attende che il backend sia pronto, polledando l'health endpoint.
 * @param maxAttempts - Numero massimo di tentativi
 * @param intervalMs - Intervallo tra tentativi in millisecondi
 * @param onRetry - Callback opzionale chiamato ad ogni tentativo fallito
 * @returns true se il backend è pronto, false se i tentativi sono esauriti
 */
export const waitForBackend = async (
  maxAttempts: number = 60,
  intervalMs: number = 2000,
  onRetry?: (attempt: number, max: number) => void,
): Promise<boolean> => {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const ready = await checkBackendHealth();
    if (ready) return true;
    onRetry?.(attempt, maxAttempts);
    if (attempt < maxAttempts) {
      await new Promise((resolve) => setTimeout(resolve, intervalMs));
    }
  }
  return false;
};

/**
 * Ottieni la lista dei personaggi storici dal backend.
 * GET /api/personaggi
 * @returns Array di personaggi
 */
export const getPersonaggi = async (): Promise<Personaggio[]> => {
  try {
    const response: AxiosResponse<Personaggio[]> = await axios.get(
      `${API_BASE_URL}/personaggi`,
    );
    return response.data;
  } catch (error) {
    console.error("Errore nel recupero personaggi:", error);
    throw error;
  }
};

/**
 * Invia un messaggio al backend e ottieni la risposta del personaggio.
 * POST /api/chat
 * @param sessionId - ID della sessione di conversazione
 * @param personaggioId - ID del personaggio selezionato
 * @param messaggio - Testo del messaggio dell'utente
 * @returns Risposta del backend con la risposta del personaggio
 */
export const sendMessage = async (
  sessionId: string,
  personaggioId: string,
  messaggio: string,
): Promise<ChatResponse> => {
  try {
    const body: ChatRequestBody = {
      session_id: sessionId,
      personaggio_id: personaggioId,
      messaggio: messaggio,
    };
    const response: AxiosResponse<ChatResponse> = await axios.post(
      `${API_BASE_URL}/chat`,
      body,
    );
    return response.data;
  } catch (error) {
    console.error("Errore nell'invio messaggio:", error);
    throw error;
  }
};

/** Formato dello storico dal backend (prima della conversione in Messaggio) */
interface BackendHistoryEntry {
  role: string;
  content: string;
}

interface BackendHistoryResponse {
  session_id: string;
  personaggio_id?: string;
  history: BackendHistoryEntry[];
}

/**
 * Ottieni lo storico della conversazione per una sessione.
 * GET /api/history/{session_id}?personaggio_id={id}
 * @param sessionId - ID della sessione di conversazione
 * @param personaggioId - ID del personaggio (opzionale, filtra per personaggio)
 * @returns Array di messaggi dello storico in formato backend ({role, content})
 */
export const getHistory = async (
  sessionId: string,
  personaggioId?: string,
): Promise<BackendHistoryEntry[]> => {
  try {
    const params = personaggioId ? { personaggio_id: personaggioId } : undefined;
    const response: AxiosResponse<BackendHistoryResponse> = await axios.get(
      `${API_BASE_URL}/history/${sessionId}`,
      { params },
    );
    return response.data.history;
  } catch (error) {
    console.error("Errore nel recupero storico:", error);
    throw error;
  }
};

/**
 * Cancella lo storico della conversazione per una sessione.
 * DELETE /api/history/{session_id}?personaggio_id={id}
 * @param sessionId - ID della sessione di conversazione
 * @param personaggioId - ID del personaggio (opzionale, cancella solo quello)
 */
export const clearHistory = async (
  sessionId: string,
  personaggioId?: string,
): Promise<void> => {
  try {
    const params = personaggioId ? { personaggio_id: personaggioId } : undefined;
    await axios.delete(`${API_BASE_URL}/history/${sessionId}`, { params });
  } catch (error) {
    console.error("Errore nella cancellazione storico:", error);
    throw error;
  }
};
