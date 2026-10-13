"use client";

import Script from "next/script";

// Runs before hydration so the stored theme and language are applied on the
// first paint: `theme` is "light" | "dark" | "system" (absent or "system"
// follows the OS), `lang` is "en" | "zh". localStorage wins in both cases;
// only a first-time visitor gets the OS/browser preference.
const THEME_INIT = `(function () {
  try {
    var stored = localStorage.getItem("theme");
    var systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    var isDark = stored === "dark" ? true : stored === "light" ? false : systemDark;
    document.documentElement.classList.toggle("dark", isDark);

    var lang = localStorage.getItem("lang");
    if (lang !== "en" && lang !== "zh") {
      lang = (navigator.language || "").toLowerCase().indexOf("zh") === 0 ? "zh" : "en";
    }
    document.documentElement.lang = lang;
  } catch (e) {}
})();`;

export function ThemeInit() {
  return (
    <Script id="theme-init" strategy="beforeInteractive">
      {THEME_INIT}
    </Script>
  );
}
