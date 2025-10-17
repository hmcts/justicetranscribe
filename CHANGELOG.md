# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

