#!/bin/bash

# Database backup script for Turbo
# Creates a backup of the PostgreSQL database

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
FORMAT="sql"
OUTPUT=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --format)
      FORMAT="$2"
      shift 2
      ;;
    --output)
      OUTPUT="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: ./scripts/backup_db.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --format FORMAT    Backup format (sql, custom, tar). Default: sql"
      echo "  --output PATH      Output file path. Default: ./backups/turbo_backup_TIMESTAMP.sql"
      echo "  --help, -h         Show this help message"
      echo ""
      echo "Examples:"
      echo "  ./scripts/backup_db.sh"
      echo "  ./scripts/backup_db.sh --format custom --output /path/to/backup.dump"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}Creating database backup...${NC}"

# Build the command
CMD="docker exec turbo-api python -m turbo.cli.main db backup --format $FORMAT"

if [ -n "$OUTPUT" ]; then
  CMD="$CMD --output $OUTPUT"
fi

# Execute the backup
if eval $CMD; then
  echo -e "${GREEN}✓ Backup completed successfully${NC}"
else
  echo -e "${RED}✗ Backup failed${NC}"
  exit 1
fi