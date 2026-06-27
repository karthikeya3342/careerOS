import React, { useState } from "react";
import { Icons } from "./icons";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  supabase: any;
  triggerToast: (msg: string, type: "success" | "error" | "info" | "warning") => void;
  onAuthSuccess: (sessionUser: any) => void;
}

export const AuthModal = ({ isOpen, onClose, supabase, triggerToast, onAuthSuccess }: AuthModalProps) => {
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authTab, setAuthTab] = useState<"login" | "signup">("login");
  const [isSubmittingAuth, setIsSubmittingAuth] = useState(false);

  if (!isOpen) return null;

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!authEmail.trim() || !authPassword.trim()) return;

    setIsSubmittingAuth(true);
    try {
      if (authTab === "login") {
        const { data, error } = await supabase.auth.signInWithPassword({
          email: authEmail,
          password: authPassword,
        });
        if (error) {
          triggerToast(error.message, "error");
        } else {
          triggerToast("Logged in successfully!", "success");
          onAuthSuccess(data.user);
          setAuthPassword("");
          onClose();
        }
      } else {
        const { data, error } = await supabase.auth.signUp({
          email: authEmail,
          password: authPassword,
        });
        if (error) {
          triggerToast(error.message, "error");
        } else {
          triggerToast("Account created successfully! Check email if verification is required.", "success");
          onAuthSuccess(data.user);
          setAuthPassword("");
          onClose();
        }
      }
    } catch (err: any) {
      triggerToast("Authentication Exception: " + err.message, "error");
    } finally {
      setIsSubmittingAuth(false);
    }
  };

  return (
    <>
      <div 
        className="fixed inset-0 bg-navy/60 backdrop-blur-sm z-[90] animate-fade-in" 
        onClick={onClose} 
      />
      <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-antiwhite border-4 border-navy shadow-[8px_8px_0px_0px_rgba(43,45,66,1)] p-6 z-[95] animate-scale-in">
        <div className="flex justify-between items-center border-b-4 border-navy pb-3 mb-4">
          <h2 className="text-lg font-black uppercase text-navy">Authentication Required</h2>
          <button 
            onClick={onClose}
            className="bg-white hover:bg-frenchgray/20 border-2 border-navy p-1 text-navy cursor-pointer transition-all"
          >
            <Icons.Close />
          </button>
        </div>
        
        <p className="text-[10px] font-bold text-frenchgray uppercase mb-4 leading-normal">
          You must log in or create an account to access the Career Command Center, run resume tailoring loops, or check application pipelines.
        </p>

        {/* Modal Auth Tabs */}
        <div className="flex border-b-2 border-navy/20 mb-4">
          <button
            onClick={() => setAuthTab("login")}
            type="button"
            className={`pb-2 px-4 text-xs font-black uppercase tracking-wider cursor-pointer border-b-3 transition-all ${
              authTab === "login"
                ? "border-vibrantred text-navy"
                : "border-transparent text-frenchgray hover:text-navy"
            }`}
          >
            Log In
          </button>
          <button
            onClick={() => setAuthTab("signup")}
            type="button"
            className={`pb-2 px-4 text-xs font-black uppercase tracking-wider cursor-pointer border-b-3 transition-all ${
              authTab === "signup"
                ? "border-vibrantred text-navy"
                : "border-transparent text-frenchgray hover:text-navy"
            }`}
          >
            Create Account
          </button>
        </div>

        <form onSubmit={handleAuthSubmit} className="space-y-4 font-sans">
          <div>
            <label className="text-[9px] font-black uppercase text-frenchgray block mb-1">Email Address</label>
            <input
              type="email"
              placeholder="your@email.com"
              value={authEmail}
              onChange={e => setAuthEmail(e.target.value)}
              className="w-full bg-antiwhite text-navy border-3 border-navy px-3 py-2 font-semibold focus:outline-none text-xs focus:ring-2 focus:ring-vibrantred"
              required
            />
          </div>
          <div>
            <label className="text-[9px] font-black uppercase text-frenchgray block mb-1">Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={authPassword}
              onChange={e => setAuthPassword(e.target.value)}
              className="w-full bg-antiwhite text-navy border-3 border-navy px-3 py-2 font-semibold focus:outline-none text-xs focus:ring-2 focus:ring-vibrantred"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isSubmittingAuth}
            className="w-full bg-vibrantred hover:bg-engorange disabled:bg-frenchgray text-antiwhite text-xs font-black uppercase py-3 border-3 border-navy shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer inline-flex justify-center items-center gap-1.5"
          >
            {isSubmittingAuth ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Processing...
              </>
            ) : authTab === "login" ? (
              "Log In & Enter"
            ) : (
              "Register New Account"
            )}
          </button>
        </form>
      </div>
    </>
  );
};
