# Allowlist Management Scripts

This directory contains scripts for managing user allowlists across development and production environments.

## Overview

The allowlist system controls who can access the JusticeTranscribe application. Users must have their email addresses in the allowlist stored in Azure Blob Storage (`lookups/allowlist.csv`).

## Scripts

### 1. `munge_allowlist.py` - Full Rebuild

**Purpose:** Rebuilds the entire allowlist from scratch using hardcoded sources (AI Justice Unit team, pilot users, manually onboarded users).

**Usage:**
```bash
# Via Makefile (recommended)
make allowlist-dev      # Rebuild dev allowlist
make allowlist-prod     # Rebuild prod allowlist
make allowlist-both     # Rebuild both

# Direct script usage
python munge_allowlist.py --env dev|prod|both
```

**When to use:**
- Initial setup of allowlists
- Syncing allowlists with source data files
- Complete refresh needed

**Data sources:**
- `data/pilot_users.csv` - Pilot program users
- Hardcoded AI Justice Unit team members
- Hardcoded manually onboarded users

### 2. `create_allowlist_update.py` - Create Timestamped CSV

**Purpose:** Creates a timestamped, compliant CSV file from clipboard/stdin input without uploading.

**Usage:**
```bash
# Via Makefile (recommended)
make allowlist-update-dev PROVIDER="region-name"
make allowlist-update-prod PROVIDER="wales"

# Without provider (uses "unknown" or reads from input)
make allowlist-update-dev

# Direct script usage
python create_allowlist_update.py --env prod --provider "wales"
# Then paste emails and press Ctrl+D
```

**Output:** `data/{env}-allowlist-update-{timestamp}.csv`

**When to use:**
- You want to review the CSV before uploading
- Creating records for documentation
- Need to share the file with others for approval

**Supported input formats:**
```
# Just emails (one per line)
user1@justice.gov.uk
user2@justice.gov.uk

# Comma-separated
user1@justice.gov.uk, user2@justice.gov.uk

# CSV with providers
user1@justice.gov.uk,wales
user2@justice.gov.uk,kss
user3@justice.gov.uk,         # Empty provider becomes "unknown"
```

**Data quality features:**
- Removes leading `\n` line breaks
- Removes trailing `>` characters
- Converts to lowercase
- Removes duplicates
- Validates email format

### 3. `merge_and_upload_allowlist.py` - Merge and Upload

**Purpose:** Merges a local allowlist file with the existing Azure allowlist and uploads the result.

**Usage:**
```bash
# Via Makefile (recommended)
make allowlist-merge-dev FILE=data/dev-allowlist-update-2025-10-08_12-06-24.csv
make allowlist-merge-prod FILE=data/prod-allowlist-update-2025-10-08_14-30-00.csv

# Direct script usage
python merge_and_upload_allowlist.py --env prod --file ../../data/prod-allowlist-update-2025-10-08_14-30-00.csv

# Dry run (validate but don't upload)
python merge_and_upload_allowlist.py --env dev --file ../../data/dev-update.csv --dry-run
```

**When to use:**
- After reviewing a timestamped CSV file
- Merging existing files with Azure allowlist
- Need detailed merge statistics

**Features:**
- Downloads current allowlist from Azure
- Validates both local and remote data
- Merges and deduplicates (existing users take precedence)
- Maintains chronological order (existing first, new appended)
- Uploads merged result back to Azure

**Data quality checks:**
- ❌ No null values in email or provider
- ❌ No leading line breaks in emails
- ❌ No trailing `>` characters
- ❌ Email format validation (must contain `@` and `.`)
- ✅ Automatic cleaning and normalization
- ✅ Duplicate detection and removal

## Workflows

### Workflow 1: One-Step Upload (Fast Path)

**Use case:** Quick updates, trusted sources, development environment

```bash
# Create and upload in one command
make allowlist-upload-dev PROVIDER="new-region"
# Paste emails, press Ctrl+D
# ✅ Done! Updated in Azure
```

**What happens:**
1. Reads emails from stdin
2. Creates timestamped CSV with validation
3. Downloads existing allowlist from Azure
4. Merges and validates
5. Uploads to Azure

**Pros:** Fast, single command
**Cons:** No manual review step

### Workflow 2: Two-Step Review (Careful Path)

**Use case:** Production updates, need approval, want to review first

```bash
# Step 1: Create timestamped CSV
make allowlist-update-prod PROVIDER="wales"
# Paste emails, press Ctrl+D
# Output: data/prod-allowlist-update-2025-10-08_14-30-00.csv

# Step 2: Review the file
cat data/prod-allowlist-update-2025-10-08_14-30-00.csv

# Step 3: Upload to Azure
make allowlist-merge-prod FILE=data/prod-allowlist-update-2025-10-08_14-30-00.csv
```

**What happens:**
1. Creates validated CSV file locally
2. You manually review it
3. Merges with Azure and uploads

**Pros:** Manual review, audit trail
**Cons:** Extra steps

### Workflow 3: Full Rebuild (Complete Refresh)

**Use case:** Syncing with source data, initial setup, major changes

```bash
# Update source data first
vim data/pilot_users.csv

# Rebuild from sources
make allowlist-prod
```

**What happens:**
1. Loads data from `pilot_users.csv` and hardcoded sources
2. Combines and deduplicates
3. Uploads to Azure

**Pros:** Single source of truth
**Cons:** Requires editing source files

## Environment Variables

Required in `.env` file:

```bash
AZURE_STORAGE_CONTAINER_NAME=justicetranscribe
AZURE_STORAGE_CONNECTION_STRING=<dev-connection-string>
AZURE_STORAGE_CONNECTION_STRING_PROD=<prod-connection-string>
```

## File Format

All scripts work with CSV files in this format:

```csv
email,provider
user1@justice.gov.uk,wales
user2@justice.gov.uk,kss
user3@justice.gov.uk,unknown
```

**Fields:**
- `email` - User's email address (lowercase, validated)
- `provider` - Region/provider identifier (lowercase)

## Safety Features

### Production Safeguards
- Confirmation prompts for prod updates
- No accidental deletions (only adds/merges)
- Existing data preserved on duplicates
- Detailed merge statistics

### Data Validation
- Strict email format checking
- No null/empty values allowed
- Automatic cleaning of malformed data
- Duplicate detection

### Audit Trail
- Timestamped filenames
- Merge statistics logged
- Original files preserved in `data/` directory

## Common Tasks

### Adding New Users to Production

**Option A - Fast:**
```bash
make allowlist-upload-prod PROVIDER="new-region"
# Paste emails, Ctrl+D
```

**Option B - Careful:**
```bash
make allowlist-update-prod PROVIDER="new-region"
# Paste emails, Ctrl+D
# Review: cat data/prod-allowlist-update-2025-10-08_14-30-00.csv
make allowlist-merge-prod FILE=data/prod-allowlist-update-2025-10-08_14-30-00.csv
```

### Adding Mixed Provider Users

```bash
make allowlist-upload-dev
# Paste in CSV format:
# user1@justice.gov.uk,wales
# user2@justice.gov.uk,kss
# user3@justice.gov.uk,unknown
# Ctrl+D
```

### Testing in Development

```bash
make allowlist-upload-dev PROVIDER="test"
# Paste test emails
```

### Checking Current Allowlist

You can download and view the current allowlist using Azure Storage Explorer or:

```bash
# Use Azure CLI
az storage blob download \
  --account-name <account> \
  --container-name justicetranscribe \
  --name lookups/allowlist.csv \
  --file current-allowlist.csv
```

## Troubleshooting

### "Email format invalid"
- Ensure emails contain `@` and `.`
- Remove any special characters
- Check for hidden line breaks

### "Null provider values"
- Provide `PROVIDER` argument or
- Use CSV format with provider column or
- Accept "unknown" as default

### "File not found"
- Use relative path from repo root
- Check filename timestamp is correct
- Ensure file exists: `ls data/`

### "Connection string not found"
- Check `.env` file exists
- Verify `AZURE_STORAGE_CONNECTION_STRING` (dev) or `AZURE_STORAGE_CONNECTION_STRING_PROD` set
- Ensure `.env` is in repo root

## Architecture Notes

### Chronological Order
The allowlist maintains insertion order to represent onboarding timeline:
- Existing users stay in their original order
- New users are appended to the end
- No alphabetical sorting applied

### Duplicate Handling
When merging:
- Existing emails take precedence
- First occurrence kept (by email, case-insensitive)
- Provider from existing entry preserved

### Headers
- New files include `email,provider` header
- Scripts automatically detect and handle headers
- Azure upload format matches existing structure

## Dependencies

All scripts require:
- `pandas` - Data manipulation
- `azure-storage-blob` - Azure Blob Storage client
- `python-dotenv` - Environment variable management
- `pyprojroot` - Project root detection

Install via:
```bash
cd backend && uv sync
```

