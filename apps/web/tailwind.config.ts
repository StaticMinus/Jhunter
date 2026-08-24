import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#080B11",
        surface: {
          DEFAULT: "rgba(17, 24, 39, 0.70)",
          hover: "rgba(30, 41, 59, 0.85)",
          border: "rgba(255, 255, 255, 0.08)",
          glow: "rgba(6, 182, 212, 0.35)",
        },
        cyan: {
          brand: "#06B6D4",
          glow: "rgba(6, 182, 212, 0.25)",
        },
        emerald: {
          match: "#10B981",
          glow: "rgba(16, 185, 129, 0.25)",
        },
        amber: {
          opp: "#F59E0B",
          glow: "rgba(245, 158, 11, 0.25)",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        heading: ["Outfit", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "float": "float 6s ease-in-out infinite",
        "radar-sweep": "sweep 3s linear infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-8px)" },
        },
        sweep: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
      },
      backdropBlur: {
        xs: "2px",
        md: "12px",
        lg: "20px",
        xl: "32px",
      },
    },
  },
  plugins: [],
} satisfies Config;
