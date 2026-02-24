#!/usr/bin/env python3
"""
Emoji cleanup script for Turbo documentation and code.
Removes all emoji characters from specified files and directories.
"""

import argparse
import os
from pathlib import Path
import re


def get_emoji_pattern():
    """
    Create regex pattern to match emoji characters.
    Covers most common emoji ranges in Unicode.
    """
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # emoticons
        "\U0001f300-\U0001f5ff"  # symbols & pictographs
        "\U0001f680-\U0001f6ff"  # transport & map symbols
        "\U0001f1e0-\U0001f1ff"  # flags (iOS)
        "\U00002702-\U000027b0"  # dingbats
        "\U000024c2-\U0001f251"  # enclosed characters
        "\U0001f900-\U0001f9ff"  # supplemental symbols
        "\U0001fa70-\U0001faff"  # symbols and pictographs extended-A
        "\U00002600-\U000026ff"  # miscellaneous symbols
        "\U00002700-\U000027bf"  # dingbats
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern


def clean_file_content(content: str) -> tuple[str, int]:
    """
    Remove emoji from file content.
    Returns cleaned content and count of removed emoji.
    """
    emoji_pattern = get_emoji_pattern()

    # Find all emoji matches for counting
    emoji_matches = emoji_pattern.findall(content)
    emoji_count = len(emoji_matches)

    # Remove emoji
    cleaned_content = emoji_pattern.sub("", content)

    # Clean up any multiple spaces that might result, but preserve line breaks
    # Replace multiple spaces (but not newlines) with single space
    cleaned_content = re.sub(r"[^\S\n]+", " ", cleaned_content)

    # Clean up any multiple consecutive newlines (more than 2)
    cleaned_content = re.sub(r"\n{3,}", "\n\n", cleaned_content)

    return cleaned_content, emoji_count


def should_process_file(file_path: Path, include_extensions: set[str]) -> bool:
    """
    Check if file should be processed based on extension.
    """
    if not include_extensions:
        return True

    return file_path.suffix.lower() in include_extensions


def clean_file(file_path: Path, dry_run: bool = False) -> tuple[bool, int]:
    """
    Clean emoji from a single file.
    Returns (was_modified, emoji_count).
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            original_content = f.read()

        cleaned_content, emoji_count = clean_file_content(original_content)

        if emoji_count > 0:
            if not dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(cleaned_content)
            return True, emoji_count

        return False, 0

    except UnicodeDecodeError:
        print(f"Warning: Could not decode {file_path} as UTF-8, skipping")
        return False, 0
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, 0


def clean_directory(
    directory: Path,
    include_extensions: set[str],
    exclude_dirs: set[str],
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Recursively clean emoji from all files in directory.
    Returns (files_modified, total_emoji_removed).
    """
    files_modified = 0
    total_emoji_removed = 0

    for root, dirs, files in os.walk(directory):
        root_path = Path(root)

        # Remove excluded directories from dirs list to prevent walking into them
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            file_path = root_path / file

            if should_process_file(file_path, include_extensions):
                was_modified, emoji_count = clean_file(file_path, dry_run)

                if was_modified:
                    files_modified += 1
                    total_emoji_removed += emoji_count
                    action = "Would clean" if dry_run else "Cleaned"
                    print(f"{action} {file_path}: removed {emoji_count} emoji")

    return files_modified, total_emoji_removed


def main():
    parser = argparse.ArgumentParser(
        description="Remove emoji from files in Turbo project"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to clean (default: current directory)",
    )
    parser.add_argument(
        "--extensions",
        "-e",
        nargs="*",
        default=[".md", ".py", ".txt", ".rst", ".json", ".yaml", ".yml", ".toml"],
        help="File extensions to process (default: common text files)",
    )
    parser.add_argument(
        "--exclude-dirs",
        nargs="*",
        default=[".git", ".venv", "__pycache__", "node_modules", ".idea"],
        help="Directories to exclude from processing",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be cleaned without making changes",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )

    args = parser.parse_args()

    include_extensions = set(args.extensions) if args.extensions else set()
    exclude_dirs = set(args.exclude_dirs)

    total_files_modified = 0
    total_emoji_removed = 0

    for path_str in args.paths:
        path = Path(path_str)

        if not path.exists():
            print(f"Error: {path} does not exist")
            continue

        if path.is_file():
            if should_process_file(path, include_extensions):
                was_modified, emoji_count = clean_file(path, args.dry_run)
                if was_modified:
                    total_files_modified += 1
                    total_emoji_removed += emoji_count
                    action = "Would clean" if args.dry_run else "Cleaned"
                    print(f"{action} {path}: removed {emoji_count} emoji")
            elif args.verbose:
                print(f"Skipped {path}: extension not in include list")

        elif path.is_dir():
            files_modified, emoji_removed = clean_directory(
                path, include_extensions, exclude_dirs, args.dry_run
            )
            total_files_modified += files_modified
            total_emoji_removed += emoji_removed

    # Summary
    action = "Would modify" if args.dry_run else "Modified"
    print(
        f"\nSummary: {action} {total_files_modified} files, "
        f"removed {total_emoji_removed} emoji total"
    )

    if args.dry_run and total_emoji_removed > 0:
        print("Run without --dry-run to apply changes")


if __name__ == "__main__":
    main()
