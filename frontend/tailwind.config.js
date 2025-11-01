export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: { 200:'#BBDEFB', 500:'#42A5F5', 900:'#1565C0' }
      },
      fontFamily: {
        sans: ['Evolventa', 'system-ui', 'ui-sans-serif', 'Arial', 'sans-serif']
      },
      boxShadow: { card: '0 6px 20px rgba(0,0,0,.12)' },
      borderRadius: { xl2: '1rem' }
    }
  },
  plugins: []
};
