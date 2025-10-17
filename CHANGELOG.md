# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Backend

- **Per-user transcription polling service** that automatically discovers and processes audio files from Azure Blob Storage
  - Each authenticated user gets their own isolated polling service
  - Services auto-start on first user request when `ENABLE_TRANSCRIPTION_POLLING=true`
  - Multiple defensive security checks to prevent cross-user data access
- New methods in `AsyncAzureBlobManager`: `list_blobs_in_prefix()`, `get_blob_metadata()`, `set_blob_metadata()`
- `ENABLE_TRANSCRIPTION_POLLING` environment variable to enable/disable automatic polling (default: false)
- Blob metadata marking system to track processed files and avoid reprocessing
- Per-user polling task management with graceful startup and shutdown

### Changed

#### Backend

- `/start-transcription-job` API endpoint marked as deprecated with comprehensive documentation
- Application startup now supports per-user polling services that start on-demand
- Transcription workflow now supports both API-triggered and auto-discovery modes (expand-contract pattern)
- `get_current_user` dependency now auto-starts polling service for authenticated users

### Security

#### Backend

- **Per-user data isolation**: Each polling service only accesses blobs under `user-uploads/{user_email}/`
- **Defensive prefix checking**: All blob operations verify the path starts with the user's prefix
- **Email validation**: Extracted emails from blob paths are validated against the service's user
- **Security logging**: Failed security checks are logged with detailed context
- Multiple layers of validation to prevent accidental cross-user access

### Technical Details

- Each user's polling service runs independently every 30 seconds when enabled
- On first poll, automatically deletes user's audio blobs older than service startup time
- Only processes files uploaded after the service starts (avoids reprocessing backlog)
- Supports `.mp4`, `.webm`, `.wav`, and `.m4a` audio formats
- Automatically marks blobs as processed using metadata to prevent duplicate processing
- Maintains existing blob deletion behavior after successful transcription
- Zero changes required to existing transcription processing logic
- Polling services are tracked in a global dictionary and cleaned up on app shutdown

### Release Notes

**This feature is complete but unreleased pending frontend integration work.** The polling service is disabled by default (`ENABLE_TRANSCRIPTION_POLLING=false`) to maintain backward compatibility. Frontend changes are required to:
1. Remove API calls to the deprecated `/start-transcription-job` endpoint
2. Rely on automatic processing after audio upload to blob storage
3. Handle "processing" UI state while polling service processes files

Once frontend changes are complete, the polling service can be enabled in production by setting `ENABLE_TRANSCRIPTION_POLLING=true`.

## [0.1.1] - 2025-10-17

### Changed

#### Frontend

- PostHog session recording configuration to selectively mask sensitive content using `ph-mask` class instead of masking all content

## [0.1.0] - 2025-10-16

### Added

#### Backend

- Audio transcription service with Azure Cognitive Services and Deepgram integration
- LLM-powered meeting minutes generation with multiple templates (CRISSA, General Style, Short & Sweet)
- User authentication system with Azure AD Easy Auth and JWT verification
- OID-based user identity validation with case-insensitive comparison
- User management system with email-based allowlisting
- PostgreSQL database integration with SQLModel ORM
- Azure Blob Storage integration for audio file management
- User onboarding workflow with status tracking
- RESTful API built with FastAPI framework
- Comprehensive error handling and logging with Sentry integration
- Database migrations with Alembic

#### Frontend

- Next.js 14 application with React 18
- Audio recording interface with real-time capture
- Audio file upload with drag-and-drop support
- Transcription viewer and editor with rich formatting
- Meeting minutes editor powered by Tiptap rich text editor
- Meeting management interface with history and search
- Multiple minute templates with customizable formatting
- User onboarding flow with step-by-step guidance
- Azure AD authentication integration
- Responsive design with Tailwind CSS
- Real-time status updates for transcription jobs

#### Infrastructure

- Terraform configuration for Azure deployment
- Multi-environment support (development, pre-production, production)
- CI/CD pipeline with GitHub Actions
- Automated testing and code coverage reporting
- Docker containerization for both frontend and backend
- Environment-specific configuration management

