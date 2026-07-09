/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f2f1fc",
          100: "#e5e3f9",
          200: "#c9c5f2",
          300: "#a49ce8",
          400: "#8074dc",
          500: "#6255cf",
          600: "#4f3fb8",
          700: "#413495",
          800: "#362c78",
          900: "#2d2662",
          950: "#1b1740",
        },
        ink: {
          50: "#f6f7f8",
          100: "#eceef0",
          200: "#d5d9de",
          300: "#b1b9c2",
          400: "#8793a1",
          500: "#697585",
          600: "#545e6d",
          700: "#454d59",
          800: "#3b414b",
          900: "#1f2329",
          950: "#131519",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
