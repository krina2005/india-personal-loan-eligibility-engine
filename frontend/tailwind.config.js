/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: { DEFAULT: "#FBF8F3", deep: "#F2EDE4" },
        ink: { DEFAULT: "#0E2A25", soft: "#3C524D", mute: "#6B7F7A" },
        line: "#E3DDD1",
        brand: { DEFAULT: "#0B8F6D", dark: "#07705A", tint: "#E3F4EE" },
        amber2: { DEFAULT: "#9A6200", tint: "#FBF0D9" },
        rose2: { DEFAULT: "#B4382F", tint: "#FBE6E3" },
        sky2: { DEFAULT: "#2F5F8F", tint: "#E5EEF7" },
      },
      fontFamily: { display: ["Fraunces", "Georgia", "serif"], sans: ["Inter", "system-ui", "sans-serif"] },
      borderRadius: { xl2: "14px" },
      boxShadow: { card: "0 1px 0 rgba(14,42,37,.04), 0 6px 18px -10px rgba(14,42,37,.18)" },
    },
  },
  plugins: [],
};
