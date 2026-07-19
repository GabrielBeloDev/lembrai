import type { Role } from "@/lib/types";
import styles from "./chat.module.css";

interface MessageBubbleProps {
  role: Role;
  content: string;
  pending?: boolean;
}

export function MessageBubble({ role, content, pending = false }: MessageBubbleProps) {
  const isUser = role === "user";
  const rowClass = isUser ? styles.rowUser : styles.rowAssistant;
  const bubbleClass = isUser ? styles.userBubble : styles.assistantBubble;
  const sender = isUser ? "Você" : "Assistente";

  return (
    <div className={`${styles.row} ${rowClass}`}>
      <div className={bubbleClass}>
        <span className={styles.sender}>{sender}</span>
        <p className={styles.content}>
          {content}
          {pending && <span className={styles.cursor} aria-hidden="true" />}
        </p>
      </div>
    </div>
  );
}
