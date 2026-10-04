import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#172033",
          light: "#2A364F",
        },
        slate: {
          DEFAULT: "#536176",
          light: "#64748B",
          dark: "#334155",
        },
        cloud: {
          DEFAULT: "#F7F9FC",
          subtle: "#F1F5F9",
        },
        surface: {
          DEFAULT: "#FFFFFF",
          muted: "#F8FAFC",
        },
        teal: {
          DEFAULT: "#0F766E",
          hover: "#0D655E",
          soft: "#E6F4F1",
          border: "#99D1C9",
        },
        blue: {
          DEFAULT: "#2563EB",
          soft: "#EFF6FF",
          border: "#BFDBFE",
        },
        amber: {
          DEFAULT: "#B45309",
          soft: "#FEF3C7",
          border: "#FDE68A",
        },
        danger: {
          DEFAULT: "#B42318",
          soft: "#FEE4E2",
          border: "#FECDCA",
        },
        border: {
          DEFAULT: "#E3E8EF",
          subtle: "#EDF2F7",
          strong: "#CBD5E1",
        },
      },
      borderRadius: {
        lg: "10px",
        xl: "12px",
        "2xl": "14px",
      },
      boxShadow: {
        soft: "0 1px 3px 0 rgba(23, 32, 51, 0.05), 0 1px 2px -1px rgba(23, 32, 51, 0.05)",
        "soft-md": "0 4px 6px -1px rgba(23, 32, 51, 0.06), 0 2px 4px -2px rgba(23, 32, 51, 0.04)",
        "soft-lg": "0 10px 15px -3px rgba(23, 32, 51, 0.07), 0 4px 6px -4px rgba(23, 32, 51, 0.04)",
      },
    },
  },
  plugins: [],
};

export default config;
