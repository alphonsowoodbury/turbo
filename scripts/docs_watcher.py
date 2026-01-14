#!/usr/bin/env python3
"""
Document File Watcher for Turbo

Watches the docs/ directory for new or modified markdown files and automatically
uploads them to Turbo with parsed frontmatter metadata.

Usage:
    python scripts/docs_watcher.py [--watch-dir DIRECTORY] [--api-url URL]

Environment Variables:
    TURBO_API_URL - Base URL for Turbo API (default: http://localhost:8001/api/v1)
    DOCS_WATCH_DIR - Directory to watch (default: docs/)
"""

import asyncio
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx
import yaml
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/docs_watcher.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
TURBO_API_URL = os.getenv('TURBO_API_URL', 'http://localhost:8001/api/v1')
DOCS_WATCH_DIR = os.getenv('DOCS_WATCH_DIR', 'docs/')
DEFAULT_PROJECT_NAME = "Turbo Code Platform"

# File patterns to watch
WATCHED_EXTENSIONS = {'.md', '.txt'}
IGNORED_PATTERNS = {
    'node_modules',
    '.git',
    '__pycache__',
    '.pytest_cache',
    'venv',
    '.venv',
    '.backups'
}


def parse_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Full file content

    Returns:
        Tuple of (frontmatter dict or None, content without frontmatter)
    """
    # Check if file starts with frontmatter delimiter
    if not content.startswith('---\n'):
        return None, content

    # Find the closing delimiter
    match = re.match(r'^---\n(.*?\n)---\n', content, re.DOTALL)
    if not match:
        logger.warning("Found opening frontmatter delimiter but no closing delimiter")
        return None, content

    frontmatter_text = match.group(1)
    content_without_frontmatter = content[match.end():]

    # Parse YAML
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            logger.warning(f"Frontmatter is not a dictionary: {type(frontmatter)}")
            return None, content
        return frontmatter, content_without_frontmatter.lstrip()
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse frontmatter YAML: {e}")
        return None, content






async def process_document_file(file_path: Path) -> bool:
    """
    Process a document file and upload to Turbo.

    Args:
        file_path: Path to the document file

    Returns:
        True if successfully processed, False otherwise
    """
    logger.info(f"Processing document: {file_path}")

    try:
        # Check if file has frontmatter with auto_upload disabled
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        frontmatter, _ = parse_frontmatter(content)
        if frontmatter and not frontmatter.get('auto_upload', True):
            logger.info(f"Skipping {file_path} (auto_upload=false)")
            return True

        # Upload file using the upload endpoint
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'text/plain')}
                response = await client.post(
                    f"{TURBO_API_URL}/documents/upload-file",
                    files=files
                )
                response.raise_for_status()
                document = response.json()
                logger.info(f"Successfully uploaded document: {document.get('title')} (ID: {document.get('id')})")
                return True

    except httpx.HTTPError as e:
        logger.error(f"Failed to upload {file_path}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Failed to process {file_path}: {e}", exc_info=True)
        return False


class DocumentEventHandler(FileSystemEventHandler):
    """Handler for document file system events."""

    def __init__(self, loop):
        super().__init__()
        self.loop = loop
        self.debounce_map = {}  # filepath -> last_event_time
        self.debounce_delay = 2.0  # seconds

    def should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed."""
        # Check extension
        if file_path.suffix not in WATCHED_EXTENSIONS:
            return False

        # Check if in ignored directory
        path_parts = file_path.parts
        if any(ignored in path_parts for ignored in IGNORED_PATTERNS):
            return False

        # Check if hidden file
        if any(part.startswith('.') for part in path_parts):
            return False

        return True

    def debounce_event(self, file_path: Path) -> bool:
        """
        Debounce file events to avoid processing the same file multiple times.

        Returns:
            True if event should be processed, False if debounced
        """
        current_time = time.time()
        last_time = self.debounce_map.get(str(file_path), 0)

        if current_time - last_time < self.debounce_delay:
            return False

        self.debounce_map[str(file_path)] = current_time
        return True

    def on_created(self, event: FileSystemEvent):
        """Handle file creation."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if self.should_process_file(file_path) and self.debounce_event(file_path):
            logger.info(f"File created: {file_path}")
            # Schedule coroutine in the event loop
            asyncio.run_coroutine_threadsafe(process_document_file(file_path), self.loop)

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if self.should_process_file(file_path) and self.debounce_event(file_path):
            logger.info(f"File modified: {file_path}")
            # Schedule coroutine in the event loop
            asyncio.run_coroutine_threadsafe(process_document_file(file_path), self.loop)


async def scan_existing_documents(watch_dir: Path):
    """Scan and process all existing documents in watch directory."""
    logger.info(f"Scanning existing documents in {watch_dir}")

    processed_count = 0
    failed_count = 0

    for file_path in watch_dir.rglob('*'):
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

        success = await process_document_file(file_path)
        if success:
            processed_count += 1
        else:
            failed_count += 1

    logger.info(f"Initial scan complete: {processed_count} processed, {failed_count} failed")


async def async_main():
    """Async main function."""
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)

    watch_dir = Path(DOCS_WATCH_DIR)
    if not watch_dir.exists():
        logger.error(f"Watch directory does not exist: {watch_dir}")
        sys.exit(1)

    logger.info(f"Starting document watcher for: {watch_dir.absolute()}")
    logger.info(f"Turbo API URL: {TURBO_API_URL}")

    # Get the current event loop
    loop = asyncio.get_running_loop()

    # Create event handler and observer
    event_handler = DocumentEventHandler(loop)
    observer = Observer()
    observer.schedule(event_handler, str(watch_dir), recursive=True)

    # Start observer
    observer.start()
    logger.info("File watcher started")

    # Scan existing documents
    try:
        await scan_existing_documents(watch_dir)
    except Exception as e:
        logger.error(f"Failed to scan existing documents: {e}", exc_info=True)

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping file watcher...")
        observer.stop()

    observer.join()
    logger.info("File watcher stopped")


def main():
    """Main entry point."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == '__main__':
    main()
