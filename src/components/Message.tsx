import "./Message.css";
import type { MessageProps } from "../types";

const Message = ({ message, isUser }: MessageProps): React.JSX.Element => {
  const formatTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("it-IT", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className={`message ${isUser ? "user" : "ai"}`}>
      <div className="message-bubble">
        <div className="message-text">{message.testo}</div>
        <div className="message-time">{formatTime(message.timestamp)}</div>
      </div>
    </div>
  );
};

export default Message;
