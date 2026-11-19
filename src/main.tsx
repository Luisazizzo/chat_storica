import { StrictMode } from "react";
import { createRoot, type RootOptions } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";

const rootElement: HTMLElement | null = document.getElementById("root");
if (!rootElement) {
  throw new Error("Elemento root non trovato nel DOM");
}

const rootOptions: RootOptions = {};

createRoot(rootElement, rootOptions).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
