"use client";

import { useCallback, useState } from "react";
import { useNotes } from "@/lib/useNotes";
import { useProfile } from "@/lib/useProfile";
import { useReminders } from "@/lib/useReminders";
import { Chat } from "./Chat";
import { NotesPanel } from "./NotesPanel";
import { ProfilePanel } from "./ProfilePanel";
import { RemindersPanel } from "./RemindersPanel";
import { TabBar } from "./TabBar";
import type { Tab, TabKey } from "./TabBar";
import styles from "./app.module.css";

const TABS: Tab[] = [
  { key: "chat", label: "Chat" },
  { key: "notes", label: "Notas" },
  { key: "reminders", label: "Lembretes" },
  { key: "profile", label: "Perfil" },
];

export function AssistantApp() {
  const [activeTab, setActiveTab] = useState<TabKey>("chat");
  const notes = useNotes();
  const reminders = useReminders();
  const profile = useProfile();

  const loadNotes = notes.load;
  const loadReminders = reminders.load;
  const loadProfile = profile.load;

  const handleSelect = useCallback(
    (tab: TabKey) => {
      setActiveTab(tab);
      if (tab === "notes") void loadNotes();
      else if (tab === "reminders") void loadReminders();
      else if (tab === "profile") void loadProfile();
    },
    [loadNotes, loadReminders, loadProfile],
  );

  return (
    <div className={styles.app}>
      <header className={styles.topbar}>
        <h1 className={styles.brand}>lembrai</h1>
        <TabBar tabs={TABS} activeTab={activeTab} onSelect={handleSelect} />
      </header>

      <main className={styles.panelArea}>
        <div
          role="tabpanel"
          id="panel-chat"
          aria-labelledby="tab-chat"
          className={styles.chatPanel}
          hidden={activeTab !== "chat"}
        >
          <Chat />
        </div>

        <div
          role="tabpanel"
          id="panel-notes"
          aria-labelledby="tab-notes"
          className={styles.tabpanel}
          hidden={activeTab !== "notes"}
          tabIndex={0}
        >
          <NotesPanel state={notes.state} onAdd={notes.add} onRetry={loadNotes} />
        </div>

        <div
          role="tabpanel"
          id="panel-reminders"
          aria-labelledby="tab-reminders"
          className={styles.tabpanel}
          hidden={activeTab !== "reminders"}
          tabIndex={0}
        >
          <RemindersPanel
            state={reminders.state}
            delivered={reminders.delivered}
            delivering={reminders.delivering}
            deliverError={reminders.deliverError}
            onDeliver={reminders.deliver}
            onRetry={loadReminders}
          />
        </div>

        <div
          role="tabpanel"
          id="panel-profile"
          aria-labelledby="tab-profile"
          className={styles.tabpanel}
          hidden={activeTab !== "profile"}
          tabIndex={0}
        >
          <ProfilePanel
            state={profile.state}
            submitting={profile.submitting}
            submitError={profile.submitError}
            onSubmit={profile.submit}
            onRetry={loadProfile}
          />
        </div>
      </main>
    </div>
  );
}
