"use client";

import { useCallback, useState } from "react";
import { getProfile, getQuestions, postProfile } from "./api";
import type { OnboardingQuestion, Profile } from "./types";
import { useLazyAsync } from "./useLazyAsync";

const LOAD_ERROR = "Não foi possível carregar o Perfil. Tente novamente.";
const SUBMIT_ERROR = "Não foi possível salvar o Perfil. Tente novamente.";

export interface ProfileData {
  profile: Profile;
  questions: OnboardingQuestion[];
}

async function loadProfileData(): Promise<ProfileData> {
  const [profile, questions] = await Promise.all([getProfile(), getQuestions()]);
  return { profile, questions };
}

export function useProfile() {
  const { state, setState, load } = useLazyAsync(loadProfileData, LOAD_ERROR);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const submit = useCallback(
    async (answers: string[]): Promise<boolean> => {
      setSubmitting(true);
      setSubmitError(null);
      try {
        const profile = await postProfile(answers);
        setState((previous) =>
          previous.status === "ready"
            ? { status: "ready", data: { ...previous.data, profile } }
            : previous,
        );
        return true;
      } catch {
        setSubmitError(SUBMIT_ERROR);
        return false;
      } finally {
        setSubmitting(false);
      }
    },
    [setState],
  );

  return { state, load, submit, submitting, submitError };
}
