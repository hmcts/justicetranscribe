# Allowlist Management Recipes - Quick Reference

This is a clear, practical guide to the allowlist management recipes available in the Makefile.

## 🎯 The Recipe You're Looking For

**YES!** There is a recipe that accepts a `FILE=data/...` argument to append to the existing lookup:

```bash
# Merge existing file with Azure allowlist and upload
make allowlist-merge-dev FILE=data/your-file.csv
make allowlist-merge-prod FILE=data/your-file.csv
```

This downloads the current Azure allowlist, merges it with your local file, and uploads the combined result.

---

## 📋 Complete Recipe Reference

### 1. **Full Rebuild** (Complete Refresh)
```bash
make allowlist-dev      # Rebuild dev allowlist from source data
make allowlist-prod     # Rebuild prod allowlist from source data  
make allowlist-both     # Rebuild both environments
```
**What it does:** Rebuilds entire allowlist from scratch using hardcoded sources (AI Justice Unit team, pilot users, manually onboarded users).

**When to use:** Initial setup, syncing with source data, major changes.

---

### 2. **Create Timestamped CSV** (Review First)
```bash
make allowlist-update-dev [PROVIDER="region-name"]
make allowlist-update-prod [PROVIDER="region-name"]
```
**What it does:** Creates a timestamped CSV file from your input (clipboard/stdin) but doesn't upload it.

**Example:**
```bash
make allowlist-update-prod PROVIDER="wales"
# Then paste emails and press Ctrl+D
# Output: data/prod-allowlist-update-2025-10-08_14-30-00.csv
```

**When to use:** When you want to review the CSV before uploading, need approval, or want to share the file.

---

### 3. **Merge & Upload** ⭐ (The One You Want)
```bash
make allowlist-merge-dev FILE=data/your-file.csv
make allowlist-merge-prod FILE=data/your-file.csv
```
**What it does:** 
1. Downloads current allowlist from Azure
2. Merges it with your local file
3. Uploads the combined result back to Azure

**Example:**
```bash
make allowlist-merge-prod FILE=data/prod-allowlist-update-2025-10-08_14-30-00.csv
```

**When to use:** After reviewing a timestamped CSV file, merging existing files with Azure allowlist.

**Features:**
- ✅ Preserves existing users (no deletions)
- ✅ Adds new users from your file
- ✅ Removes duplicates (existing takes precedence)
- ✅ Maintains chronological order
- ✅ Detailed merge statistics

---

### 4. **One-Step Upload** (Fast Path)
```bash
make allowlist-upload-dev [PROVIDER="region-name"]
make allowlist-upload-prod [PROVIDER="region-name"]
```
**What it does:** Creates timestamped CSV from stdin AND uploads it in one command.

**Example:**
```bash
make allowlist-upload-prod PROVIDER="wales"
# Paste emails, press Ctrl+D
# ✅ Done! Updated in Azure
```

**When to use:** Quick updates, trusted sources, development environment.

---

### 5. **Deduplication**
```bash
make allowlist-dedupe-dev
make allowlist-dedupe-prod
```
**What it does:** Removes duplicate emails from the Azure allowlist.

**When to use:** When you suspect there are duplicates in the current allowlist.

---

## 🔄 Common Workflows

### Workflow A: Quick Add (Fast)
```bash
make allowlist-upload-prod PROVIDER="new-region"
# Paste emails, Ctrl+D
# ✅ Done!
```

### Workflow B: Review First (Careful)
```bash
# Step 1: Create file
make allowlist-update-prod PROVIDER="wales"
# Paste emails, Ctrl+D

# Step 2: Review
cat data/prod-allowlist-update-2025-10-08_14-30-00.csv

# Step 3: Upload
make allowlist-merge-prod FILE=data/prod-allowlist-update-2025-10-08_14-30-00.csv
```

### Workflow C: Use Existing File
```bash
# You have a file already
make allowlist-merge-prod FILE=data/your-existing-file.csv
```

---

## 📁 File Format

All files should be CSV with this format:
```csv
email,provider
user1@justice.gov.uk,wales
user2@justice.gov.uk,kss
user3@justice.gov.uk,unknown
```

**Supported input formats:**
- Just emails (one per line)
- Comma-separated emails
- CSV with providers
- Mixed formats (script handles it)

---

## ⚠️ Safety Features

- **Production prompts:** Confirmation required for prod updates
- **No deletions:** Only adds/merges, never removes existing users
- **Data validation:** Strict email format checking, duplicate removal
- **Audit trail:** Timestamped filenames, merge statistics

---

## 🚨 Error Messages

| Error | Solution |
|-------|----------|
| `FILE is required` | Use: `make allowlist-merge-dev FILE=data/your-file.csv` |
| `File not found` | Check file path: `ls data/` |
| `Email format invalid` | Ensure emails contain `@` and `.` |
| `Connection string not found` | Check `.env` file has `AZURE_STORAGE_CONNECTION_STRING` |

---

## 💡 Pro Tips

1. **Always test in dev first:**
   ```bash
   make allowlist-merge-dev FILE=data/your-file.csv
   ```

2. **Use dry-run for testing:**
   ```bash
   cd scripts/allowlist
   python merge_and_upload_allowlist.py --env prod --file ../../data/your-file.csv --dry-run
   ```

3. **Check merge statistics:** The merge command shows exactly what it's doing:
   ```
   📈 Merge statistics:
      - Existing users: 150
      - New file users: 25
      - Truly new users: 20
      - Duplicates removed: 5
      - Final total: 170
   ```

4. **File paths:** Always use relative paths from repo root:
   ```bash
   make allowlist-merge-prod FILE=data/prod-allowlist-update-2025-10-08_14-30-00.csv
   ```

---

## 🎯 Quick Answer to Your Question

**YES!** The recipe you're looking for is:

```bash
make allowlist-merge-dev FILE=data/your-file.csv
make allowlist-merge-prod FILE=data/your-file.csv
```

This will append your file to the existing Azure allowlist and upload the combined result.
