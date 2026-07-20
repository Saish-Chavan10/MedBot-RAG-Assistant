export default function TypingIndicator() {
    return (
        <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0 bg-[#0D1B2E] border border-[#1e3a5f]">
                M
            </div>
            <div className="p-4 rounded-xl max-w-[80%] bg-[#111827] border border-[#1e3a5f] flex gap-1 items-center h-[42px]">
                <div className="w-1.5 h-1.5 bg-slate-400 rounded-full typing" style={{ animationDelay: '0ms' }} />
                <div className="w-1.5 h-1.5 bg-slate-400 rounded-full typing" style={{ animationDelay: '200ms' }} />
                <div className="w-1.5 h-1.5 bg-slate-400 rounded-full typing" style={{ animationDelay: '400ms' }} />
            </div>
        </div>
    );
}