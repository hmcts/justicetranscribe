# Transcription Polling Service Refactor

## Summary

Refactored the transcription polling service from a per-user model to a global model that monitors all users' files.

## Key Changes

### 1. TranscriptionPollingService Class (`backend/app/audio/transcription_polling_service.py`)

**Before:** Service was initialized per-user with `user_email` parameter
**After:** Service is initialized once globally without any user parameter

#### Changes Made:
- **`__init__()`**: Removed `user_email` parameter, now monitors entire `user-uploads/` directory
- **`_should_skip_blob()`**: Removed user-specific security checks
- **`poll_for_new_audio_files()`**: Now polls across all users instead of one user
- **`extract_user_email_from_blob_path()`**: Simplified to just extract email without validation
- **`process_discovered_audio()`**: Removes user-specific checks, extracts user from blob path
- **`_mark_blob_with_error()`**: Updated logging to remove user-specific references
- **`_mark_blob_permanently_failed()`**: Updated logging to remove user-specific references
- **`_evaluate_blob_for_cleanup()`**: Simplified blob validation logic
- **`_cleanup_old_blobs_on_startup()`**: Now cleans up across all users
- **`run_polling_loop()`**: Updated to process all users' files

### 2. Dependencies (`backend/utils/dependencies.py`)

**Removed:** Auto-start polling service code from `get_current_user()` function

The dependency function no longer attempts to start individual polling services when users make requests.

### 3. Main Application (`backend/main.py`)

**Before:** 
- Maintained dictionary of per-user polling tasks
- Started new polling service for each user on their first request
- Used threading locks to prevent race conditions

**After:**
- Single global polling task that monitors all users
- Started once at application startup
- Simplified lifecycle management

#### Changes Made:
- Removed `active_polling_tasks` dictionary
- Removed `_polling_tasks_lock` threading lock
- Removed `ensure_user_polling_started()` function
- Updated `lifespan()` to start/stop single global service
- Removed unused `threading` import

## How It Works Now

1. **Application Startup**: A single `TranscriptionPollingService` instance is created and started
2. **Polling**: Service polls the entire `user-uploads/` directory every 30 seconds
3. **Discovery**: For each unprocessed audio file found:
   - Extract user email from subdirectory structure (`user-uploads/{email}/`)
   - Look up user in database
   - Process transcription for that user
4. **Application Shutdown**: Global polling task is cancelled gracefully

## Benefits

- **Simplified Architecture**: One service instead of N services (where N = number of users)
- **Reduced Resource Usage**: Single polling loop instead of multiple concurrent loops
- **No Race Conditions**: No need for threading locks
- **Easier Maintenance**: Single code path for all users
- **Automatic Processing**: All users' files are discovered automatically without requiring user requests

## File Structure Expected

```
user-uploads/
├── user1@example.com/
│   └── recording.mp4
├── user2@example.com/
│   └── audio.wav
└── user3@example.com/
    └── meeting.webm
```

The service extracts the email from the second path component and uses it to identify which user the file belongs to.

