/* Shared Tailwind CDN theme. Must load after the Tailwind CDN script
   and before the page renders. */
tailwind.config = {
  theme: {
    extend: {
      colors: {
        ink: '#0a0e14',
        panel: '#111826',
        edge: '#1f2937',
        accent: '#ff9900',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'ui-monospace', 'monospace'],
      },
    },
  },
};
