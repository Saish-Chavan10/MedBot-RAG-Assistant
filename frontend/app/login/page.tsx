"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import Link from "next/link";
import { apiLogin, saveAuth } from "../lib/api";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    
    const handleLogin = async () => {
        setError("");
        if (!email || !password) {
            setError("Please fill in all the fields");
            return;
        }
        setLoading(true);
        try {
            const result = await apiLogin(email, password);
            if (!result.success) {
                setError(result.error || "Invalid email or password");
                return;
            }
            saveAuth(result.token, result.user);
            router.push("/");
        } catch (e) {
            setError("Something went wrong. Please try again");
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter") handleLogin();
    };

    return (
        <div className="min-h-screen bg-[#0a0f1e] flex items-center justify-center px-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="w-14 h-14 rounded-2xl bg-blue-600 flex items-center justify-center text-white font-bold text-xl mx-auto mb-4">
                        M
                    </div>
                    <h1 className="text-2xl font-bold text-white">Welcome Back</h1>
                    <p className="text-slate-400 text-sm mt-1">Sign in to Medbot</p>
                </div>

                <div className="bg-[#0D1B2E] border border-[#1e3a5f] rounded-2xl p-8 space-y-5">
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm px-4 py-3 rounded-xl">
                            {error}
                        </div>
                    )}
                    
                    <div>
                        <label className="text-slate-300 text-sm font-medium block mb-2">Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="doctor@hospital.com"
                            className="w-full bg-[#0a0f1e] border border-[#1e3a5f] focus:border-blue-500 text-slate-200 placeholder-slate-500 rounded-xl px-4 py-3 text-sm outline-none transition-colors"
                        />
                    </div>

                    <div>
                        <label className="text-slate-300 text-sm font-medium block mb-2">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Enter your password"
                            className="w-full bg-[#0a0f1e] border border-[#1e3a5f] focus:border-blue-500 text-slate-200 placeholder-slate-500 rounded-xl px-4 py-3 text-sm outline-none transition-colors"
                        />
                    </div>

                    <button 
                        onClick={handleLogin} 
                        disabled={loading}
                        className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 rounded-xl transition-colors disabled:opacity-50 mt-2"
                    >
                        {loading ? "Signing in..." : "Sign in"}
                    </button>
                    
                    <div className="text-center mt-6">
                        <p className="text-slate-400 text-sm">
                            Don't have an account? <Link href="/register" className="text-blue-400 hover:text-blue-300 font-medium">Create one</Link>
                        </p>
                    </div>
                </div>
                
                <p className="text-center text-slate-600 text-xs mt-6">
                    Medbot powered by Gale Encyclopedia of Medicine
                </p>
            </div> 
        </div>
    );
}