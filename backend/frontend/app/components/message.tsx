import { useState } from "react";
import ReactMarkdown from "react-markdown";

interface MessageProps {
    role: "user" | "bot";
    content: string;
    sources?: any[];
    duration_ms?: number;
}

export default function Message({ role, content, sources, duration_ms }: MessageProps) {
    const [copied, setCopied] = useState(false);
    const isUser = role === "user";

    const handleCopy = () => {
        navigator.clipboard.writeText(content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className={`flex items-start gap-3 group animate-in fade-in ${isUser ? "flex-row-reverse" : ""}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0 ${isUser ? "bg-blue-600" : "bg-[#0D1B2E] border border-[#1e3a5f]"}`}>
                {isUser ? "Dr" : "M"}
            </div>
            <div className={`p-4 rounded-xl max-w-[80%] relative ${isUser ? "bg-blue-600 text-white" : "bg-[#111827] border border-[#1e3a5f] text-slate-200"}`}>
                
                {!isUser && content && (
                    <button 
                        onClick={handleCopy} 
                        className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity bg-[#1e3a5f] hover:bg-blue-600 text-slate-300 hover:text-white px-2 py-1 rounded-lg text-xs"
                    >
                        {copied ? "Copied!" : "Copy"}
                    </button>
                )}

                <div className="prose prose-invert max-w-none text-sm">
                    <ReactMarkdown>{content}</ReactMarkdown>
                </div>

                {sources && sources.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-[#1e3a5f] flex flex-col gap-1 w-full">
                        <p className="text-xs text-slate-400 mb-1 flex justify-between items-center">
                            <span>Sources from Gale Encyclopedia:</span>
                            {duration_ms && <span className="text-[10px] text-slate-500">{duration_ms / 1000}s</span>}
                        </p>
                        <div className="flex flex-wrap gap-2">
                            {sources.map((source, idx) => (
                                <div key={idx} className="bg-[#0D1B2E] border border-[#1e3a5f] px-3 py-2 rounded max-w-xs">
                                    <span className="text-blue-400 font-medium text-xs">Page {source.page}</span>
                                    <p className="text-slate-300 text-xs mt-0.5 truncate">{source.preview}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}