/** Formatta un anno con AC (Avanti Cristo) o DC (Dopo Cristo) */
export const formatAnno = (anno: number): string => {
  if (anno < 0) {
    return `${Math.abs(anno)} AC`;
  }
  return `${anno} DC`;
};

/** Formatta un periodo storico (es. "100 AC - 44 AC") */
export const formatPeriodo = (annoNascita: number, annoMorte: number): string => {
  return `${formatAnno(annoNascita)} - ${formatAnno(annoMorte)}`;
};
