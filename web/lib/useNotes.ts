"use client";

import { useCallback } from "react";
import { getNotes, postNote } from "./api";
import type { StoredNote } from "./types";
import { useLazyAsync } from "./useLazyAsync";

const LOAD_ERROR = "Não foi possível carregar as Notas. Tente novamente.";

export function useNotes() {
  const { state, setState, load } = useLazyAsync(getNotes, LOAD_ERROR);

  const add = useCallback(
    async (text: string): Promise<void> => {
      const optimistic: StoredNote = { id: `pending-${Date.now()}`, text };
      setState((previous) =>
        previous.status === "ready"
          ? { status: "ready", data: [optimistic, ...previous.data] }
          : previous,
      );
      try {
        await postNote(text);
      } catch (error) {
        setState((previous) =>
          previous.status === "ready"
            ? {
                status: "ready",
                data: previous.data.filter((note) => note.id !== optimistic.id),
              }
            : previous,
        );
        throw error;
      }
      try {
        setState({ status: "ready", data: await getNotes() });
      } catch {
        // the note is already persisted; a failed reconcile must not surface
        // as an error, so keep the optimistic entry on screen
      }
    },
    [setState],
  );

  return { state, load, add };
}
