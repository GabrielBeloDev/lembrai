import type { KeyboardEvent } from "react";
import styles from "./chat.module.css";

interface ComposerProps {
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
  onSend: () => void;
}

export function Composer({ value, disabled, onChange, onSend }: ComposerProps) {
  const hasContent = value.trim().length > 0;

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    const isPlainEnter = event.key === "Enter" && !event.shiftKey;
    if (!isPlainEnter) return;
    event.preventDefault();
    onSend();
  };

  return (
    <form
      className={styles.composer}
      onSubmit={(event) => {
        event.preventDefault();
        onSend();
      }}
    >
      <label htmlFor="chat-input" className={styles.visuallyHidden}>
        Mensagem para o Assistente
      </label>
      <textarea
        id="chat-input"
        className={styles.input}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Escreva sua mensagem…"
        rows={1}
        disabled={disabled}
        autoComplete="off"
      />
      <button
        type="submit"
        className={styles.send}
        disabled={disabled || !hasContent}
      >
        Enviar
      </button>
    </form>
  );
}
