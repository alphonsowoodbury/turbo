#!/usr/bin/env python3
"""
Document Audit Agent for Turbo

Audits all documents in docs/ directory, ensures proper frontmatter,
and re-uploads missing or updated documents to Turbo.

Usage:
    python scripts/docs_audit_agent.py [--dry-run] [--fix-headers] [--upload-all]

Options:
    --dry-run       Show what would be done without making changes
    --fix-headers   Add or fix missing frontmatter in files
    --upload-all    Re-upload all documents (not just missing ones)
"""

import argparse
import asyncio
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/docs_audit.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
TURBO_API_URL = os.getenv('TURBO_API_URL', 'http://localhost:8001/api/v1')
DOCS_DIR = Path('docs/')
DEFAULT_PROJECT_NAME = "Turbo Code Platform"

# File patterns
WATCHED_EXTENSIONS = {'.md', '.txt'}
IGNORED_PATTERNS = {'node_modules', '.git', '__pycache__', '.pytest_cache', 'venv', '.venv', '.backups'}


def parse_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], str]:
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
    elif 'design' in path_str or '/architecture/' in path_str:
        return 'design'
    elif 'requirements' in path_str:
        return 'requirements'
    else:
        return 'other'


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


def generate_frontmatter(file_path: Path, content: str, existing_frontmatter: Optional[Dict]) -> Dict[str, Any]:
    """Generate or enhance frontmatter for a document."""
    # Start with existing frontmatter if available
    frontmatter = existing_frontmatter.copy() if existing_frontmatter else {}

    # Ensure required fields
    if 'doc_type' not in frontmatter:
        frontmatter['doc_type'] = detect_doc_type_from_path(file_path)

    if 'project_name' not in frontmatter:
        frontmatter['project_name'] = DEFAULT_PROJECT_NAME

    if 'title' not in frontmatter:
        frontmatter['title'] = extract_title_from_content(content, str(file_path))

    # Add optional fields if missing
    if 'version' not in frontmatter:
        frontmatter['version'] = "1.0"

    # Auto-detect tags from path
    if 'tags' not in frontmatter:
        tags = []
        path_parts = file_path.parts

        # Add directory-based tags
        if 'guides' in path_parts:
            tags.append('guide')
        if 'adr' in path_parts:
            tags.append('architecture')
        if 'api' in path_parts:
            tags.append('api')
        if 'deployment' in path_parts:
            tags.append('deployment')
        if 'development' in path_parts:
            tags.append('development')

        if tags:
            frontmatter['tags'] = ', '.join(tags)

    return frontmatter


def format_frontmatter(frontmatter: Dict[str, Any]) -> str:
    """Format frontmatter as YAML."""
    yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_content}---\n\n"


async def get_existing_documents() -> Dict[str, Dict]:
    """Get all existing documents from Turbo API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{TURBO_API_URL}/documents/", params={"limit": 1000})
            response.raise_for_status()
            documents = response.json()

            # Index by title for quick lookup
            return {doc['title']: doc for doc in documents}
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch existing documents: {e}")
            return {}


async def upload_document(file_path: Path) -> bool:
    """Upload document to Turbo API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'text/plain')}
                response = await client.post(
                    f"{TURBO_API_URL}/documents/upload-file",
                    files=files
                )
                response.raise_for_status()
                document = response.json()
                logger.info(f"✓ Uploaded: {document.get('title')} (ID: {document.get('id')})")
                return True
        except httpx.HTTPError as e:
            logger.error(f"✗ Failed to upload {file_path}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"  Response: {e.response.text}")
            return False


async def audit_file(
    file_path: Path,
    existing_docs: Dict[str, Dict],
    dry_run: bool = False,
    fix_headers: bool = False,
    upload_all: bool = False
) -> Dict[str, Any]:
    """
    Audit a single file.

    Returns dict with:
        - status: 'ok', 'missing_header', 'missing_upload', 'error'
        - action_taken: description of what was done
        - needs_upload: bool
    """
    result = {
        'file': str(file_path),
        'status': 'ok',
        'action_taken': None,
        'needs_upload': False
    }

    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse frontmatter
        frontmatter, clean_content = parse_frontmatter(content)

        # Check if frontmatter is missing or incomplete
        if not frontmatter or 'doc_type' not in frontmatter or 'project_name' not in frontmatter:
            result['status'] = 'missing_header'

            # Generate proper frontmatter
            new_frontmatter = generate_frontmatter(file_path, clean_content, frontmatter)

            if fix_headers and not dry_run:
                # Write updated file with frontmatter
                new_content = format_frontmatter(new_frontmatter) + clean_content

                # Create backup
                backup_dir = DOCS_DIR / '.backups'
                backup_dir.mkdir(exist_ok=True)
                backup_path = backup_dir / file_path.name
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                # Write updated file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                result['action_taken'] = f"Added/fixed frontmatter (backup: {backup_path})"
                result['needs_upload'] = True
            elif fix_headers and dry_run:
                result['action_taken'] = "Would add/fix frontmatter"
                result['needs_upload'] = True
            else:
                result['action_taken'] = "Frontmatter missing (use --fix-headers to fix)"
                result['needs_upload'] = True
        else:
            # Frontmatter exists, check if document is in database
            title = frontmatter.get('title') or extract_title_from_content(clean_content, str(file_path))

            if title not in existing_docs:
                result['status'] = 'missing_upload'
                result['action_taken'] = "Not found in database"
                result['needs_upload'] = True
            elif upload_all:
                result['status'] = 'force_reupload'
                result['action_taken'] = "Re-uploading (--upload-all)"
                result['needs_upload'] = True
            else:
                result['action_taken'] = "Already in database"

        return result

    except Exception as e:
        logger.error(f"Error auditing {file_path}: {e}", exc_info=True)
        result['status'] = 'error'
        result['action_taken'] = str(e)
        return result


async def main():
    """Main audit function."""
    parser = argparse.ArgumentParser(description='Audit and fix document headers')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--fix-headers', action='store_true', help='Add or fix missing frontmatter')
    parser.add_argument('--upload-all', action='store_true', help='Re-upload all documents')
    parser.add_argument('--upload-missing', action='store_true', default=True, help='Upload missing documents (default)')
    args = parser.parse_args()

    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)

    logger.info("=" * 80)
    logger.info("DOCUMENT AUDIT AGENT")
    logger.info("=" * 80)
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    logger.info(f"Fix headers: {args.fix_headers}")
    logger.info(f"Upload all: {args.upload_all}")
    logger.info(f"Upload missing: {args.upload_missing}")
    logger.info("=" * 80)

    # Get existing documents from database
    logger.info("Fetching existing documents from database...")
    existing_docs = await get_existing_documents()
    logger.info(f"Found {len(existing_docs)} documents in database")

    # Scan all markdown files
    logger.info(f"Scanning {DOCS_DIR}...")
    files_to_process = []

    for file_path in DOCS_DIR.rglob('*'):
        if not file_path.is_file():
            continue

        if file_path.suffix not in WATCHED_EXTENSIONS:
            continue

        # Check if in ignored directory
        path_parts = file_path.parts
        if any(ignored in path_parts for ignored in IGNORED_PATTERNS):
            continue

        # Check if hidden file
        if any(part.startswith('.') for part in path_parts):
            continue

        files_to_process.append(file_path)

    logger.info(f"Found {len(files_to_process)} files to audit")
    logger.info("")

    # Audit all files
    results = {
        'ok': [],
        'missing_header': [],
        'missing_upload': [],
        'force_reupload': [],
        'error': []
    }

    for file_path in files_to_process:
        result = await audit_file(
            file_path,
            existing_docs,
            dry_run=args.dry_run,
            fix_headers=args.fix_headers,
            upload_all=args.upload_all
        )

        status = result['status']
        results[status].append(result)

        # Log result
        if status == 'ok':
            logger.info(f"✓ {file_path.name}: {result['action_taken']}")
        elif status in ['missing_header', 'missing_upload', 'force_reupload']:
            logger.warning(f"⚠ {file_path.name}: {result['action_taken']}")
        else:
            logger.error(f"✗ {file_path.name}: {result['action_taken']}")

    # Upload missing/updated documents
    if not args.dry_run and (args.upload_missing or args.upload_all):
        logger.info("")
        logger.info("=" * 80)
        logger.info("UPLOADING DOCUMENTS")
        logger.info("=" * 80)

        files_to_upload = [
            Path(r['file']) for r in results['missing_header'] + results['missing_upload'] + results['force_reupload']
            if r['needs_upload']
        ]

        logger.info(f"Uploading {len(files_to_upload)} documents...")

        upload_results = {'success': 0, 'failed': 0}
        for file_path in files_to_upload:
            success = await upload_document(file_path)
            if success:
                upload_results['success'] += 1
            else:
                upload_results['failed'] += 1

        logger.info(f"Upload complete: {upload_results['success']} success, {upload_results['failed']} failed")

    # Print summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("AUDIT SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total files scanned: {len(files_to_process)}")
    logger.info(f"  ✓ OK: {len(results['ok'])}")
    logger.info(f"  ⚠ Missing headers: {len(results['missing_header'])}")
    logger.info(f"  ⚠ Missing from database: {len(results['missing_upload'])}")
    logger.info(f"  ⚠ Force re-upload: {len(results['force_reupload'])}")
    logger.info(f"  ✗ Errors: {len(results['error'])}")

    if args.dry_run:
        logger.info("")
        logger.info("This was a DRY RUN - no changes were made")
        logger.info("Run without --dry-run to apply changes")

    logger.info("=" * 80)


if __name__ == '__main__':
    asyncio.run(main())
