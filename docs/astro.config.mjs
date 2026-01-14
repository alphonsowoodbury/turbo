// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import node from '@astrojs/node';

// https://astro.build/config
export default defineConfig({
	output: 'server',
	adapter: node({
		mode: 'standalone',
	}),
	integrations: [
		starlight({
			title: 'Turbo Docs',
			description: 'Documentation for Turbo-Plan - AI-powered project management',
			social: [
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/turbo-plan/turbo-plan' },
			],
			sidebar: [
				{
					label: 'Getting Started',
					items: [
						{ label: 'Introduction', slug: 'getting-started/introduction' },
						{ label: 'Quick Start', slug: 'getting-started/quick-start' },
						{ label: 'Installation', slug: 'getting-started/installation' },
					],
				},
				{
					label: 'Concepts',
					items: [
						{ label: 'Projects', slug: 'concepts/projects' },
						{ label: 'Issues', slug: 'concepts/issues' },
						{ label: 'Initiatives', slug: 'concepts/initiatives' },
					],
				},
				{
					label: 'Guides',
					items: [
						{ label: 'MCP Integration', slug: 'guides/mcp-integration' },
						{ label: 'Claude Code Setup', slug: 'guides/claude-code-setup' },
					],
				},
				{
					label: 'API Reference',
					autogenerate: { directory: 'api-reference' },
				},
			],
			customCss: ['./src/styles/custom.css'],
		}),
	],
});
