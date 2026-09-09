import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import basicSsl from '@vitejs/plugin-basic-ssl'

export default defineConfig({
  plugins: [basicSsl(),vue()],
  server: {
    proxy: {
      "/api": "http://localhost:8000"
    }
  }
});