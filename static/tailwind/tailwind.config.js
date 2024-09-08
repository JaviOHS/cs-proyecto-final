module.exports = {
  content: [
    '../../templates/**/*.html', 
    '../../**/templates/**/*.html', 
    '../css/tailwind.css',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Quicksand', 'sans-serif'],
      },
    }
  },
  plugins: [],
}