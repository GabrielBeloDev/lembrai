"use client";

import { useCallback, useState } from "react";
import type { FormEvent } from "react";
import { ApiError } from "@/lib/api";
import type { StoredNote } from "@/lib/types";
import type { AsyncState } from "@/lib/useLazyAsync";
import styles from "./app.module.css";

const EMPTY_NOTE_ERROR = "A nota não pode ficar vazia.";
const ADD_ERROR = "Não foi possível salvar a nota. Tente novamente.";

interface NotesPanelProps {
  state: AsyncState<StoredNote[]>;
  onAdd: (text: string) => Promise<void>;
  onRetry: () => void;
}

function NotesList({
  state,
  onRetry,
}: {
  state: AsyncState<StoredNote[]>;
  onRetry: () => void;
}) {
  if (state.status === "idle" || state.status === "loading") {
    return <p className={styles.hint}>Carregando notas…</p>;
  }
  if (state.status === "error") {
    return (
      <div className={styles.errorBox} role="alert">
        <p>{state.message}</p>
        <button type="button" className={styles.secondaryButton} onClick={onRetry}>
          Tentar de novo
        </button>
      </div>
    );
  }
  if (state.data.length === 0) {
    return (
      <p className={styles.hint}>Nenhuma nota ainda. Adicione a primeira acima.</p>
    );
  }
  return (
    <ul className={styles.list}>
      {state.data.map((note) => (
        <li key={note.id} className={styles.card}>
          {note.text}
        </li>
      ))}
    </ul>
  );
}

export function NotesPanel({ state, onAdd, onRetry }: NotesPanelProps) {
  const [text, setText] = useState("");
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const trimmed = text.trim();
      if (trimmed.length === 0) {
        setAddError(EMPTY_NOTE_ERROR);
        return;
      }
      setAdding(true);
      setAddError(null);
      try {
        await onAdd(trimmed);
        setText("");
      } catch (error) {
        const isEmptyRejection = error instanceof ApiError && error.status === 422;
        setAddError(isEmptyRejection ? EMPTY_NOTE_ERROR : ADD_ERROR);
      } finally {
        setAdding(false);
      }
    },
    [text, onAdd],
  );

  const canSubmit = !adding && text.trim().length > 0;

  return (
    <section className={styles.section} aria-label="Notas">
      <form className={styles.addForm} onSubmit={handleSubmit}>
        <label htmlFor="note-input" className={styles.fieldLabel}>
          Nova nota
        </label>
        <div className={styles.addRow}>
          <input
            id="note-input"
            className={styles.textInput}
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="Escreva uma nota…"
            autoComplete="off"
            disabled={adding}
          />
          <button
            type="submit"
            className={styles.primaryButton}
            disabled={!canSubmit}
          >
            Adicionar
          </button>
        </div>
        {addError !== null && (
          <p className={styles.fieldError} role="alert">
            {addError}
          </p>
        )}
      </form>

      <NotesList state={state} onRetry={onRetry} />
    </section>
  );
}
