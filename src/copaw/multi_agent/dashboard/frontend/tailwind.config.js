/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'apple-gray': '#f5f5f7',
        'apple-dark': '#1d1d1f',
        'apple-secondary': '#86868b',
        'apple-blue': '#007aff',
        'apple-green': '#34c759',
        'apple-orange': '#ff9500',
        'apple-red': '#ff3b30',
        'apple-purple': '#af52de',
        'apple-pink': '#ff2d55',
        'apple-teal': '#5ac8fa',
      },
      borderRadius: {
        'apple': '16px',
        'apple-lg': '24px',
      },
      boxShadow: {
        'apple': '0 4px 12px rgba(0, 0, 0, 0.05)',
        'apple-lg': '0 8px 32px rgba(0, 0, 0, 0.08)',
      },
      backdropBlur: {
        'apple': '20px',
      }
    },
  },
  plugins: [],
}