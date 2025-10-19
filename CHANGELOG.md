# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Backend

- **Per-user transcription polling service** that automatically discovers and processes audio files from Azure Blob Storage
- New methods in `AsyncAzureBlobManager`: `list_blobs_in_prefix()`, `get_blob_metadata()`, `set_blob_metadata()`
- Retry tracking system using blob metadata (`retry_count`, `status`, `last_error`, `last_attempt`)
- Blob metadata marking to track processed files, retry attempts, and permanently failed jobs
- Cleanup utility scripts: `delete_null_title_meetings.py` and `inspect_meetings.py`

### Changed

#### Backend

- `/start-transcription-job` API endpoint marked as deprecated
- Transcription workflow now supports both API-triggered and auto-discovery modes (expand-contract pattern)
- `get_current_user` dependency now auto-starts polling service for authenticated users
- Retry logic refactored: blob download retries (3 attempts) separate from transcription API retries (2 attempts max)

### Fixed

#### Backend

- Duplicate transcription records no longer created on retry failures - database save now deferred until after successful audio processing
- Polling service retry limit set to 2 attempts (1 retry max) to prevent duplicate record creation

### Release Notes

1. Remove API calls to the deprecated `/start-transcription-job` endpoint
2. Rely on automatic processing after audio upload to blob storage
3. Handle "processing" UI state while polling service processes files

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

