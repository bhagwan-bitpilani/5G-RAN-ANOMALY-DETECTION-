import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current directory.
  const env = loadEnv(mode, process.cwd(), '')

  const isProduction = mode === 'production'
  
  return {
    plugins: [react()],
    
    // Base public path when served in production
    base: isProduction ? '/' : '/',
    
    // Server configuration
    server: {
      host: true, // Listen on all addresses
      port: 3000,
      strictPort: true, // Exit if port is already in use
      cors: true,
      
      // Proxy API calls to backend in development
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
    
    // Preview configuration (for `vite preview`)
    preview: {
      host: true,
      port: 3000,
      strictPort: true,
    },

    // Build configuration
    build: {
      outDir: 'dist',
      sourcemap: isProduction ? false : true, // Only generate sourcemaps in development
      minify: isProduction ? 'esbuild' : false,
      target: 'esnext',
      
      // Chunking optimization
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom'],
            ui: ['@mui/material', '@emotion/react', '@emotion/styled'],
            charts: ['recharts'],
            utils: ['lodash', 'date-fns', 'axios'],
          },
        },
      },
      
      // Asset handling
      assetsDir: 'assets',
      chunkSizeWarningLimit: 1000, // Increase chunk size warning limit (in kB)
      
      // Empty outDir before build
      emptyOutDir: true,
    },

    // Environment variables
    define: {
      __APP_ENV__: JSON.stringify(env.APP_ENV),
    },

    // CSS configuration
    css: {
      devSourcemap: !isProduction, // Generate sourcemaps for CSS in development
    },

    // Resolve configuration
    resolve: {
      alias: {
        '@': '/src', // Optional: if you use path aliases
      },
    },

    // Optimize dependencies
    optimizeDeps: {
      include: ['react', 'react-dom', '@mui/material', 'recharts'],
    },
  }
})
