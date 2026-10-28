import { useId } from "react";
import { MODEL_MODES } from "../lib/modelModes";

export default function ModelSelector({ value, onChange, disabled }) {
  const id = useId();
  const selected = MODEL_MODES.find((mode) => mode.id === value);
  return (
    <div className="model-selector">
      <label htmlFor={id}>Модель и защита</label>
      <select id={id} value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)} aria-describedby={`${id}-hint`}>
        {MODEL_MODES.map((mode) => <option key={mode.id} value={mode.id}>{mode.label}</option>)}
      </select>
      <p id={`${id}-hint`}>{selected?.description} Смена модели начинает новый чат.</p>
    </div>
  );
}
