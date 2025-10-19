"""Quick diagnostic script to inspect untitled meetings."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select

from app.database.postgres_database import engine
from app.database.postgres_models import Transcription

with Session(engine) as session:
    query = select(Transcription).where(
        (Transcription.title == "Untitled Meeting") | (Transcription.title == None)  # noqa: E711
    ).order_by(Transcription.created_datetime.desc()).limit(20)

    meetings = session.exec(query).all()

    print(f"\nFound {len(meetings)} untitled meetings (showing first 20):\n")
    print(f"{'ID':<40} {'User ID':<40} {'Created':<30} {'Title'}")
    print("=" * 150)

    for m in meetings:
        title = m.title if m.title else "NULL"
        print(f"{m.id!s:<40} {m.user_id!s:<40} {m.created_datetime.isoformat():<30} {title}")

