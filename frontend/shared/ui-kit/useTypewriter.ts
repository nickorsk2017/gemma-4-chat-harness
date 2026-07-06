"use client";

import { useEffect, useState } from "react";

const TICK_MS = 24;
/** Target full-reveal duration bounds (ms) — long replies speed up, short stay readable. */
const MIN_DURATION_MS = 400;
const MAX_DURATION_MS = 4000;
const MS_PER_CHAR = 18;

function charsPerTick(length: number): number {
  const duration = Math.min(
    MAX_DURATION_MS,
    Math.max(MIN_DURATION_MS, length * MS_PER_CHAR),
  );
  return Math.max(1, Math.ceil((length * TICK_MS) / duration));
}

/**
 * ChatGPT-style typewriter reveal. Returns the currently visible prefix of
 * `text` and a `done` flag. When `enabled` is false the full text is returned
 * immediately. Pure presentation logic — no store/service access.
 */
export function useTypewriter(text: string, enabled: boolean) {
  const [count, setCount] = useState(() => (enabled ? 0 : text.length));

  useEffect(() => {
    if (!enabled) {
      setCount(text.length);
      return;
    }
    setCount(0);
    const step = charsPerTick(text.length);
    const timer = setInterval(() => {
      setCount((prev) => {
        const next = prev + step;
        if (next >= text.length) {
          clearInterval(timer);
          return text.length;
        }
        return next;
      });
    }, TICK_MS);
    return () => clearInterval(timer);
  }, [text, enabled]);

  const done = count >= text.length;
  return { visible: done ? text : text.slice(0, count), done };
}
