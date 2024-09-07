module.exports = {
  content: [
    '../../templates/**/*.html', 
    '../../**/templates/**/*.html', 
    '../css/tailwind.css',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'primary': {
          dark: '#0c1322',
          dark_secondary: '#0f172a',
        },
      },
      fontFamily: {
        sans: ['Quicksand', 'sans-serif'],
      },
    }
  },
  plugins: [],
}