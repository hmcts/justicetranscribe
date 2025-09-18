# Backend Scripts

This directory contains management scripts for the Justice Transcribe backend.

## User Management

The `user_management.py` script provides utilities for managing users in the database.

### Usage

From the backend directory:

```bash
# List all users
python -m scripts.user_management list

# Reset user onboarding status
python -m scripts.user_management reset developer@localhost.com

# Set specific onboarding status
python -m scripts.user_management set-onboarding developer@localhost.com true

# Show help
python -m scripts.user_management help
```

### Commands

- `list` - List all users in the database with their onboarding status
- `reset <email>` - Reset a user's onboarding status to false (useful for testing)
- `set-onboarding <email> <true|false>` - Set a specific onboarding status
- `help` - Show detailed help information

### Examples

```bash
# See all users
python -m scripts.user_management list

# Reset onboarding for testing
python -m scripts.user_management reset developer@localhost.com

# Mark onboarding as complete
python -m scripts.user_management set-onboarding developer@localhost.com true
```

## Adding New Scripts

When adding new management scripts:

1. Place them in this `scripts/` directory
2. Add an `__init__.py` file if the directory doesn't have one
3. Include a docstring explaining the script's purpose
4. Add a `main()` function for CLI entry point
5. Update this README with usage instructions
