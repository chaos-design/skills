"use client";

import Script from "next/script";

// Runs before hydration so the stored theme and language are applied on the
// first paint: `theme` is "light" | "dark" | "system", `lang` is "en" | "zh".
// localStorage wins; a first-time visitor (no stored choice) gets the dark
// palette, and an explicit "system" choice keeps following the OS.
const THEME_INIT = `(function () {
  try {
    var stored = localStorage.getItem("theme");
    var systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    var isDark = stored === "light" ? false : stored === "system" ? systemDark : true;
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
