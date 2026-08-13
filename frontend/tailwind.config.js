/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Core brand palette from Stitch design system
        'manila': '#EDE6D6',
        'ink': '#1C1B19',
        'stamp-red': '#A63D2F',
        'olive': '#6B7353',
        'olive-secondary': '#5A6243',
        'confidence-teal': '#3C6E71',
        'fresh-paper': '#F4F0E6',

        // Material Design surface tokens
        'surface': '#FFF9ED',
        'surface-bright': '#FFF9ED',
        'surface-dim': '#E0D9CA',
        'surface-container': '#F4EDDD',
        'surface-container-low': '#FAF3E3',
        'surface-container-high': '#EFE8D8',
        'surface-container-highest': '#E9E2D2',
        'surface-container-lowest': '#FFFFFF',
        'surface-variant': '#E9E2D2',

        // On-surface
        'on-surface': '#1E1C12',
        'on-surface-variant': '#494740',

        // Primary
        'primary': '#000000',
        'on-primary': '#FFFFFF',
        'primary-container': '#1C1B19',
        'on-primary-container': '#868380',

        // Secondary
        'secondary': '#5A6243',
        'on-secondary': '#FFFFFF',
        'secondary-container': '#DEE7C0',
        'on-secondary-container': '#606849',

        // Tertiary
        'tertiary': '#000000',
        'on-tertiary': '#FFFFFF',
        'tertiary-container': '#410000',
        'on-tertiary-container': '#D5604F',

        // Error
        'error': '#BA1A1A',
        'on-error': '#FFFFFF',
        'error-container': '#FFDAD6',
        'on-error-container': '#93000A',

        // Other
        'outline': '#7A776F',
        'outline-variant': '#CBC6BD',
        'inverse-surface': '#333026',
        'inverse-on-surface': '#F7F0E0',
        'surface-tint': '#605E5B',
      },
      fontFamily: {
        'headline': ['"Courier Prime"', 'monospace'],
        'body': ['"IBM Plex Serif"', 'serif'],
        'code': ['"IBM Plex Mono"', 'monospace'],
        'label': ['"Courier Prime"', 'monospace'],
      },
      fontSize: {
        'headline-lg': ['32px', { lineHeight: '40px', fontWeight: '700', letterSpacing: '-0.02em' }],
        'headline-md': ['24px', { lineHeight: '32px', fontWeight: '700' }],
        'body-lg': ['18px', { lineHeight: '28px', fontWeight: '400' }],
        'body-md': ['16px', { lineHeight: '24px', fontWeight: '400' }],
        'label-caps': ['14px', { lineHeight: '16px', fontWeight: '700' }],
        'code-sm': ['13px', { lineHeight: '20px', fontWeight: '400' }],
      },
      spacing: {
        'margin': '32px',
        'gutter': '24px',
        'stack': '16px',
        'indent': '40px',
      },
      borderRadius: {
        DEFAULT: '0px',
        'lg': '0px',
        'xl': '0px',
        'full': '0px',
        'md': '0px',
        'sm': '0px',
      },
    },
  },
  plugins: [],
}
