"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Script from "next/script";
import {
  ShieldCheck,
  Lock,
  Mail,
  ArrowRight,
  Shield,
  CheckCircle2,
  X,
  AlertCircle,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

declare global {
  interface Window {
    google?: any;
  }
}

export default function LoginPage() {
  const router = useRouter();
  const { loginWithGoogle, loginAdmin, isAuthenticated, isAdmin } = useAuth();

  const [loading, setLoading] = useState(false);
  const [googleError, setGoogleError] = useState<string | null>(null);

  // Hidden Admin Modal State
  const [showAdminModal, setShowAdminModal] = useState(false);
  const [adminEmail, setAdminEmail] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  const [adminLoading, setAdminLoading] = useState(false);
  const [adminError, setAdminError] = useState<string | null>(null);

  const googleBtnContainerRef = useRef<HTMLDivElement>(null);
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "116946628146-1lsdqfh2ircjnkbg3nt2i5fkh48km7gm.apps.googleusercontent.com";

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      if (isAdmin) {
        router.replace("/admin");
      } else {
        router.replace("/chatask");
      }
    }
  }, [isAuthenticated, isAdmin, router]);

  // Hidden Keyboard Shortcut Listener (Ctrl+Shift+A or Cmd+Shift+A)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === "A" || e.key === "a")) {
        e.preventDefault();
        setShowAdminModal((prev) => !prev);
        setAdminError(null);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Handle Google OAuth Credential Response
  const handleGoogleCredentialResponse = async (response: any) => {
    setLoading(true);
    setGoogleError(null);
    try {
      const loggedUser = await loginWithGoogle({
        token: response.credential,
        email: "",
      });

      if (loggedUser.role === "ADMIN") {
        router.push("/admin");
      } else {
        router.push("/chatask");
      }
    } catch (err: any) {
      console.error("Google Auth failed:", err);
      setGoogleError("Google authentication could not be completed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Initialize Google Identity Services
  const initGoogleGsi = () => {
    if (typeof window !== "undefined" && window.google?.accounts?.id) {
      try {
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: handleGoogleCredentialResponse,
          auto_select: false,
          cancel_on_tap_outside: true,
        });

        if (googleBtnContainerRef.current) {
          window.google.accounts.id.renderButton(googleBtnContainerRef.current, {
            theme: "filled_black",
            size: "large",
            text: "continue_with",
            shape: "pill",
            width: "320",
          });
        }
      } catch (err) {
        console.warn("Could not render Google Sign-In button:", err);
      }
    }
  };

  const handleManualGoogleClick = () => {
    setLoading(true);
    setGoogleError(null);
    if (typeof window !== "undefined" && window.google?.accounts?.id) {
      try {
        window.google.accounts.id.prompt((notification: any) => {
          if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
            // Fallback to direct auth request if prompt suppressed
            loginWithGoogle()
              .then((user) => {
                if (user.role === "ADMIN") {
                  router.push("/admin");
                } else {
                  router.push("/chatask");
                }
              })
              .catch(() => {
                setGoogleError("Google authentication could not be completed. Please try again.");
              })
              .finally(() => setLoading(false));
          }
        });
      } catch {
        loginWithGoogle()
          .then((user) => {
            if (user.role === "ADMIN") {
              router.push("/admin");
            } else {
              router.push("/chatask");
            }
          })
          .catch(() => {
            setGoogleError("Google authentication could not be completed. Please try again.");
          })
          .finally(() => setLoading(false));
      }
    } else {
      loginWithGoogle()
        .then((user) => {
          if (user.role === "ADMIN") {
            router.push("/admin");
          } else {
            router.push("/chatask");
          }
        })
        .catch(() => {
          setGoogleError("Google authentication could not be completed. Please try again.");
        })
        .finally(() => setLoading(false));
    }
  };

  // Hidden Admin Login Handler
  const handleAdminSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adminEmail.trim() || !adminPassword.trim()) {
      setAdminError("Invalid administrator credentials.");
      return;
    }

    setAdminLoading(true);
    setAdminError(null);

    try {
      await loginAdmin({
        email: adminEmail.trim(),
        password: adminPassword,
      });
      setShowAdminModal(false);
      router.push("/admin");
    } catch (err: any) {
      setAdminError("Invalid administrator credentials.");
    } finally {
      setAdminLoading(false);
    }
  };

  return (
    <>
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        onLoad={initGoogleGsi}
      />

      <div className="min-h-screen bg-background flex flex-col justify-center items-center p-4 relative overflow-hidden select-none">
        {/* Background Glow Accents */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-10 right-10 w-80 h-80 bg-teal-500/5 rounded-full blur-3xl pointer-events-none" />

        {/* Main Normal Login Card */}
        <div className="w-full max-w-md bg-surface border border-surface-border rounded-2xl p-8 shadow-2xl z-10 space-y-7 relative">
          {/* Brand Header */}
          <div className="text-center space-y-3">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 mb-1 shadow-inner">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center justify-center gap-1 font-sans">
                FINEE<span className="text-emerald-400">.ai</span>
              </h1>
              <p className="text-sm font-medium text-emerald-300/90 mt-1">
                Secure Financial Knowledge & Advisory Intelligence
              </p>
              <p className="text-xs text-gray-400 mt-2 font-sans max-w-xs mx-auto">
                Sign in securely to access your advisory workspace.
              </p>
            </div>
          </div>

          {/* Error notification if Google fails */}
          {googleError && (
            <div className="p-3 rounded-xl bg-red-950/50 border border-red-800 text-xs text-red-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{googleError}</span>
            </div>
          )}

          {/* Single Primary Action: Continue with Google */}
          <div className="space-y-4 flex flex-col items-center">
            {/* Google GSI Render Target */}
            <div ref={googleBtnContainerRef} className="w-full flex justify-center" />

            {/* Custom Google Styled Button (fallback / primary) */}
            <button
              type="button"
              onClick={handleManualGoogleClick}
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl bg-surface-raised hover:bg-surface-hover border border-surface-border hover:border-surface-borderLight text-white text-sm font-semibold flex items-center justify-center gap-3 transition-all shadow-lg hover:shadow-emerald-500/5 active:scale-[0.99] group cursor-pointer"
            >
              <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <span>{loading ? "Connecting with Google..." : "Continue with Google"}</span>
            </button>
          </div>

          {/* Enterprise Compliance Badges */}
          <div className="pt-4 border-t border-surface-border text-center space-y-3">
            <div className="flex items-center justify-center gap-4 text-[11px] font-mono text-gray-500">
              <span className="flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> SOC-2 Type II
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Shield className="w-3.5 h-3.5 text-emerald-500" /> 256-bit AES
              </span>
              <span>•</span>
              <span>FINRA Grounded</span>
            </div>
          </div>
        </div>

        {/* Hidden Administrator Authentication Modal (Triggered by Ctrl+Shift+A or Cmd+Shift+A) */}
        {showAdminModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div
              className="absolute inset-0 bg-black/80 backdrop-blur-md transition-opacity"
              onClick={() => setShowAdminModal(false)}
            />

            <div className="w-full max-w-md bg-surface border border-emerald-500/40 rounded-2xl p-7 shadow-2xl z-10 space-y-5 relative animate-in fade-in zoom-in-95 duration-200">
              {/* Modal Header */}
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                      <ShieldCheck className="w-4 h-4" />
                    </div>
                    <h2 className="text-base font-bold text-white tracking-tight font-sans">
                      FINEE<span className="text-emerald-400">.ai</span>
                    </h2>
                  </div>
                  <p className="text-xs font-semibold text-emerald-400 font-mono">
                    Administrator Access
                  </p>
                </div>

                <button
                  onClick={() => setShowAdminModal(false)}
                  className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-surface-raised transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Error Message */}
              {adminError && (
                <div className="p-2.5 rounded-xl bg-red-950/60 border border-red-800 text-xs text-red-300 font-mono flex items-center gap-2">
                  <AlertCircle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                  <span>{adminError}</span>
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleAdminSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-gray-300">Admin Email</label>
                  <div className="relative">
                    <Mail className="w-4 h-4 absolute left-3 top-2.5 text-gray-500" />
                    <input
                      type="email"
                      required
                      value={adminEmail}
                      onChange={(e) => setAdminEmail(e.target.value)}
                      placeholder="admin@finee.ai"
                      className="w-full bg-surface-raised border border-surface-border rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 font-sans transition-colors"
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-gray-300">Password</label>
                  <div className="relative">
                    <Lock className="w-4 h-4 absolute left-3 top-2.5 text-gray-500" />
                    <input
                      type="password"
                      required
                      value={adminPassword}
                      onChange={(e) => setAdminPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="w-full bg-surface-raised border border-surface-border rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 font-sans transition-colors"
                    />
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="pt-2 flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setShowAdminModal(false)}
                    className="w-1/3 py-2.5 px-4 rounded-xl bg-surface-raised hover:bg-surface-hover border border-surface-border text-gray-300 text-xs font-semibold transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={adminLoading}
                    className="flex-1 py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-surface-raised text-white text-xs font-semibold flex items-center justify-center gap-2 transition-all shadow-md cursor-pointer"
                  >
                    <span>{adminLoading ? "Authenticating..." : "[ Authenticate ]"}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
