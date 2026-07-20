import sys
import json
import time
from pathlib import Path
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from functools import wraps

# Ensure python looks in the right directory for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import FLASK_SECRET_KEY, FLASK_DEBUG, FLASK_PORT, OLLAMA_BASE_URL, LLM_MODEL, LLM_TEMPERATURE
from src.RAG_chain import build_rag_chain, build_streaming_chain, PROMPT
from src.vectorstore import load_vectorstore, get_retriever
from src.auth import register_user, login_user, verify_token
from src.chat_store import (
    create_session, get_sessions, update_session_title,
    delete_session, save_message, get_messages
)
from src.logger import get_logger

log = get_logger(__name__)

# --- Authentication Middleware ---
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'missing or invalid token'}), 401

        token = auth_header.split(' ')[1]
        result = verify_token(token)

        if not result.get('valid'):
            return jsonify({'error': result.get('error')}), 401

        request.user_id = result.get('user_id')
        request.user_email = result.get('email')

        return f(*args, **kwargs)
    return decorated


# --- App Factory Initialization ---
def create_app():
    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    log.info("Initializing the rag pipeline")
    try:
        vs = load_vectorstore()
        retriever = get_retriever(vs)
        chain = build_rag_chain(retriever)
        
        app.config['chain'] = chain
        app.config['retriever'] = retriever
        log.info("rag pipeline is ready")
    except Exception as e:
        log.error(f"failed to init rag pipeline: {e}")
        app.config['chain'] = None
        app.config['retriever'] = None

    return app

app = create_app()


# --- API Routes ---

@app.route('/health', methods=['GET'])
def health():
    ready = app.config.get('chain') is not None
    return jsonify({'status': 'ok', 'ready': ready})

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    full_name = data.get('full_name', '').strip()

    if not email or not password or not full_name:
        return jsonify({'error': 'all fields are required'}), 400

    result = register_user(email, password, full_name)
    if not result.get('success'):
        return jsonify({'error': result.get('error')}), 400

    log.info(f"new user is registered with {email}")
    return jsonify(result), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({'error': 'email and password are required'}), 400

    result = login_user(email, password)
    if not result.get('success'):
        return jsonify({'error': result.get('error')}), 401
    
    return jsonify(result), 200

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_me():
    return jsonify({'user_id': request.user_id, 'email': request.user_email})

@app.route('/api/sessions', methods=['GET'])
@require_auth
def list_sessions():
    sessions = get_sessions(request.user_id)
    return jsonify({'sessions': sessions})

@app.route('/api/sessions', methods=['POST'])
@require_auth
def new_session():
    data = request.get_json(silent=True) or {}
    title = data.get('title', 'New Chat')
    session = create_session(request.user_id, title)
    return jsonify(session), 201

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
@require_auth
def remove_session(session_id):
    delete_session(session_id, request.user_id)
    return jsonify({'success': True})

@app.route('/api/sessions/<session_id>/messages', methods=['GET'])
@require_auth
def list_messages(session_id):
    messages = get_messages(session_id)
    return jsonify({'messages': messages})

@app.route('/api/chat/stream', methods=['POST'])
@require_auth
def chat_stream():
    retriever = app.config.get('retriever')
    if retriever is None:
        return jsonify({'error': 'rag pipeline not ready'}), 503

    data = request.get_json(silent=True) or {}
    question = data.get('question', '').strip()
    session_id = data.get('session_id', '').strip()

    if not question or not session_id:
        return jsonify({'error': 'invalid request'}), 400
    if len(question) > 2000:
        return jsonify({'error': 'question is too long'}), 400

    save_message(session_id, 'user', question)

    sessions = get_sessions(request.user_id)
    current = next((s for s in sessions if s.get('id') == session_id), None)
    
    if current and current.get('title') == 'New Chat':
        title = question[:50] + ('...' if len(question) > 50 else '')
        update_session_title(session_id, title)

    from langchain_ollama import ChatOllama

    def generate():
        try:
            docs = retriever.invoke(question)
            context = "\n".join([doc.page_content for doc in docs])
            
            sources = []
            seen = set()
            for doc in docs:
                page = doc.metadata.get('page', '?')
                if page not in seen:
                    seen.add(page)
                    preview = doc.page_content[:150].replace('\n', ' ')
                    sources.append({'page': page, 'preview': preview})

            llm = ChatOllama(
                model=LLM_MODEL, 
                base_url=OLLAMA_BASE_URL, 
                temperature=LLM_TEMPERATURE
            )
            
            full_prompt = PROMPT.format(context=context, input=question)
            
            full_answer = ""
            for chunk in llm.stream(full_prompt):
                if chunk.content:
                    full_answer += chunk.content
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
            
            save_message(session_id, 'bot', full_answer, sources=sources)
            
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            log.error(f"streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()), 
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'route not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'internal server error'}), 500


if __name__ == '__main__':
    log.info(f"medbot starting on port {FLASK_PORT}")
    app.run(host='0.0.0.0', port=int(FLASK_PORT), debug=FLASK_DEBUG)