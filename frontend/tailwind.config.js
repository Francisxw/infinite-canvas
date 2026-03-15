/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'canvas-bg': '#0f0f0f',
        'node-bg': '#1a1a1a',
        'node-border': '#2a2a2a',
        'accent': '#3b82f6',
      },
    },
  },
  plugins: [],
}
