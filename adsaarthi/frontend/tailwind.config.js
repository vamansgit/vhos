/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eefdf5",
          100: "#d6f9e5",
          200: "#b0f0cd",
          300: "#7ce2ae",
          400: "#43cd8c",
          500: "#1eb371",
          600: "#13915b",
          700: "#12744b",
          800: "#125c3e",
          900: "#114c34",
          950: "#062a1d",
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
