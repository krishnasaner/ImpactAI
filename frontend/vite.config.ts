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
              return 'admin-dashboard';
            }
            if (id.includes('/pages/StudentDashboard.tsx')) {
              return 'student-dashboard';
            }
            if (id.includes('/pages/Booking.tsx')) {
              return 'booking-page';
            }
            return;
          }

          if (id.includes('node_modules/lucide-react') || id.includes('node_modules/react-icons')) {
            return 'icons';
          }

          if (id.includes('node_modules/@radix-ui')) {
            return 'radix-ui';
          }

          if (id.includes('node_modules/recharts')) {
            return 'charts';
          }

          if (id.includes('node_modules/framer-motion')) {
            return 'framer-motion';
          }

          if (id.includes('node_modules/@tanstack/react-query') || id.includes('node_modules/axios')) {
            return 'network-query';
          }

          if (id.includes('node_modules/react-router')) {
            return 'router';
          }

          if (id.includes('node_modules/date-fns') || id.includes('node_modules/clsx') || id.includes('node_modules/tailwind-merge') || id.includes('node_modules/zod')) {
            return 'utilities';
          }

          return 'vendor';
        },
      },
    },
    chunkSizeWarningLimit: 800,
  },
}));
