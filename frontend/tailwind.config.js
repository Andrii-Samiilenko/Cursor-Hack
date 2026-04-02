/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["\"DM Sans\"", "system-ui", "sans-serif"],
        mono: ["\"JetBrains Mono\"", "ui-monospace", "monospace"],
      },
      colors: {
        surface: {
          900: "#0c0f14",
          800: "#121822",
          700: "#1a2230",
          600: "#243044",
        },
        accent: {
          DEFAULT: "#3dd6c6",
          dim: "#2a9d8f",
          glow: "#5eead4",
        },
      },
      boxShadow: {
        card: "0 0 0 1px rgba(61, 214, 198, 0.08), 0 12px 40px rgba(0, 0, 0, 0.45)",
      },
    },
  },
  plugins: [],
};
