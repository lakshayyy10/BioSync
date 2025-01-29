/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = { fs: false }; // Prevent "fs" module from bundling in browser
    }
    return config;
  },
  // Add other config options if needed
};

module.exports = nextConfig;

