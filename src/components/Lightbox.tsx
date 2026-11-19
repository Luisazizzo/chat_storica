import "./Lightbox.css";
import type { LightboxProps } from "../types";

const Lightbox = ({ image, name, onClose }: LightboxProps): React.JSX.Element => {
  return (
    <div className="lightbox-overlay" onClick={onClose}>
      <div className="lightbox-content" onClick={(e: React.MouseEvent<HTMLDivElement>) => e.stopPropagation()}>
        <button className="lightbox-close" onClick={onClose}>
          ✕
        </button>
        <img src={image} alt={name} />
        <div className="lightbox-caption">{name}</div>
      </div>
    </div>
  );
};

export default Lightbox;
