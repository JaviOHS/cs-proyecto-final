module.exports = {
  mode: 'jit',
  content: [
    '../../templates/**/*.html',
    '../../app/**/templates/*.html',
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
