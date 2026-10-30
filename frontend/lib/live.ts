"use client";

import { useEffect, useRef } from "react";
import { subscribeEvents } from "./api";

export function useLiveRefresh(refresh: () => void) {
  const refreshRef = useRef(refresh);
  refreshRef.current = refresh;

  useEffect(() => {
    const controller = new AbortController();
    let poll: number | undefined;
    let stopped = false;

    subscribeEvents(() => refreshRef.current(), controller.signal).catch(() => {
      if (stopped) return;
      poll = window.setInterval(() => refreshRef.current(), 8000);
    });

    return () => {
      stopped = true;
      controller.abort();
      if (poll) window.clearInterval(poll);
    };
  }, []);
}
