import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8765",
    },
  },
  build: {
    outDir: "../src/obsidian_knowledge_base/static/dist",
    emptyOutDir: true,
  },
});
