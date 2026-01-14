# Turbo Code Frontend

Modern Next.js frontend for Turbo Code - built for speed and polish like Linear/Jira.

## Tech Stack

- **Next.js 15** - App Router with React Server Components
- **TypeScript** - Full type safety
- **Tailwind CSS** - Utility-first styling
- **Shadcn/ui** - High-quality accessible components
- **TanStack Query** - Powerful async state management
- **Axios** - HTTP client for API calls
- **Lucide React** - Beautiful icons

## Getting Started

### Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

The app will be available at [http://localhost:3001](http://localhost:3001).

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Dashboard
│   └── projects/          # Projects pages
├── components/            # React components
│   ├── ui/               # Shadcn/ui components
│   ├── layout/           # Layout components (sidebar, header)
│   ├── projects/         # Project-specific components
│   ├── issues/           # Issue-specific components
│   └── dashboard/        # Dashboard components
├── hooks/                # Custom React hooks
│   ├── use-projects.ts   # Project queries & mutations
│   └── use-issues.ts     # Issue queries & mutations
├── lib/                  # Utilities and configuration
│   ├── api/             # API client and endpoints
│   │   ├── client.ts    # Axios instance
│   │   ├── projects.ts  # Project API calls
│   │   └── issues.ts    # Issue API calls
│   ├── providers.tsx    # React Query provider
│   ├── types.ts         # TypeScript types
│   └── utils.ts         # Utility functions
└── public/              # Static assets
```

## Features

### Current

- Dashboard with project & issue stats
- Project list with filtering by status
- Type-safe API integration
- Responsive layout with sidebar navigation
- Loading and error states
- React Query caching and optimistic updates

### Planned

- Create/Edit project dialogs
- Issue board (Kanban view)
- Issue list and details
- Command palette (Cmd+K)
- Keyboard shortcuts
- Search functionality
- Document management
- Tag management
- Dark mode
- Real-time updates

## API Integration

The frontend connects to the FastAPI backend via a type-safe client:

```typescript
// Using React Query hooks
const { data: projects } = useProjects({ status: "active" });

// Mutations
const createProject = useCreateProject();
createProject.mutate({
  name: "My Project",
  description: "Description",
  priority: "high",
  status: "active",
});
```

## Docker Deployment

The frontend is included in the main docker-compose stack:

```bash
# From project root
docker-compose up -d

# Frontend will be available at http://localhost:3001
# API at http://localhost:8001
```

## Development Tips

1. **Component Development**: Use Shadcn/ui components as building blocks
2. **State Management**: Use TanStack Query for server state, React hooks for UI state
3. **Styling**: Tailwind classes + CSS variables for theming
4. **Type Safety**: Import types from `@/lib/types`
5. **API Calls**: Always use React Query hooks from `@/hooks`

## Contributing

When adding new features:

1. Create types in `lib/types.ts`
2. Add API calls in `lib/api/*.ts`
3. Create React Query hooks in `hooks/*.ts`
4. Build UI components in `components/`
5. Add pages in `app/`

## Performance

- React Server Components for fast initial loads
- React Query for intelligent caching
- Automatic code splitting
- Optimized production builds
- Image optimization with Next.js Image

## License

MIT