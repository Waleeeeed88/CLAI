const { fontFamily } = require('tailwindcss/defaultTheme');

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        clai: {
          frame: '#020202',
          bg: '#030303',
          shell: '#0a0a0a',
          surface: '#111111',
          panel: '#171717',
          card: '#1e1e1f',
          border: '#2a2a2d',
          text: '#f5f5f7',
          muted: '#a1a1aa',
          accent: '#b8c4ff',
          success: '#d8dbe2',
          warning: '#cbc6bc',
          error: '#ff7b72',
        },
        agent: {
          senior: '#d7dce5',
          coder: '#c6cfde',
          coder2: '#b5c0d1',
          qa: '#d0d6df',
          ba: '#bfc4cd',
          reviewer: '#e1e4ea',
        },
      },
      fontFamily: {
        sans: ['Inter', ...fontFamily.sans],
        mono: ['JetBrains Mono', ...fontFamily.mono],
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
