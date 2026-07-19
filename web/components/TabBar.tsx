"use client";

import { useCallback } from "react";
import type { KeyboardEvent } from "react";
import styles from "./app.module.css";

export type TabKey = "chat" | "notes" | "reminders" | "profile";

export interface Tab {
  key: TabKey;
  label: string;
}

interface TabBarProps {
  tabs: Tab[];
  activeTab: TabKey;
  onSelect: (tab: TabKey) => void;
}

export function TabBar({ tabs, activeTab, onSelect }: TabBarProps) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLDivElement>) => {
      const currentIndex = tabs.findIndex((tab) => tab.key === activeTab);
      const lastIndex = tabs.length - 1;
      let nextIndex = currentIndex;
      if (event.key === "ArrowRight") {
        nextIndex = currentIndex === lastIndex ? 0 : currentIndex + 1;
      } else if (event.key === "ArrowLeft") {
        nextIndex = currentIndex === 0 ? lastIndex : currentIndex - 1;
      } else if (event.key === "Home") {
        nextIndex = 0;
      } else if (event.key === "End") {
        nextIndex = lastIndex;
      } else {
        return;
      }
      event.preventDefault();
      onSelect(tabs[nextIndex].key);
      const buttons =
        event.currentTarget.querySelectorAll<HTMLButtonElement>('[role="tab"]');
      buttons[nextIndex]?.focus();
    },
    [tabs, activeTab, onSelect],
  );

  return (
    <div
      role="tablist"
      aria-label="Seções"
      className={styles.tabs}
      onKeyDown={handleKeyDown}
    >
      {tabs.map((tab) => {
        const selected = tab.key === activeTab;
        return (
          <button
            key={tab.key}
            type="button"
            role="tab"
            id={`tab-${tab.key}`}
            aria-selected={selected}
            aria-controls={`panel-${tab.key}`}
            tabIndex={selected ? 0 : -1}
            className={selected ? `${styles.tab} ${styles.tabActive}` : styles.tab}
            onClick={() => onSelect(tab.key)}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
