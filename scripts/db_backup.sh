#!/bin/bash

# Simple database backup using the postgres container
# Creates a SQL dump of the database

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Default output
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="./backups"
OUTPUT="${BACKUP_DIR}/turbo_backup_${TIMESTAMP}.sql"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --output|-o)
      OUTPUT="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: ./scripts/db_backup.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --output, -o PATH   Output file path (default: ./backups/turbo_backup_TIMESTAMP.sql)"
      echo "  --help, -h          Show this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

# Create backup directory
mkdir -p "$(dirname "$OUTPUT")"

echo -e "${BLUE}Creating database backup...${NC}"

# Use the postgres container to dump the database
docker exec turbo-postgres pg_dump -U turbo -d turbo > "$OUTPUT"

if [ $? -eq 0 ]; then
  SIZE=$(ls -lh "$OUTPUT" | awk '{print $5}')
  echo -e "${GREEN}✓ Backup created successfully${NC}"
  echo -e "  Location: $OUTPUT"
  echo -e "  Size: $SIZE"
else
  echo -e "${RED}✗ Backup failed${NC}"
  exit 1
fi