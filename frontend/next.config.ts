import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: "standalone",
  // Enable if you're using images
  images: {
    unoptimized: true,
  },
}

export default nextConfig
