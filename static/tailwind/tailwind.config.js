module.exports = {
  content: [
    '../../templates/**/*.html', 
    '../../**/templates/**/*.html', 
    '../../**/*.html',
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