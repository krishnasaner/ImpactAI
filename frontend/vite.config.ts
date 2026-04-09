import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  base: '/',
  server: {
    host: '::',
    port: 8080,
  },
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
    dedupe: ['react', 'react-dom'],
  },
  define: {
    global: 'globalThis',
  },
  build: {
    target: 'esnext',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          if (!id.includes('node_modules')) {
            if (id.includes('/pages/admin-Dashboard.tsx')) {
              return 'dashboard';
            }
            if (id.includes('/pages/') && (id.includes('StudentDashboard') || id.includes('Booking'))) {
              return 'heavy-pages';
            }
            return;
          }

          // Keep React in the default vendor graph to avoid circular chunk references.
          if (id.includes('react') || id.includes('react-dom')) {
            return 'vendor';
          }

          // UI libraries
            if (id.includes('@radix-ui')) {
              return 'radix-ui';
            }

          // Router and state management
          if (id.includes('react-router') || id.includes('@tanstack/react-query')) {
            return 'router-query';
          }

          // Charts and animations
          if (id.includes('recharts') || id.includes('framer-motion')) {
            return 'charts-animations';
          }

          // Utilities and smaller libraries
          if (id.includes('date-fns') || id.includes('clsx') || id.includes('tailwind-merge')) {
            return 'utilities';
          }

          return 'vendor';
        },
      },
    },
    chunkSizeWarningLimit: 600,
  },
}));
