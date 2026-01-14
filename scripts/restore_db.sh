#!/bin/bash

# Database restore script for Turbo
# Restores a PostgreSQL database from backup

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backup file is provided
if [ $# -eq 0 ]; then
  echo -e "${RED}Error: No backup file specified${NC}"
  echo ""
  echo "Usage: ./scripts/restore_db.sh BACKUP_FILE [--confirm]"
  echo ""
  echo "Arguments:"
  echo "  BACKUP_FILE    Path to the backup file to restore"
  echo "  --confirm      Skip confirmation prompt (use with caution!)"
  echo ""
  echo "Examples:"
  echo "  ./scripts/restore_db.sh ./backups/turbo_backup_20240108_120000.sql --confirm"
  exit 1
fi

BACKUP_FILE="$1"
CONFIRM_FLAG=""

# Check if --confirm flag is provided
if [ "$2" == "--confirm" ]; then
  CONFIRM_FLAG="--confirm"
else
  # Show warning and ask for confirmation
  echo -e "${YELLOW}⚠️  WARNING: This will overwrite all existing data!${NC}"
  echo -e "${YELLOW}Database will be restored from: $BACKUP_FILE${NC}"
  echo ""
  read -p "Are you sure you want to continue? (yes/no): " -r
  echo
  if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${BLUE}Restore cancelled${NC}"
    exit 0
  fi
  CONFIRM_FLAG="--confirm"
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
  echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
  exit 1
fi

echo -e "${BLUE}Restoring database...${NC}"

# Execute the restore
if docker exec turbo-api python -m turbo.cli.main db restore "$BACKUP_FILE" $CONFIRM_FLAG; then
  echo -e "${GREEN}✓ Restore completed successfully${NC}"
else
  echo -e "${RED}✗ Restore failed${NC}"
  exit 1
fi