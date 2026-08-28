import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, "../", "");
  const runtimeEnv = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env;

  return {
    // 生产环境通过 /shengya/ 子路径提供静态资源。
    base: runtimeEnv?.VITE_BASE_PATH || env.VITE_BASE_PATH || "/",
    envDir: "../",
    plugins: [react()],
    server: {
      port: 5173
    },
    test: {
      environment: "jsdom",
      environmentOptions: {
        jsdom: {
          url: "http://localhost/"
        }
      },
      restoreMocks: true,
      setupFiles: "./src/test/setup.ts"
    }
  };
});
