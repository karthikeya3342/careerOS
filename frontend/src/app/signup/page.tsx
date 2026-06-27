"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/utils/supabase/client";

export default function SignupPage() {
  const router = useRouter();
  const supabase = createClient();
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    // If already logged in, redirect to home
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        router.push("/");
      }
    });
  }, [router, supabase]);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) return;

    setIsSubmitting(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
      });
      if (error) {
        setErrorMsg(error.message);
      } else {
        setSuccessMsg("Account created successfully! Check your inbox for verification if needed, or proceed to log in.");
        setEmail("");
        setPassword("");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "An unexpected error occurred.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-antiwhite text-navy font-sans flex items-center justify-center p-4 antialiased selection:bg-vibrantred selection:text-antiwhite retro-dot-grid">
      <div className="w-full max-w-md bg-white border-4 border-navy shadow-[8px_8px_0px_0px_rgba(43,45,66,1)] p-6 sm:p-8 animate-scale-in relative">
        <div className="absolute -top-3.5 -left-3.5 bg-vibrantred text-antiwhite text-[8px] font-black uppercase px-2 py-0.5 border-2 border-navy tracking-widest">
          SECURE CHANNEL
        </div>

        <div className="flex justify-between items-center border-b-4 border-navy pb-4 mb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black uppercase text-navy tracking-tight leading-none">SIGN UP</h1>
            <p className="text-[9px] font-black uppercase text-frenchgray tracking-wider mt-1.5">Register New Workspace profile</p>
          </div>
          <span className="w-3 h-3 bg-vibrantred rounded-full" />
        </div>

        {errorMsg && (
          <div className="bg-vibrantred/15 border-3 border-vibrantred p-3 text-xs font-bold text-navy uppercase mb-6 shadow-[2px_2px_0px_0px_rgba(239,35,60,0.15)] leading-relaxed">
            ⚠ Warning: {errorMsg}
          </div>
        )}

        {successMsg && (
          <div className="bg-green-50 border-3 border-green-600 p-3 text-xs font-bold text-navy uppercase mb-6 shadow-[2px_2px_0px_0px_rgba(22,163,74,0.15)] leading-relaxed">
            ✓ Success: {successMsg}
          </div>
        )}

        <form onSubmit={handleSignup} className="space-y-4">
          <div>
            <label className="text-[9px] font-black uppercase text-frenchgray tracking-wider block mb-1.5">Email Address</label>
            <input
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full bg-antiwhite text-navy border-3 border-navy px-3.5 py-2.5 font-bold focus:outline-none text-xs sm:text-sm focus:ring-2 focus:ring-vibrantred focus:shadow-[2px_2px_0px_0px_rgba(239,35,60,1)] transition-all placeholder:text-frenchgray/60"
              required
            />
          </div>

          <div>
            <label className="text-[9px] font-black uppercase text-frenchgray tracking-wider block mb-1.5">Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full bg-antiwhite text-navy border-3 border-navy px-3.5 py-2.5 font-bold focus:outline-none text-xs sm:text-sm focus:ring-2 focus:ring-vibrantred focus:shadow-[2px_2px_0px_0px_rgba(239,35,60,1)] transition-all placeholder:text-frenchgray/60"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-vibrantred hover:bg-engorange disabled:bg-frenchgray text-antiwhite text-xs font-black uppercase py-3.5 border-3 border-navy shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer flex justify-center items-center gap-2"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Creating Profile...
              </>
            ) : (
              "Create Account & Proceed"
            )}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t-2 border-navy/10 text-center font-sans">
          <p className="text-[10px] font-bold text-frenchgray uppercase">
            Already have an account?{" "}
            <a href="/login" className="text-vibrantred hover:underline font-black">
              Sign In
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
