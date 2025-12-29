/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          violet: 'rgba(139, 92, 246, 0.5)', 
        }
      },
      backdropBlur: {
        'xl': '24px', /* For that heavy frosted glass look */
      },
      boxShadow: {
        'premium': '0 0 50px -12px rgba(139, 92, 246, 0.25)',
      }
    },
  },
  plugins: [],
};