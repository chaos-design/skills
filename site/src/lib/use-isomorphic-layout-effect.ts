import { useEffect, useLayoutEffect } from "react";

/**
 * `useLayoutEffect` on the client, `useEffect` on the server.
 *
 * Used where a stored preference (language, theme) has to be applied before
 * the browser paints: a passive effect runs after the first paint, so the
 * visitor would see the default for one frame. Layout effects run in the same
 * commit as hydration, so the swap happens before anything is drawn — and the
 * first render still matches the server HTML, so hydration stays clean.
 */
export const useIsomorphicLayoutEffect =
  typeof window !== "undefined" ? useLayoutEffect : useEffect;
