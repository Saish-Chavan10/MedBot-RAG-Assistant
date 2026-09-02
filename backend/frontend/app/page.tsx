"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
    isLoggedIn,
    getUser,
    logout,
    fetchSessions,
    createSession,
    deleteSession,
    fetchMessages,
    streamMessage,
    Session,
    ChatMessage
} from "./lib/api";
import Message from "./components/message";
import TypingIndicator from "./components/typing-indicator";

export default function Home() {
    const router = useRouter();
    const [user, setUser] = useState<any>(null);
    const [sessions, setSessions] = useState<Session[]>([]);
    const [activeSession, setActiveSession] = useState<Session | null>(null);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [queryText, setQueryText] = useState("");
    const [loading, setLoading] = useState(false);
    const [healthy, setHealthy] = useState<boolean | null>(null);
    
    const bottomRef = useRef<HTMLDivElement>(null);
    const queryTextRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        if (!isLoggedIn()) {
            router.push("/login");
            return;
        }
        setUser(getUser());
        setHealthy(true);
        loadSessions();
    }, []);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    const loadSessions = async () => {
        const data = await fetchSessions();
        setSessions(data);
    };

    const handleNewChat = async () => {
        const session = await createSession("New Chat");
        setSessions((prev) => [session, ...prev]);
        setActiveSession(session);
        setMessages([]);
        queryTextRef.current?.focus();
    };

    const handleSelectSession = async (session: Session) => {
        setActiveSession(session);
        const msgs = await fetchMessages(session.id);
        setMessages(msgs);
    };

    const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
        e.stopPropagation();
        await deleteSession(sessionId);
        setSessions((prev) => prev.filter((s) => s.id !== sessionId));
        if (activeSession?.id === sessionId) {
            setActiveSession(null);
            setMessages([]);
        }
    };

    const handleLogout = () => {
        logout();
        router.push("/login");
    };

    const handleSend = async (q: string) => {
        if (!q.trim()) return;
        
        let currentSession = activeSession;
        if (!currentSession) {
            currentSession = await createSession("New Chat");
            setSessions((prev) => [currentSession!, ...prev]);
            setActiveSession(currentSession);
        }

        const newMsg: ChatMessage = { 
            id: Date.now().toString(), 
            role: "user", 
            content: q, 
            sources: [] 
        };
        
        setMessages((prev) => [...prev, newMsg]);
        setQueryText("");
        setLoading(true);

        const botMsgId = (Date.now() + 1).toString();
        let currentBotContent = "";
        let currentSources: any[] = [];

        setMessages((prev) => [...prev, { id: botMsgId, role: "bot", content: "", sources: [] }]);

        await streamMessage(
            q,
            currentSession.id,
            (token) => {
                currentBotContent += token;
                setMessages((prev) => prev.map(m => m.id === botMsgId ? { ...m, content: currentBotContent } : m));
            },
            (sources) => {
                currentSources = sources;
                setMessages((prev) => prev.map(m => m.id === botMsgId ? { ...m, sources: currentSources } : m));
            },
            () => {
                setLoading(false);
                loadSessions();
            },
            (err) => {
                console.error(err);
                setLoading(false);
            }
        );
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend(queryText);
        }
    };

    const handlequeryText = (e: React.FormEvent<HTMLTextAreaElement>) => {
    const target = e.currentTarget;
    target.style.height = "auto";
    target.style.height = `${target.scrollHeight}px`;
    };

    const suggestedQuestions = [
        "What are the symptoms of malaria?",
        "What is the difference between type 1 and type 2 diabetes?",
        "What causes kidney failure?"
    ];

    const showWelcome = messages.length === 0;

    return (
        <div className="flex h-screen bg-[#0a0f1e] overflow-hidden">
            <aside className="w-64 bg-[#0D1B2E] border-r border-[#1e3a5f] flex flex-col shrink-0">
                <div className="p-4 border-b border-[#1e3a5f] flex items-center gap-2 mb-4">
                    <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-xs">M</div>
                    <span className="text-white font-semibold text-sm">Medbot</span>
                </div>
                
                <div className="px-4">
                    <button onClick={handleNewChat} className="w-full bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium py-2 px-3 rounded-xl transition-all flex items-center gap-2">
                        <span className="text-lg leading-none">+</span> New Chat
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-2 space-y-1 mt-4">
                    {sessions.length === 0 ? (
                        <p className="text-slate-500 text-xs text-center mt-4">No chats yet</p>
                    ) : (
                        sessions.map((s) => (
                            <div key={s.id} onClick={() => handleSelectSession(s)} className="cursor-pointer text-slate-300 text-sm p-2 hover:bg-[#1e3a5f] rounded flex justify-between group">
                                <span className="truncate">{s.title}</span>
                                <button onClick={(e) => handleDeleteSession(e, s.id)} className="hidden group-hover:block text-red-400">X</button>
                            </div>
                        ))
                    )}
                </div>

                <div className="p-4 border-t border-[#1e3a5f]">
                    <div className="flex items-center justify-between">
                        <div className="overflow-hidden">
                            <p className="text-white text-xs font-medium truncate">{user?.full_name}</p>
                            <p className="text-slate-400 text-xs truncate">{user?.email}</p>
                        </div>
                        <button onClick={handleLogout} className="text-xs text-red-400 hover:text-red-300 shrink-0 ml-2">Logout</button>
                    </div>
                </div>
            </aside>

            <main className="flex-1 flex flex-col overflow-hidden">
                <header className="flex items-center justify-between px-6 py-4 border-b border-[#1e3a5f] bg-[#0D1B2E] shrink-0">
                    <h1 className="text-white font-semibold text-base leading-none">
                        {activeSession ? activeSession.title : "Medbot"}
                    </h1>
                    <div className="flex items-center gap-3">
                        <div className="flex items-center gap-1.5">
                            <div className={`w-2 h-2 rounded-full ${healthy === null ? 'bg-yellow-400' : healthy ? 'bg-emerald-400' : 'bg-red-400'}`} />
                            <span className="text-xs text-slate-300">
                                {healthy === null ? "Connecting..." : healthy ? "Online" : "Offline"}
                            </span>
                        </div>
                    </div>
                </header>

                <div className="flex-1 overflow-y-auto px-4 py-6">
                    {showWelcome ? (
                        <div className="max-w-3xl mx-auto space-y-6 flex flex-col items-center justify-center min-h-[60vh] gap-8">
                            <div className="text-center">
                                <div className="w-14 h-14 rounded-2xl bg-blue-600 flex items-center justify-center text-white font-bold text-xl mx-auto mb-4">M</div>
                                <h2 className="text-2xl font-semibold text-white mb-2">Hello, {user?.full_name?.split(" ")[0]}</h2>
                                <p className="text-slate-300 text-sm max-w-md">AI powered medical assistant trained on the Gale Encyclopedia of Medicine 3rd Edition</p>
                            </div>
                            
                            <div className="w-full max-w-md">
                                <p className="text-xs text-slate-400 text-center mb-3">Suggested questions you can ask</p>
                                <div className="flex flex-col gap-2">
                                    {suggestedQuestions.map((q, i) => (
                                        <button key={i} onClick={() => handleSend(q)} className="text-left px-4 py-3 rounded-xl bg-[#111827] border border-[#1e3a5f] hover:border-blue-500 hover:bg-[#0D1B2E] text-slate-300 hover:text-white text-sm transition-all">
                                            {q}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="max-w-3xl mx-auto space-y-6">
                            {messages.map((msg, i) => {
                                const isLast = i === messages.length - 1;
                                const isEmptyBot = isLast && msg.role === 'bot' && msg.content === "" && loading;
                                
                                if (isEmptyBot) {
                                    return <TypingIndicator key={msg.id} />;
                                }

                                return (
                                    <Message 
                                        key={msg.id}
                                        role={msg.role}
                                        content={msg.content}
                                        sources={msg.sources}
                                        duration_ms={msg.duration_ms}
                                    />
                                );
                            })}
                            <div ref={bottomRef} />
                        </div>
                    )}
                </div>

                <div className="px-4 py-4 border-t border-[#1e3a5f] bg-[#0D1B2E] shrink-0">
                    <div className="max-w-3xl mx-auto flex items-end gap-3 bg-[#0a0f1e] p-2 rounded-xl border border-[#1e3a5f]">
                        <textarea
                            ref={queryTextRef}
                            value={queryText}
                            onChange={(e) => setQueryText(e.target.value)}
                            onKeyDown={handleKeyDown}
                            onInput={handlequeryText}
                            placeholder="Ask a medical question... Press Enter to send"
                            rows={1}
                            className="flex-1 bg-transparent text-slate-200 placeholder-slate-500 text-sm resize-none outline-none max-h-32 leading-relaxed px-2 py-1"
                        />
                        <button onClick={() => handleSend(queryText)} className="bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm px-4 py-2 rounded-lg transition-colors shrink-0">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                            </svg>
                        </button>
                    </div>
                    <p className="text-center text-xs text-slate-400 mt-2">Medbot can make mistakes. Always verify with clinical judgment.</p>
                </div>
            </main>
        </div>
    );
}