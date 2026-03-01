/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        nu: {
          purple: "#4E2A84",
          "purple-dark": "#401F6E",
          "purple-light": "#7B5EA7",
          "purple-faint": "#F3EFF8",
        },
      },
    },
  },
  plugins: [],
};
