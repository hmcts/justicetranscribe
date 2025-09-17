# Contributing to Justice Transcribe

## Development Workflow

We have two development approaches depending on what you're working on:

### Backend-only Changes

**Use Makefile recipes for faster development:**

**Why:** The Makefile approach uses `npm run dev` which is faster and has more
lenient TypeScript checking, perfect for backend development. It'll also allow
hot reloading for quick iteration on the frontend.

### Frontend Changes (or Full-stack)

**Use Docker Compose for production-like testing:**
```bash
docker compose build    # Build with strict TypeScript compilation
docker compose up       # Run the full stack
```

**Why:** Docker Compose runs `npm run build` which enforces strict TypeScript
compilation and production-ready linting. This catches type errors and
formatting issues that would break CI/CD.

## Before Submitting a PR

- **Backend-only changes:** Makefile testing is sufficient
- **Frontend changes:** Always run `docker compose build` to ensure it passes strict compilation
- **When in doubt:** Use Docker Compose - it mirrors the CI/CD environment

## Testing Onboarding Flow

To test onboarding repeatedly in development:

1. Add to your backend `.env`:
   ```env
   FORCE_ONBOARDING_DEV=true
   ```

2. Restart your backend

3. You'll see a warning banner and onboarding will never be marked "complete"

## After Submitting a PR

1. **Monitor CI/CD workflows** - Check that all automated tests pass
2. **Review Cursor bug bot findings** - Address any exceptions or issues identified in your diff
3. **Fix any pipeline failures** - Resolve build errors, test failures
4. **Only then** Once complete indicate to a colleague that the PR is ready for review
