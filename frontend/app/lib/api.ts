import Cookies from "js-cookie";

const TOKEN_KEY = "medbot_token";
const USER_KEY = "medbot_user";
const backendURL = process.env.NEXT_PUBLIC_BACKEND_URL;

export interface User {
    id: string;
    email: string;
    full_name: string;
}

export interface Session {
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
}

export interface Source {
    page: string;
    preview: string;
}

export interface ChatMessage {
    id: string;
    role: "user" | "bot";
    content: string;
    sources?: Source[];
    duration_ms?: number;
}

export function saveAuth(token: string, user: User) {
    Cookies.set(TOKEN_KEY, token, { expires: 1 });
    Cookies.set(USER_KEY, JSON.stringify(user), { expires: 1 });
}

export function getToken(): string | undefined {
    return Cookies.get(TOKEN_KEY);
}

export function getUser(): User | null {
    const raw = Cookies.get(USER_KEY);
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch {
        return null;
    }
}

export function isLoggedIn(): boolean {
    return !!getToken();
}

export function logout(): void {
    Cookies.remove(TOKEN_KEY);
    Cookies.remove(USER_KEY);
}

const getAuthHeaders = () => {
    const token = getToken();
    return {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {})
    };
};

export async function apiRegister(email: string, password: string, full_name: string) {
    const result = await fetch(`${backendURL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, full_name })
    });
    return result.json();
}

export async function apiLogin(email: string, password: string) {
    const result = await fetch(`${backendURL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });
    return result.json();
}

export async function fetchSessions(): Promise<Session[]> {
    const result = await fetch(`${backendURL}/api/sessions`, {
        headers: getAuthHeaders()
    });
    const data = await result.json();
    return data.sessions || [];
}

export async function createSession(title: string): Promise<Session> {
    const result = await fetch(`${backendURL}/api/sessions`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ title })
    });
    return result.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
    await fetch(`${backendURL}/api/sessions/${sessionId}`, {
        method: "DELETE",
        headers: getAuthHeaders()
    });
}

export async function fetchMessages(sessionId: string): Promise<ChatMessage[]> {
    const result = await fetch(`${backendURL}/api/sessions/${sessionId}/messages`, {
        headers: getAuthHeaders()
    });
    const data = await result.json();
    return data.messages || [];
}

export async function streamMessage(
    question: string,
    sessionId: string,
    onToken: (token: string) => void,
    onSources: (sources: Source[]) => void,
    onDone: () => void,
    onError: (error: string) => void
): Promise<void> {
    const result = await fetch(`${backendURL}/api/chat/stream`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ question, session_id: sessionId })
    });

    if (!result.ok) {
        onError("Failed to connect to the server");
        return;
    }

    const reader = result.body?.getReader();
    const decoder = new TextDecoder();
    
    if (!reader) {
        onError("No response body");
        return;
    }

    let buffer = "";
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
                const data = JSON.parse(line.slice(6));
                if (data.type === "token") {
                    onToken(data.content);
                } else if (data.type === "sources") {
                    onSources(data.sources);
                } else if (data.type === "done") {
                    onDone();
                } else if (data.type === "error") {
                    onError(data.content);
                }
            } catch (e) {
                continue;
            }
        }
    }
}