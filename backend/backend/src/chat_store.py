import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

# Ensure python looks in the right directory for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from src.logger import get_logger
from supabase import create_client

log = get_logger(__name__)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def create_session(user_id: str, title: str = "New Chat"):
    result = supabase.table('chat_sessions').insert({
        'user_id': user_id,
        'title': title
    }).execute()
    session = result.data[0]
    log.info(f"session created {session['id']} for user {user_id}")
    return session

def get_sessions(user_id: str) -> List:
    result = supabase.table('chat_sessions').select('*').eq('user_id', user_id).order('updated_at', desc=True).execute()
    return result.data

def update_session_title(session_id: str, title: str):
    supabase.table('chat_sessions').update({
        'title': title,
        'updated_at': datetime.now(timezone.utc).isoformat()
    }).eq('id', session_id).execute()
    log.info(f"session title updated")

def delete_session(session_id: str, user_id: str) -> bool:
    result = supabase.table('chat_sessions').delete().eq('id', session_id).eq('user_id', user_id).execute()
    log.info(f"session deleted {session_id}")
    return True

def save_message(session_id: str, role: str, content: str, sources: Optional[List] = None, duration_ms: Optional[int] = None):
    result = supabase.table('messages').insert({
        'session_id': session_id,
        'role': role,
        'content': content,
        'sources': sources,
        'duration_ms': duration_ms
    }).execute()
    log.info(f"message saved {role} in session {session_id}")
    return result.data[0]

def get_messages(session_id: str):
    result = supabase.table('messages').select('*').eq('session_id', session_id).order('created_at').execute()
    return result.data