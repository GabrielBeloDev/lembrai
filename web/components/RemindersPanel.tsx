"use client";

import type { Reminder } from "@/lib/types";
import type { AsyncState } from "@/lib/useLazyAsync";
import styles from "./app.module.css";

const DATE_FORMAT = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "medium",
  timeStyle: "short",
});

function formatDue(due: string): string {
  const date = new Date(due);
  return Number.isNaN(date.getTime()) ? due : DATE_FORMAT.format(date);
}

interface RemindersPanelProps {
  state: AsyncState<Reminder[]>;
  delivered: string[] | null;
  delivering: boolean;
  deliverError: string | null;
  onDeliver: () => void;
  onRetry: () => void;
}

function RemindersList({
  state,
  onRetry,
}: {
  state: AsyncState<Reminder[]>;
  onRetry: () => void;
}) {
  if (state.status === "idle" || state.status === "loading") {
    return <p className={styles.hint}>Carregando lembretes…</p>;
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
    return <p className={styles.hint}>Nenhum lembrete ainda.</p>;
  }
  return (
    <ul className={styles.list}>
      {state.data.map((reminder) => (
        <li key={reminder.id} className={styles.reminderCard}>
          <p className={styles.reminderMessage}>{reminder.message}</p>
          <div className={styles.reminderMeta}>
            <time dateTime={reminder.due}>{formatDue(reminder.due)}</time>
            <span
              className={
                reminder.delivered ? styles.badgeDelivered : styles.badgePending
              }
            >
              {reminder.delivered ? "Entregue" : "Pendente"}
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}

export function RemindersPanel({
  state,
  delivered,
  delivering,
  deliverError,
  onDeliver,
  onRetry,
}: RemindersPanelProps) {
  return (
    <section className={styles.section} aria-label="Lembretes">
      <div className={styles.toolbar}>
        <button
          type="button"
          className={styles.primaryButton}
          onClick={onDeliver}
          disabled={delivering}
        >
          {delivering ? "Verificando…" : "Verificar vencidos"}
        </button>
      </div>

      {deliverError !== null && (
        <p className={styles.fieldError} role="alert">
          {deliverError}
        </p>
      )}

      {delivered !== null && (
        <div className={styles.deliveredBox} role="status">
          {delivered.length === 0 ? (
            <p>Nenhum lembrete vencido.</p>
          ) : (
            <>
              <p className={styles.deliveredTitle}>Entregues agora</p>
              <ul className={styles.list}>
                {delivered.map((message, index) => (
                  <li key={index} className={styles.card}>
                    {message}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      <RemindersList state={state} onRetry={onRetry} />
    </section>
  );
}
