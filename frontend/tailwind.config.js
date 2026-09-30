/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'corporate-blue': '#1e3a8a',
        'corporate-light-blue': '#3b82f6',
        'slate-gray': '#64748b',
        'slate-dark': '#0f172a',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
