# Entity Comments Section Pattern

## Overview

The `EntityCommentsSection` component provides a consistent, reusable pattern for displaying comments across all entity detail pages. It features a compact scrollable design with a fixed input at the bottom.

## Features

- **Fixed height container**: Prevents comments from taking over the screen
- **Scrollable comments list**: Max 400px height with independent scrolling
- **Fixed input at bottom**: Always accessible, auto-expands as user types
- **Slim by default**: Input starts at 36px, expands to 200px max
- **Enter to send**: Quick keyboard shortcut (Shift+Enter for new line)
- **Consistent UX**: Same behavior across all entity types

## Usage

### Basic Example

```tsx
import { EntityCommentsSection } from "@/components/shared/entity-comments-section";

export default function EntityDetailPage() {
  const entityId = params.id as string;

  return (
    <PageLayout title="Entity Details">
      <div className="flex flex-col h-full overflow-hidden">
        {/* Scrollable content area */}
        <div className="flex-1 overflow-y-auto space-y-4 p-6 pb-0">
          {/* Your entity content here */}
        </div>

        {/* Fixed comments section */}
        <EntityCommentsSection
          entityType="issue"
          entityId={entityId}
          height="500px"
        />
      </div>
    </PageLayout>
  );
}
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `entityType` | `"issue" \| "project" \| "milestone" \| "initiative" \| "document"` | Required | Type of entity |
| `entityId` | `string` | Required | UUID of the entity |
| `height` | `string` | `"500px"` | Total height of comments section |
| `title` | `string` | `"Comments"` | Section header title |

## Implementation Examples

### 1. Issue Detail Page ✅ (Implemented)

**File**: `frontend/app/issues/[id]/page.tsx`

```tsx
<EntityCommentsSection
  entityType="issue"
  entityId={issueId}
  height="500px"
/>
```

### 2. Project Detail Page

**File**: `frontend/app/projects/[id]/page.tsx`

```tsx
import { EntityCommentsSection } from "@/components/shared/entity-comments-section";

export default function ProjectDetailPage() {
  const projectId = params.id as string;

  return (
    <PageLayout title={project.name}>
      <div className="flex flex-col h-full overflow-hidden">
        {/* Project content */}
        <div className="flex-1 overflow-y-auto space-y-4 p-6 pb-0">
          {/* Project stats, milestones, initiatives, etc. */}
        </div>

        {/* Project discussions */}
        <EntityCommentsSection
          entityType="project"
          entityId={projectId}
          height="500px"
          title="Discussions"
        />
      </div>
    </PageLayout>
  );
}
```

### 3. Milestone Detail Page

**File**: `frontend/app/milestones/[id]/page.tsx`

```tsx
import { EntityCommentsSection } from "@/components/shared/entity-comments-section";

export default function MilestoneDetailPage() {
  const milestoneId = params.id as string;

  return (
    <PageLayout title={milestone.name}>
      <div className="flex flex-col h-full overflow-hidden">
        {/* Milestone content */}
        <div className="flex-1 overflow-y-auto space-y-4 p-6 pb-0">
          {/* Milestone details, progress, issues, etc. */}
        </div>

        {/* Milestone notes/discussions */}
        <EntityCommentsSection
          entityType="milestone"
          entityId={milestoneId}
          height="450px"
          title="Notes & Discussions"
        />
      </div>
    </PageLayout>
  );
}
```

### 4. Initiative Detail Page

**File**: `frontend/app/initiatives/[id]/page.tsx`

```tsx
import { EntityCommentsSection } from "@/components/shared/entity-comments-section";

export default function InitiativeDetailPage() {
  const initiativeId = params.id as string;

  return (
    <PageLayout title={initiative.name}>
      <div className="flex flex-col h-full overflow-hidden">
        {/* Initiative content */}
        <div className="flex-1 overflow-y-auto space-y-4 p-6 pb-0">
          {/* Initiative details, issues, documents, etc. */}
        </div>

        {/* Initiative discussions */}
        <EntityCommentsSection
          entityType="initiative"
          entityId={initiativeId}
          height="500px"
          title="Team Discussions"
        />
      </div>
    </PageLayout>
  );
}
```

### 5. Document Detail Page

**File**: `frontend/app/documents/[id]/page.tsx`

```tsx
import { EntityCommentsSection } from "@/components/shared/entity-comments-section";

export default function DocumentDetailPage() {
  const documentId = params.id as string;

  return (
    <PageLayout title={document.title}>
      <div className="flex flex-col h-full overflow-hidden">
        {/* Document content */}
        <div className="flex-1 overflow-y-auto space-y-4 p-6 pb-0">
          {/* Document viewer, metadata, versions, etc. */}
        </div>

        {/* Document feedback/reviews */}
        <EntityCommentsSection
          entityType="document"
          entityId={documentId}
          height="400px"
          title="Feedback & Reviews"
        />
      </div>
    </PageLayout>
  );
}
```

## Required Page Layout Pattern

For the comments section to work correctly, the page must follow this structure:

```tsx
<PageLayout>
  <div className="flex flex-col h-full overflow-hidden">
    {/* 1. Scrollable content area */}
    <div className="flex-1 overflow-y-auto space-y-4 p-6 pb-0">
      {/* Main content here */}
    </div>

    {/* 2. Fixed comments section */}
    <EntityCommentsSection {...props} />
  </div>
</PageLayout>
```

### Key CSS Classes:

- **Outer container**: `flex flex-col h-full overflow-hidden`
  - Full height, column layout, hide overflow

- **Content area**: `flex-1 overflow-y-auto space-y-4 p-6 pb-0`
  - Flex grow, vertical scroll, spacing, padding (no bottom padding)

- **Comments section**: Provided by `EntityCommentsSection`
  - Fixed height, flex-shrink-0, border-top

## Backend API Requirements

Each entity type will need comment endpoints:

### Issues ✅ (Implemented)
- `POST /api/v1/comments/` - Create comment
- `GET /api/v1/comments/issue/{issue_id}` - Get comments
- `PUT /api/v1/comments/{comment_id}` - Update comment
- `DELETE /api/v1/comments/{comment_id}` - Delete comment

### Projects (TODO)
- `POST /api/v1/projects/{project_id}/comments/`
- `GET /api/v1/projects/{project_id}/comments/`
- Similar CRUD operations

### Milestones (TODO)
- `POST /api/v1/milestones/{milestone_id}/comments/`
- `GET /api/v1/milestones/{milestone_id}/comments/`

### Initiatives (TODO)
- `POST /api/v1/initiatives/{initiative_id}/comments/`
- `GET /api/v1/initiatives/{initiative_id}/comments/`

### Documents (TODO)
- `POST /api/v1/documents/{document_id}/comments/`
- `GET /api/v1/documents/{document_id}/comments/`

## Extending the Component

### Adding New Entity Types

1. **Update the component prop type**:
```tsx
// frontend/components/shared/entity-comments-section.tsx
entityType: "issue" | "project" | "milestone" | "initiative" | "document" | "your-new-type"
```

2. **Add the entity case**:
```tsx
{entityType === "your-new-type" ? (
  <YourNewTypeCommentList entityId={entityId} />
) : (
  // existing cases
)}
```

3. **Create the comment list component**:
```tsx
// frontend/components/your-entity/comment-list.tsx
export function YourNewTypeCommentList({ entityId }: { entityId: string }) {
  // Use the same pattern as CommentList
}
```

### Customizing Appearance

You can customize the appearance by passing additional props:

```tsx
<EntityCommentsSection
  entityType="issue"
  entityId={issueId}
  height="600px"           // Taller section
  title="Team Feedback"    // Custom title
/>
```

## Migration Checklist

To migrate an existing entity detail page:

- [ ] Import `EntityCommentsSection` component
- [ ] Wrap content in flex column container with `h-full overflow-hidden`
- [ ] Move main content to scrollable div with `flex-1 overflow-y-auto`
- [ ] Replace existing comments section with `EntityCommentsSection`
- [ ] Remove bottom padding from content area (`pb-0`)
- [ ] Test scrolling behavior (both content and comments)
- [ ] Verify textarea auto-expand and Enter key behavior
- [ ] Confirm comments don't overflow screen

## Design Principles

1. **Consistency**: Same UX across all entity types
2. **Compactness**: Comments don't dominate the screen
3. **Accessibility**: Always visible input, keyboard shortcuts
4. **Performance**: Independent scrolling, efficient rendering
5. **Flexibility**: Customizable height and title

## Testing

Before deploying to production:

1. **Visual testing**: Verify layout on different screen sizes
2. **Scroll testing**: Test both content and comments scrolling independently
3. **Input testing**: Test auto-expand, Enter key, Shift+Enter
4. **Long comment testing**: Ensure long comment threads scroll properly
5. **Empty state**: Test with no comments
6. **Loading state**: Test while comments are loading

## Future Enhancements

Potential improvements to consider:

- [ ] Collapsible comments section
- [ ] Comment reactions (emoji responses)
- [ ] Comment threading (replies to comments)
- [ ] Comment sorting (newest/oldest/most active)
- [ ] Comment search/filter
- [ ] Real-time updates (WebSocket)
- [ ] @mentions with autocomplete
- [ ] Rich text editor (formatting, images)
- [ ] Comment drafts (auto-save)
- [ ] Keyboard navigation

## Questions?

For implementation help or questions:
- See example: `frontend/app/issues/[id]/page.tsx`
- Component source: `frontend/components/shared/entity-comments-section.tsx`
- Base component: `frontend/components/issues/comment-list.tsx`
