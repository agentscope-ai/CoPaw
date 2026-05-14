import { useEffect, useState } from "react";

/**
 * Breakpoint (px) below which the UI switches to its mobile layout.
 * Kept in sync with the `@media (max-width: ...)` queries used in
 * `styles/mobile.css` and component-level stylesheets.
 */
export const MOBILE_BREAKPOINT = 768;

/**
 * React hook that returns `true` when the viewport is at or below the
 * mobile breakpoint. Uses matchMedia so it responds to live resizes,
 * rotations, and browser UI collapse/expand without re-renders on every
 * resize event.
 */
export function useIsMobile(breakpoint: number = MOBILE_BREAKPOINT): boolean {
  const getMatch = () =>
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia(`(max-width: ${breakpoint}px)`).matches;

  const [isMobile, setIsMobile] = useState<boolean>(getMatch);

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const mq = window.matchMedia(`(max-width: ${breakpoint}px)`);
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    // Initial sync in case SSR / first paint diverged
    setIsMobile(mq.matches);

    if (mq.addEventListener) {
      mq.addEventListener("change", handler);
      return () => mq.removeEventListener("change", handler);
    }
    // Safari < 14 fallback
    mq.addListener(handler);
    return () => mq.removeListener(handler);
  }, [breakpoint]);

  return isMobile;
}

export default useIsMobile;
