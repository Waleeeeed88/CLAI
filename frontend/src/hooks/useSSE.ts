"use client";
import { useEffect, useRef } from "react";
import { getStreamUrl } from "../lib/api";
import { SSEEvent } from "../lib/types";

const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1500;

export function useSSE(
  sessionId: string | null,
  onEvent: (event: SSEEvent) => void,
) {
  const retriesRef = useRef(0);
  // Keep a stable ref to onEvent so the effect doesn't re-run when the
  // callback identity changes (zustand store functions change every render).
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!sessionId) return;
    retriesRef.current = 0;

    let es: EventSource | null = null;
    let closed = false;

    function connect() {
      if (closed) return;

      es = new EventSource(getStreamUrl(sessionId!));

      es.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data) as SSEEvent;
          retriesRef.current = 0;
          onEventRef.current(event);

          // Only close on terminal "done" — errors from backend may be
          // per-agent and the pipeline can continue after them.
          if (event.type === "done") {
            es?.close();
          }
        } catch {
          // malformed event — ignore
        }
      };

      es.onerror = () => {
        es?.close();
        if (closed) return;
        if (retriesRef.current < MAX_RETRIES) {
          retriesRef.current += 1;
          setTimeout(connect, RETRY_DELAY_MS * retriesRef.current);
        } else {
          onEventRef.current({
            type: "error",
            message: "Lost connection to server",
          } as SSEEvent);
        }
      };
    }

    connect();

    return () => {
      closed = true;
      es?.close();
    };
  }, [sessionId]); // Only re-run when sessionId changes
}
