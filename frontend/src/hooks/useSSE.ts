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
          onEvent(event);

          if (event.type === "done" || event.type === "error") {
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
          onEvent({
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
  }, [sessionId, onEvent]);
}
