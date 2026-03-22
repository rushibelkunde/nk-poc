/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./index.html",
  ],
  theme: {
    extend: {
      colors: {
        nkPrimary: "#1E3A8A", // Deep blue
        nkAccent: "#F59E0B",  // Amber
      }
    },
  },
  plugins: [],
}
