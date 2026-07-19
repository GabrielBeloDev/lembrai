"use client";

import { useState } from "react";
import type { AsyncState } from "@/lib/useLazyAsync";
import type { ProfileData } from "@/lib/useProfile";
import { OnboardingForm } from "./OnboardingForm";
import styles from "./app.module.css";

interface ProfilePanelProps {
  state: AsyncState<ProfileData>;
  submitting: boolean;
  submitError: string | null;
  onSubmit: (answers: string[]) => Promise<boolean>;
  onRetry: () => void;
}

export function ProfilePanel({
  state,
  submitting,
  submitError,
  onSubmit,
  onRetry,
}: ProfilePanelProps) {
  const [editing, setEditing] = useState(false);

  if (state.status === "idle" || state.status === "loading") {
    return <p className={styles.hint}>Carregando perfil…</p>;
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

  const { profile, questions } = state.data;
  const hasProfile = profile.content !== null;
  const showForm = !hasProfile || editing;

  const handleSubmit = async (answers: string[]) => {
    const saved = await onSubmit(answers);
    if (saved) setEditing(false);
  };

  return (
    <section className={styles.section} aria-label="Perfil">
      {!hasProfile && (
        <p className={styles.hint}>
          Você ainda não tem um Perfil. Responda às perguntas abaixo para o
          Assistente te conhecer melhor.
        </p>
      )}

      {showForm ? (
        <OnboardingForm
          questions={questions}
          submitting={submitting}
          submitError={submitError}
          onSubmit={handleSubmit}
          onCancel={hasProfile ? () => setEditing(false) : undefined}
        />
      ) : (
        <>
          <article className={styles.profileContent}>{profile.content}</article>
          <button
            type="button"
            className={styles.secondaryButton}
            onClick={() => setEditing(true)}
          >
            Editar Perfil
          </button>
        </>
      )}
    </section>
  );
}
