const { fontFamily } = require('tailwindcss/defaultTheme');

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        clai: {
          bg: '#060b17',
          surface: '#0f172a',
          card: '#111827',
          border: '#1e293b',
          text: '#d6e2f2',
          muted: '#8b9cb8',
          accent: '#22d3ee',
          success: '#34d399',
          warning: '#fbbf24',
          error: '#fb7185',
        },
        agent: {
          senior: '#a78bfa',
          coder: '#60a5fa',
          coder2: '#22d3ee',
          qa: '#34d399',
          ba: '#fbbf24',
          reviewer: '#fb7185',
        },
      },
      fontFamily: {
        sans: ['Space Grotesk', ...fontFamily.sans],
        mono: ['IBM Plex Mono', ...fontFamily.mono],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-up': 'slideUp 0.3s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
      },
      keyframes: {
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
};
