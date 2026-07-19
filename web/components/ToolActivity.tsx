import type { ToolActivityItem, ToolActivityKind } from "@/lib/types";
import styles from "./chat.module.css";

const VERB_BY_KIND: Record<ToolActivityKind, string> = {
  tool: "chamou",
  tool_result: "resultado de",
  tool_error: "argumentos inválidos para",
};

interface ToolActivityProps {
  items: ToolActivityItem[];
}

export function ToolActivity({ items }: ToolActivityProps) {
  return (
    <ul className={styles.toolActivity} aria-label="Atividade de Ferramentas">
      {items.map((item, index) => (
        <li key={index} className={styles.toolItem}>
          <span className={styles.toolVerb}>{VERB_BY_KIND[item.kind]}</span>{" "}
          <span className={styles.toolName}>{item.name}</span>
          {item.detail !== null && (
            <span className={styles.toolDetail}>: {item.detail}</span>
          )}
        </li>
      ))}
    </ul>
  );
}
