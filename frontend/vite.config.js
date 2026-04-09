import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: '/CTS-3000-Quantified-Self-Data/',
  plugins: [react()],
})
