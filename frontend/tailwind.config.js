const TONES = ["success", "warning", "danger", "info", "neutral"];
const TONE_PROPS = ["bg", "fg", "border"];

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  safelist: TONES.flatMap((tone) =>
    TONE_PROPS.map((prop) =>
      prop === "bg" ? `bg-${tone}-bg` : prop === "fg" ? `text-${tone}-fg` : `border-${tone}-border`
    )
  ),
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        display: ["Fraunces", "Georgia", "serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        // console chrome (dark header/nav)
        console: {
          DEFAULT: "#141A22",
          raised: "#1D2530",
          border: "#2B3542",
          fg: "#EFEBE1",
          muted: "#9AA5B1",
        },
        // warm paper canvas + ink text
        canvas: "#F5F2EA",
        surface: "#FFFFFF",
        ink: "#1C1A14",
        muted: "#6B6355",

        brand: {
          DEFAULT: "#1F6E52",
          dark: "#175841",
          light: "#E6F1EA",
        },

        success: { fg: "#1F6E52", bg: "#E6F1EA", border: "#BEDACA" },
        danger: { fg: "#92352A", bg: "#FBEAE5", border: "#E9BCAF" },
        warning: { fg: "#8A5A12", bg: "#FBF1DE", border: "#EAD2A0" },
        info: { fg: "#1D5B66", bg: "#E8F2F3", border: "#BBDBDF" },
        neutral: { fg: "#6B6355", bg: "#EFEAE0", border: "#E1DACA" },
      },
      boxShadow: {
        soft: "0 1px 2px rgba(28, 26, 20, 0.04), 0 6px 16px -8px rgba(28, 26, 20, 0.08)",
        card: "0 1px 2px rgba(28, 26, 20, 0.05), 0 12px 28px -12px rgba(28, 26, 20, 0.12)",
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.25rem",
      },
      keyframes: {
        "rail-ping": {
          "0%": { transform: "scale(1)", opacity: "0.55" },
          "75%, 100%": { transform: "scale(2.2)", opacity: "0" },
        },
      },
      animation: {
        "rail-ping": "rail-ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite",
      },
    },
  },
  plugins: [],
};
