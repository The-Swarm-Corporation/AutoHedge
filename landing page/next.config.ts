import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    rules: {
      // Vite-style `?raw` imports in the vendored ThreeUI sources.
      // The loader emits the HTML file contents verbatim as a default export.
      "*.html": {
        loaders: ["./tools/raw-loader.cjs"],
        as: "*.js",
      },
    },
  },
};

export default nextConfig;
