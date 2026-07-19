"use client";

import { useCallback, useState } from "react";
import { deliverReminders, getReminders } from "./api";
import { useLazyAsync } from "./useLazyAsync";

const LOAD_ERROR = "Não foi possível carregar os Lembretes. Tente novamente.";
const DELIVER_ERROR = "Não foi possível verificar os Lembretes vencidos.";

export function useReminders() {
  const { state, setState, load } = useLazyAsync(getReminders, LOAD_ERROR);
  const [delivered, setDelivered] = useState<string[] | null>(null);
  const [delivering, setDelivering] = useState(false);
  const [deliverError, setDeliverError] = useState<string | null>(null);

  const deliver = useCallback(async (): Promise<void> => {
    setDelivering(true);
    setDeliverError(null);
    try {
      try {
        const messages = await deliverReminders();
        setDelivered(messages);
      } catch {
        setDeliverError(DELIVER_ERROR);
        return;
      }
      try {
        setState({ status: "ready", data: await getReminders() });
      } catch {
        // delivery succeeded; a failed reconcile must not surface as an error
      }
    } finally {
      setDelivering(false);
    }
  }, [setState]);

  return { state, load, deliver, delivered, delivering, deliverError };
}
