#!/usr/bin/env python3
"""
Remove all emojis from document content in the database.
"""

import asyncio
import re

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from turbo.core.database.connection import get_db_session
from turbo.core.repositories import DocumentRepository
from turbo.core.schemas.document import DocumentUpdate

console = Console()


def remove_emojis(text: str) -> str:
    """Remove all emojis from text."""
    # Emoji pattern - covers most emoji ranges
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FAFF"  # extended symbols
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text)


async def clean_documents():
    """Remove emojis from all documents."""
    async for session in get_db_session():
        repo = DocumentRepository(session)

        # Get all documents
        documents = await repo.get_all()
        console.print(f"[cyan]Found {len(documents)} documents to check[/cyan]\n")

        updated_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Cleaning documents...", total=len(documents))

            for doc in documents:
                original_content = doc.content
                cleaned_content = remove_emojis(original_content)

                if original_content != cleaned_content:
                    # Update document
                    update_data = DocumentUpdate(content=cleaned_content)
                    await repo.update(doc.id, update_data)
                    updated_count += 1
                    console.print(f"[yellow]Cleaned: {doc.title}[/yellow]")

                progress.advance(task)

        await session.commit()

        console.print(f"\n[green]Done! Updated {updated_count} documents[/green]")
        console.print(f"[dim]{len(documents) - updated_count} documents had no emojis[/dim]")


if __name__ == "__main__":
    asyncio.run(clean_documents())
