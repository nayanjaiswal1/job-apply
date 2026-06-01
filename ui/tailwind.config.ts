import type { Config } from 'tailwindcss'

export default {
  darkMode: ['class'],
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand:          'var(--color-brand)',
        'brand-muted':  'var(--color-brand-muted)',
        body:           'var(--color-body)',
        muted:          'var(--color-muted)',
        raised:         'var(--color-raised)',
        danger:         'var(--color-danger)',
        success:        'var(--color-success)',
        warning:        'var(--color-warning)',
        border:         'hsl(var(--border))',
        input:          'hsl(var(--input))',
        ring:           'hsl(var(--ring))',
        background:     'hsl(var(--background))',
        foreground:     'hsl(var(--foreground))',
        primary: {
          DEFAULT:    'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT:    'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT:    'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        destructive: {
          DEFAULT:    'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)'],
        mono: ['var(--font-mono)'],
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      boxShadow: {
        sm:      'var(--shadow-sm)',
        DEFAULT: 'var(--shadow)',
        lg:      'var(--shadow-lg)',
      },
    },
  },
} satisfies Config
