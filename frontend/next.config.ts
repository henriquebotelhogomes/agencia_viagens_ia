import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Empacota a app com um servidor mínimo próprio (server.js), sem depender do
  // node_modules completo — imagem Docker menor. Ver frontend/Dockerfile.
  output: "standalone",
};

export default nextConfig;
