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
      colors: {
        // Orange theme colors
        'theme1': {
          100: '#fff7ed', // Lightest
          200: '#ffedd5',
          300: '#fed7aa',
          400: '#fdba74',
          500: '#f97316', // Base
          600: '#ea580c',
          700: '#c2410c',
          800: '#9a3412',
          900: '#7c2d12', // Darkest
        },
        // Blue theme colors
        'theme2': {
          100: '#e0f2fe', // Lightest
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9', // Base
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e', // Darkest
        }
      },
      // Add theme-specific background colors
      backgroundColor: theme => ({
        ...theme('colors'),
      }),
      // Add theme-specific text colors
      textColor: theme => ({
        ...theme('colors'),
      }),
      // Add theme-specific border colors
      borderColor: theme => ({
        ...theme('colors'),
      }),
    }
  },
  plugins: [],
}