#!/usr/bin/env python3
"""
User Management Scripts for Justice Transcribe

This module provides command-line utilities for managing users in the database.
Useful for development, testing, and administrative tasks.

Usage:
    python -m scripts.user_management list                    # List all users
    python -m scripts.user_management reset <email>           # Reset user onboarding
    python -m scripts.user_management set-onboarding <email> <true|false>  # Set onboarding status
"""
import os
import sys
from uuid import UUID

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.interface_functions import get_user_by_id, update_user
from app.database.postgres_database import engine
from sqlmodel import Session, select
from app.database.postgres_models import User


def reset_user_onboarding(email: str) -> bool:
    """Reset onboarding status for a user by email"""
    with Session(engine) as session:
        # Find user by email
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        
        if not user:
            print(f"❌ User with email '{email}' not found")
            return False
            
        print(f"📧 Found user: {user.email}")
        print(f"🆔 User ID: {user.id}")
        print(f"📊 Current onboarding status: {user.has_completed_onboarding}")
        
        # Reset onboarding status
        user.has_completed_onboarding = False
        session.add(user)
        session.commit()
        session.refresh(user)
        
        print(f"✅ Reset onboarding status to: {user.has_completed_onboarding}")
        return True


def set_user_onboarding(email: str, completed: bool) -> bool:
    """Set onboarding status for a user by email"""
    with Session(engine) as session:
        # Find user by email
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        
        if not user:
            print(f"❌ User with email '{email}' not found")
            return False
            
        print(f"📧 Found user: {user.email}")
        print(f"🆔 User ID: {user.id}")
        print(f"📊 Current onboarding status: {user.has_completed_onboarding}")
        
        # Set onboarding status
        user.has_completed_onboarding = completed
        session.add(user)
        session.commit()
        session.refresh(user)
        
        print(f"✅ Set onboarding status to: {user.has_completed_onboarding}")
        return True


def list_all_users():
    """List all users in the database"""
    with Session(engine) as session:
        statement = select(User)
        users = session.exec(statement).all()
        
        print("👥 All users in database:")
        if not users:
            print("  (No users found)")
            return
            
        for user in users:
            status = "✅ Completed" if user.has_completed_onboarding else "⏳ Pending"
            print(f"  - {user.email} (ID: {user.id}, Onboarding: {status})")


def show_help():
    """Show help information"""
    print("""
🔧 Justice Transcribe User Management

Commands:
  list                           List all users in the database
  reset <email>                  Reset user onboarding status to false
  set-onboarding <email> <bool>  Set specific onboarding status (true/false)
  help                           Show this help message

Examples:
  python -m scripts.user_management list
  python -m scripts.user_management reset developer@localhost.com
  python -m scripts.user_management set-onboarding developer@localhost.com true
  python -m scripts.user_management help
""")


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        list_all_users()
    elif command == "reset":
        if len(sys.argv) < 3:
            print("❌ Please provide an email address")
            print("Usage: python -m scripts.user_management reset <email>")
            sys.exit(1)
        email = sys.argv[2]
        reset_user_onboarding(email)
    elif command == "set-onboarding":
        if len(sys.argv) < 4:
            print("❌ Please provide an email address and boolean value")
            print("Usage: python -m scripts.user_management set-onboarding <email> <true|false>")
            sys.exit(1)
        email = sys.argv[2]
        completed_str = sys.argv[3].lower()
        if completed_str not in ["true", "false"]:
            print("❌ Boolean value must be 'true' or 'false'")
            sys.exit(1)
        completed = completed_str == "true"
        set_user_onboarding(email, completed)
    elif command == "help":
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
