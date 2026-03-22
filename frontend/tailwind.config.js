/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./index.html",
  ],
  theme: {
    extend: {
      colors: {
        nkPrimary: "#0e1117", // Main background
        nkCard: "#262730",    // Card background
        nkAccent: "#ff4b4b",  // Streamlit red
        nkHighlight: "#f97316", // Streamlit-style orange/amber
        nkText: "#fafafa",    // Main text
        nkBorder: "rgba(250, 250, 250, 0.1)", // Subtle white border
      }
    },
  },
  plugins: [],
}
