import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        canvas: 'var(--bg-canvas, #f5f5f7)',
        surface: 'var(--bg-surface, #ffffff)',
        'text-primary': 'var(--text-primary, #000000)',
        'text-secondary': 'var(--text-secondary, #86868b)',
        'text-body-secondary': 'var(--text-body-secondary, #6e6e73)',
        'text-tertiary': 'var(--text-body-secondary, #6e6e73)',
        'accent-action': 'var(--accent-action, #0071e3)',
        'accent-action-hover': 'var(--accent-action-hover, #0077ed)',
        'accent-action-active': 'var(--accent-action-active, #0062c4)',
        'clinical-critical': 'var(--clinical-critical, #ff3b30)',
        'clinical-critical-text': 'var(--clinical-critical-text, #d70015)',
        'clinical-critical-hover': 'var(--clinical-critical-hover, #ff453a)',
        'clinical-critical-active': 'var(--clinical-critical-active, #d70015)',
        'clinical-verified': 'var(--clinical-verified, #34c759)',
        'clinical-verified-text': 'var(--clinical-verified-text, #1d7a37)',
        'clinical-pending': 'var(--clinical-pending, #ff9f0a)',
        'clinical-pending-text': 'var(--clinical-pending-text, #8a5200)',
        'border-hairline': 'var(--border-hairline-color, rgba(0, 0, 0, 0.1))',
        hairline: 'var(--border-hairline-color, rgba(0, 0, 0, 0.1))',
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          'Helvetica',
          'Arial',
          'sans-serif',
        ],
      },
      boxShadow: {
        ceiling: '0 1px 2px rgba(0,0,0,.04), 0 8px 24px rgba(0,0,0,.06)',
      },
      borderRadius: {
        card: '18px',
      },
    },
  },
  plugins: [],
};

export default config;
