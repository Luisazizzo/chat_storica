import "./ContactList.css";
import { formatPeriodo } from "../utils/dateUtils";
import cesareLogo from "../assets/giulio_cesare.jpg";
import leonardoLogo from "../assets/leonardo_da_vinci.jpg";
import galileoLogo from "../assets/galileo_galilei.jpg";
import danteLogo from "../assets/dante_alighieri.jpg";
import napoleoneLogo from "../assets/napoleone_buonaparte.jpg";
import type { ContactListProps, PersonaggioImages } from "../types";

const personaggioImages: PersonaggioImages = {
  cesare: cesareLogo,
  leonardo: leonardoLogo,
  galileo: galileoLogo,
  dante: danteLogo,
  napoleone: napoleoneLogo,
};

const ContactList = ({
  personaggi,
  selectedPersonaggio,
  onSelectPersonaggio,
}: ContactListProps): React.JSX.Element => {
  if (!personaggi || personaggi.length === 0) {
    return (
      <div className="contact-list">
        <div className="contact-list-header">
          <h2>Personaggi Storici</h2>
        </div>
        <div className="contacts">
          <div
            style={{ padding: "20px", textAlign: "center", color: "#667781" }}
          >
            Caricamento personaggi...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="contact-list">
      <div className="contact-list-header">
        <h2>Personaggi Storici</h2>
      </div>
      <div className="contacts">
        {personaggi.map((personaggio) => {
          const periodo = formatPeriodo(
            personaggio.anno_nascita,
            personaggio.anno_morte,
          );

          return (
            <div
              key={personaggio.id}
              className={`contact ${selectedPersonaggio?.id === personaggio.id ? "active" : ""}`}
              onClick={() => onSelectPersonaggio(personaggio)}
            >
              <div className="contact-avatar">
                <img
                  src={personaggioImages[personaggio.id]}
                  alt={personaggio.nome}
                />
              </div>
              <div className="contact-info">
                <div className="contact-name">{personaggio.nome}</div>
                <div className="contact-period">{periodo}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ContactList;
