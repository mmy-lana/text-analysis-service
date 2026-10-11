import adapter from '@sveltejs/adapter-vercel';
import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [
		tailwindcss(),
		// SvelteKit 3 reads configuration exclusively from this plugin call
		// (svelte.config.js is no longer supported by this version), so the
		// adapter is declared here as the single source of deployment config.
		sveltekit({
			adapter: adapter()
		})
	],
	server: {
		proxy: {
			// Local development proxy: same-origin /api requests avoid CORS and
			// port mismatches against the FastAPI service.
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true
			}
		}
	}
});
