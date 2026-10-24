// @ts-check
import { defineConfig } from 'astro/config';

// Laman GitHub Pages projek: https://maryamstore6.github.io/hadiahkorporat/
export default defineConfig({
  site: 'https://maryamstore6.github.io',
  base: '/hadiahkorporat',
  output: 'static',
  trailingSlash: 'ignore',
  build: { inlineStylesheets: 'auto' },
});
