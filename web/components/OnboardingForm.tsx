"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import type { OnboardingQuestion } from "@/lib/types";
import styles from "./app.module.css";

interface OnboardingFormProps {
  questions: OnboardingQuestion[];
  submitting: boolean;
  submitError: string | null;
  onSubmit: (answers: string[]) => void;
  onCancel?: () => void;
}

export function OnboardingForm({
  questions,
  submitting,
  submitError,
  onSubmit,
  onCancel,
}: OnboardingFormProps) {
  const [answers, setAnswers] = useState<string[]>(() =>
    questions.map(() => ""),
  );

  const updateAnswer = (index: number, value: string) => {
    setAnswers((previous) =>
      previous.map((answer, position) => (position === index ? value : answer)),
    );
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit(answers);
  };

  const hasAnyAnswer = answers.some((answer) => answer.trim().length > 0);

  return (
    <form className={styles.onboardingForm} onSubmit={handleSubmit}>
      {questions.map((question, index) => {
        const fieldId = `onboarding-${index}`;
        const hintId = `${fieldId}-hint`;
        return (
          <div key={question.title} className={styles.field}>
            <label htmlFor={fieldId} className={styles.fieldLabel}>
              {question.title}
            </label>
            <p id={hintId} className={styles.fieldHint}>
              {question.question}
            </p>
            <input
              id={fieldId}
              className={styles.textInput}
              value={answers[index]}
              onChange={(event) => updateAnswer(index, event.target.value)}
              aria-describedby={hintId}
              autoComplete="off"
              disabled={submitting}
            />
          </div>
        );
      })}

      {submitError !== null && (
        <p className={styles.fieldError} role="alert">
          {submitError}
        </p>
      )}

      <div className={styles.formActions}>
        <button
          type="submit"
          className={styles.primaryButton}
          disabled={submitting || !hasAnyAnswer}
        >
          {submitting ? "Salvando…" : "Salvar Perfil"}
        </button>
        {onCancel && (
          <button
            type="button"
            className={styles.secondaryButton}
            onClick={onCancel}
            disabled={submitting}
          >
            Cancelar
          </button>
        )}
      </div>
    </form>
  );
}
