export const DEFAULT_MODE = "guarded_smooth";
export const MODEL_MODES = [
  { id: "baseline", label: "Vicuna 7B — базовая", description: "Обычная модель без защитного системного промпта." },
  { id: "guarded", label: "Vicuna Guarded", description: "Модель с защитной системной инструкцией." },
  { id: "guarded_smooth", label: "Vicuna Guarded + SmoothLLM", description: "Дополнительная защита от GCG: пять вариантов запроса. Ответ занимает больше времени." },
];

export function validMode(value) {
  return MODEL_MODES.some((mode) => mode.id === value) ? value : DEFAULT_MODE;
}

export function preferredMode() {
  try {
    return validMode(localStorage.getItem("assistant-model-mode"));
  } catch {
    return DEFAULT_MODE;
  }
}

export function rememberMode(mode) {
  try {
    localStorage.setItem("assistant-model-mode", validMode(mode));
  } catch {
    // The selector still works when browser storage is unavailable.
  }
}
