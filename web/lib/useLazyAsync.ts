"use client";

import { useCallback, useRef, useState } from "react";
import type { Dispatch, SetStateAction } from "react";

export type AsyncState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; data: T }
  | { status: "error"; message: string };

interface LazyAsync<T> {
  state: AsyncState<T>;
  setState: Dispatch<SetStateAction<AsyncState<T>>>;
  load: () => Promise<void>;
}

export function useLazyAsync<T>(
  fetcher: () => Promise<T>,
  errorMessage: string,
): LazyAsync<T> {
  const [state, setState] = useState<AsyncState<T>>({ status: "idle" });
  const hasLoaded = useRef(false);

  const load = useCallback(async () => {
    if (hasLoaded.current) return;
    hasLoaded.current = true;
    setState({ status: "loading" });
    try {
      const data = await fetcher();
      setState({ status: "ready", data });
    } catch {
      // let the panel offer a retry: the next load() must run again
      hasLoaded.current = false;
      setState({ status: "error", message: errorMessage });
    }
  }, [fetcher, errorMessage]);

  return { state, setState, load };
}
