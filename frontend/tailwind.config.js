/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        main: '#4DDDBD',
        gray2: '#EDEDED',
        gray3: '#C3C3C3',
        gray5: '#9B9B9B',
        gray6: '#F0F1F3',
        gray7: '#555756',
        black: '#1B1B1B',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.3s ease-in-out',
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
};
