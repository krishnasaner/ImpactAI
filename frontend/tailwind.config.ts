import type { Config } from 'tailwindcss';
import tailwindcssAnimate from 'tailwindcss-animate';

export default {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    fontFamily: {
      sans: ['DM Sans Variable', 'Avenir Next', 'Segoe UI', 'sans-serif'],
      display: ['Manrope Variable', 'Arial Black', 'Segoe UI', 'sans-serif'],
    },
    extend: {
      colors: {
        // ImpactAI neo-brutalist wellness palette
        primary: {
          DEFAULT: '#FFE17C',
          foreground: '#171E19',
          light: '#FFF0A8',
          glow: '#FFE17C',
          variant: '#E9CF65',
        },
        accent: {
          DEFAULT: '#B7C6C2',
          foreground: '#171E19',
          light: '#CED7D4',
          variant: '#9FAFAA',
        },
        cta: {
          DEFAULT: '#FFB400', // Warm Amber
          foreground: '#171E19',
          hover: '#E5A200',
        },
        neutral: {
          DEFAULT: '#F5F5F5',
          dark: '#E5E7EB',
          light: '#FAFAFA',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          muted: '#F8FAFC',
        },
        danger: '#E53935',
        warning: '#F9A825',
        success: '#43A047',

        // Compatibility tokens
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: '#2F7A6D',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
          light: 'hsl(var(--secondary-light))',
          variant: 'hsl(var(--secondary-variant))',
        },
        trust: { DEFAULT: '#2F7A6D', foreground: '#FFFFFF' },
        safety: { DEFAULT: '#43A047', foreground: '#FFFFFF' },
        severity: {
          low: '#43A047',
          medium: '#FFB400',
          high: '#F9A825',
          crisis: '#E53935',
        },
        destructive: { DEFAULT: '#E53935', foreground: '#FFFFFF' },
        muted: { DEFAULT: 'hsl(var(--muted))', foreground: 'hsl(var(--muted-foreground))' },
        popover: { DEFAULT: 'hsl(var(--popover))', foreground: 'hsl(var(--popover-foreground))' },
        card: { DEFAULT: 'hsl(var(--card))', foreground: 'hsl(var(--card-foreground))' },
        heading: { DEFAULT: '#172B26', light: '#2F7A6D' },
      },
      boxShadow: {
        sm: '0 1px 2px rgba(0,0,0,0.05)',
        md: '0 4px 6px rgba(0,0,0,0.08)',
        lg: '0 10px 15px rgba(0,0,0,0.1)',
        floating: '0 10px 25px -5px rgba(0, 0, 0, 0.08)',
        premium: '0 12px 30px -8px rgba(47, 122, 109, 0.2)',
      },
      borderRadius: {
        md: '0.5rem',
        lg: '0.75rem',
        xl: '1rem',
        '2xl': '1.5rem',
      },
      keyframes: {
        tilt: {
          '0%, 100%': { transform: 'rotate(-1deg)' },
          '50%': { transform: 'rotate(1deg)' },
        },
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        breathe: {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.8' },
          '50%': { transform: 'scale(1.35)', opacity: '1' },
        },
      },
      animation: {
        tilt: 'tilt 3s ease-in-out infinite',
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        breathe: 'breathe 8s ease-in-out infinite',
      },
    },
  },
  plugins: [tailwindcssAnimate],
} satisfies Config;
