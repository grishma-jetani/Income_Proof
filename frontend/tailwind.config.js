/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        cream: '#FAF9F6',
        forest: {
          DEFAULT: '#2D4A43',
          dark: '#1F3530',
          light: '#3E635B',
        },
        gold: {
          DEFAULT: '#C8A560',
          light: '#E3D2AC',
        },
        ink: '#1F2A27',
        slate: '#6B7280',
        sage: '#5B8A72',
        rust: '#C2654A',
        border: '#E8E5DE',
      },
      fontFamily: {
        display: ['Fraunces', 'serif'],
        sans: ['Inter', 'sans-serif'],
      },
      borderRadius: {
        xl: '1rem',
        '2xl': '1.25rem',
      },
      boxShadow: {
        card: '0 2px 12px rgba(31, 42, 39, 0.06)',
        cardHover: '0 4px 20px rgba(31, 42, 39, 0.10)',
      },
    },
  },
  plugins: [],
}