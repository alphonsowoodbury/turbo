"""Document API endpoints."""

import logging
import re
from pathlib import Path
from uuid import UUID

import yaml
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from pydantic import BaseModel

from turbo.api.dependencies import get_document_service, get_project_service, get_tag_service
from turbo.core.schemas import DocumentCreate, DocumentResponse, DocumentUpdate, ProjectCreate, TagCreate
from turbo.core.services import DocumentService, ProjectService, TagService
from turbo.utils.exceptions import (
    DocumentNotFoundError,
    ProjectNotFoundError,
)
from turbo.utils.exceptions import (
    ValidationError as TurboValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class TemplateRequest(BaseModel):
    """Request model for creating document from template."""

    template_name: str
    title: str
    project_id: UUID
    variables: dict = {}


class DuplicateRequest(BaseModel):
    """Request model for duplicating document."""

    title: str
    version: str | None = None


class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete operations."""

    document_ids: list[UUID]


class Template(BaseModel):
    """Template information model."""

    name: str
    description: str
    variables: list[str]


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_data: DocumentCreate,
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Create a new document."""
    try:
        return await document_service.create_document(document_data)
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {document_data.project_id} not found",
        )
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID, document_service: DocumentService = Depends(get_document_service)
) -> DocumentResponse:
    """Get a document by ID."""
    try:
        return await document_service.get_document_by_id(document_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found",
        )


@router.get("/", response_model=list[DocumentResponse])
async def get_documents(
    type_filter: str | None = Query(None, alias="type"),
    format_filter: str | None = Query(None, alias="format"),
    project_id: UUID | None = Query(None),
    workspace: str | None = Query(None, pattern="^(all|personal|freelance|work)$"),
    work_company: str | None = Query(None),
    limit: int | None = Query(None, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    document_service: DocumentService = Depends(get_document_service),
) -> list[DocumentResponse]:
    """Get all documents with optional filtering by type, format, project, or workspace."""
    # Workspace filtering takes precedence
    if workspace and workspace != "all":
        return await document_service.get_documents_by_workspace(
            workspace=workspace,
            work_company=work_company,
            limit=limit,
            offset=offset,
        )
    elif type_filter:
        return await document_service.get_documents_by_type(type_filter)
    elif format_filter:
        return await document_service.get_documents_by_format(format_filter)
    elif project_id:
        return await document_service.get_documents_by_project(project_id)
    else:
        return await document_service.get_all_documents(limit=limit, offset=offset)


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    document_data: DocumentUpdate,
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Update a document."""
    try:
        return await document_service.update_document(document_id, document_data)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found",
        )
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID, document_service: DocumentService = Depends(get_document_service)
) -> None:
    """Delete a document."""
    try:
        await document_service.delete_document(document_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found",
        )


@router.get("/search", response_model=list[DocumentResponse])
async def search_documents(
    query: str = Query(..., min_length=1),
    document_service: DocumentService = Depends(get_document_service),
) -> list[DocumentResponse]:
    """Search documents by title and content."""
    return await document_service.search_documents(query)


@router.get("/{document_id}/versions", response_model=list[dict])
async def get_document_versions(
    document_id: UUID, document_service: DocumentService = Depends(get_document_service)
) -> list[dict]:
    """Get document version history."""
    try:
        return await document_service.get_document_versions(document_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found",
        )


@router.get("/{document_id}/export")
async def export_document(
    document_id: UUID,
    format: str = Query(..., pattern="^(pdf|html|docx|markdown)$"),
    document_service: DocumentService = Depends(get_document_service),
) -> Response:
    """Export document in different formats."""
    try:
        content, content_type = await document_service.export_document(
            document_id, format
        )

        # Set appropriate headers based on format
        headers = {}
        if format == "pdf":
            headers["Content-Disposition"] = (
                f"attachment; filename=document_{document_id}.pdf"
            )
        elif format == "docx":
            headers["Content-Disposition"] = (
                f"attachment; filename=document_{document_id}.docx"
            )

        return Response(content=content, media_type=content_type, headers=headers)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found",
        )
    except Exception:
        logger.exception("Export failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export failed",
        )


@router.post(
    "/from-template",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document_from_template(
    template_request: TemplateRequest,
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Create a document from a template."""
    try:
        return await document_service.create_document_from_template(
            template_request.template_name,
            template_request.title,
            template_request.project_id,
            template_request.variables,
        )
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {template_request.project_id} not found",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/templates", response_model=list[Template])
async def get_available_templates(
    document_service: DocumentService = Depends(get_document_service),
) -> list[Template]:
    """Get available document templates."""
    templates_data = await document_service.get_available_templates()
    return [
        Template(
            name=template["name"],
            description=template["description"],
            variables=template["variables"],
        )
        for template in templates_data
    ]


@router.post(
    "/{document_id}/duplicate",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_document(
    document_id: UUID,
    duplicate_request: DuplicateRequest,
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Duplicate a document."""
    try:
        return await document_service.duplicate_document(
            document_id, duplicate_request.title, duplicate_request.version
        )
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found",
        )


@router.post("/upload-file", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document_file(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service),
    project_service: ProjectService = Depends(get_project_service),
    tag_service: TagService = Depends(get_tag_service),
) -> DocumentResponse:
    """
    Upload a document file with frontmatter metadata.

    Supports:
    - Markdown files (.md) with YAML frontmatter
    - Text files (.txt) with YAML frontmatter
    - Auto-detection of title, doc_type, and project
    - Auto-creation of projects and tags if they don't exist

    Frontmatter format:
    ---
    doc_type: user_guide
    project_name: Turbo Code Platform
    title: My Document
    version: "1.0"
    author: user@example.com
    tags: tag1, tag2, tag3
    ---

    Content starts here...
    """
    try:
        # Read file content with size limit (10 MB)
        max_size = 10 * 1024 * 1024
        content_bytes = await file.read(max_size + 1)
        if len(content_bytes) > max_size:
            raise HTTPException(
                status_code=413,
                detail="File too large. Maximum upload size is 10 MB.",
            )
        content = content_bytes.decode('utf-8')

        # Parse frontmatter
        frontmatter, clean_content = parse_frontmatter(content)

        # Determine document properties
        file_path = Path(file.filename or "untitled.md")

        # Get or detect doc_type
        doc_type = frontmatter.get('doc_type') if frontmatter else None
        if not doc_type:
            doc_type = detect_doc_type_from_path(file_path)

        # Get or detect title
        title = frontmatter.get('title') if frontmatter else None
        if not title:
            title = extract_title_from_content(clean_content, str(file_path))

        # Get project name (default to "Turbo Code Platform")
        project_name = frontmatter.get('project_name', 'Turbo Code Platform') if frontmatter else 'Turbo Code Platform'

        # Find or create project
        project_id = await find_or_create_project(project_name, project_service)

        # Check for existing document (upsert mode)
        update_mode = frontmatter.get('update_mode', 'upsert') if frontmatter else 'upsert'
        existing_doc = await find_existing_document_by_title(title, project_id, document_service)

        if existing_doc and update_mode == 'skip':
            # Return existing document without updating
            return existing_doc

        # Prepare document data
        doc_data = {
            "title": title,
            "content": clean_content,
            "type": doc_type,
            "project_id": project_id,
            "version": frontmatter.get('version', '1.0') if frontmatter else '1.0',
            "author": frontmatter.get('author') if frontmatter else None,
            "format": frontmatter.get('format', detect_format_from_extension(file_path)) if frontmatter else detect_format_from_extension(file_path),
        }

        # Create or update document
        if existing_doc and update_mode == 'upsert':
            # Update existing document
            document = await document_service.update_document(
                existing_doc.id,
                DocumentUpdate(**{k: v for k, v in doc_data.items() if k != 'project_id'})
            )
        else:
            # Create new document
            document = await document_service.create_document(DocumentCreate(**doc_data))

        # Handle tags
        if frontmatter and 'tags' in frontmatter:
            tags = frontmatter['tags']
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',')]

            # Find or create tags and associate with document
            for tag_name in tags:
                if not tag_name:
                    continue

                tag = await find_or_create_tag(tag_name, tag_service)
                # Associate tag with document (via tag service or document service)
                # Note: This might need adjustment based on your tagging implementation
                try:
                    await tag_service.add_tag_to_entity('document', document.id, tag.id)
                except Exception:
                    # Tag association might fail if already exists, that's okay
                    pass

        return document

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded text"
        )
    except Exception:
        logger.exception("Failed to upload document")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document",
        )


def parse_frontmatter(content: str) -> tuple[dict | None, str]:
    """Parse YAML frontmatter from content."""
    if not content.startswith('---\n'):
        return None, content

    match = re.match(r'^---\n(.*?\n)---\n', content, re.DOTALL)
    if not match:
        return None, content

    frontmatter_text = match.group(1)
    content_without_frontmatter = content[match.end():]

    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return None, content
        return frontmatter, content_without_frontmatter.lstrip()
    except yaml.YAMLError:
        return None, content


def extract_title_from_content(content: str, filename: str) -> str:
    """Extract title from content or filename."""
    # Try to find first H1 heading
    h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if h1_match:
        return h1_match.group(1).strip()

    # Use filename
    path = Path(filename)
    if path.stem and path.stem != 'README':
        title = path.stem.replace('-', ' ').replace('_', ' ')
        return title.title()

    return "Untitled Document"


def detect_doc_type_from_path(file_path: Path) -> str:
    """Detect document type from file path."""
    path_str = str(file_path).lower()

    if '/guides/' in path_str:
        return 'user_guide'
    elif '/adr/' in path_str:
        return 'adr'
    elif '/api/' in path_str:
        return 'api_doc'
    elif 'readme' in path_str:
        return 'readme'
    elif 'changelog' in path_str:
        return 'changelog'
    elif 'spec' in path_str or 'specification' in path_str:
        return 'specification'
    elif 'design' in path_str:
        return 'design'
    elif 'requirements' in path_str:
        return 'requirements'
    else:
        return 'other'


def detect_format_from_extension(file_path: Path) -> str:
    """Detect document format from file extension."""
    ext = file_path.suffix.lower()

    if ext == '.md':
        return 'markdown'
    elif ext == '.html':
        return 'html'
    elif ext == '.txt':
        return 'text'
    elif ext == '.pdf':
        return 'pdf'
    elif ext == '.docx':
        return 'docx'
    else:
        return 'text'


async def find_or_create_project(project_name: str, project_service: ProjectService) -> UUID:
    """Find existing project or create new one."""
    # Try to find existing project
    projects = await project_service.get_all_projects()
    for project in projects:
        if project.name == project_name:
            return project.id

    # Create new project
    new_project = await project_service.create_project(
        ProjectCreate(
            name=project_name,
            description=f"Auto-created project for {project_name}",
            status="active",
            priority="medium"
        )
    )
    return new_project.id


async def find_existing_document_by_title(title: str, project_id: UUID, document_service: DocumentService) -> DocumentResponse | None:
    """Find existing document by title and project."""
    documents = await document_service.get_documents_by_project(project_id)
    for doc in documents:
        if doc.title == title:
            return doc
    return None


async def find_or_create_tag(tag_name: str, tag_service: TagService):
    """Find existing tag or create new one."""
    # Try to find existing tag
    tags = await tag_service.get_all_tags()
    for tag in tags:
        if tag.name == tag_name:
            return tag

    # Create new tag
    new_tag = await tag_service.create_tag(
        TagCreate(
            name=tag_name,
            color="#3b82f6",  # Default blue
            description=f"Auto-created tag for {tag_name}"
        )
    )
    return new_tag


@router.post("/bulk-delete", response_model=dict)
async def bulk_delete_documents(
    bulk_request: BulkDeleteRequest,
    document_service: DocumentService = Depends(get_document_service),
) -> dict:
    """Bulk delete documents."""
    try:
        deleted_count = await document_service.bulk_delete_documents(
            bulk_request.document_ids
        )
        return {"deleted_count": deleted_count}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
