import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: { extend: { colors: { ink: "#0b2149", line: "#cdd9e9" } } },
  plugins: [],
} satisfies Config;
