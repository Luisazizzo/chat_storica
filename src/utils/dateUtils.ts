/**
 * Formatta un anno con AC (Avanti Cristo) o DC (Dopo Cristo)
 * @param anno - Anno in formato numerico (negativo = AC, positivo = DC)
 * @returns Stringa formattata (es. "44 AC", "1452 DC")
 */
export const formatAnno = (anno: number): string => {
  if (anno < 0) {
    return `${Math.abs(anno)} AC`;
  }
  return `${anno} DC`;
};

/**
 * Formatta un periodo storico
 * @param annoNascita - Anno di nascita (negativo per AC)
 * @param annoMorte - Anno di morte (negativo per AC)
 * @returns Stringa formattata (es. "100 AC - 44 AC")
 */
export const formatPeriodo = (annoNascita: number, annoMorte: number): string => {
  return `${formatAnno(annoNascita)} - ${formatAnno(annoMorte)}`;
};
