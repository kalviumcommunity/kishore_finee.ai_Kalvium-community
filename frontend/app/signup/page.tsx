"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Script from "next/script";
import {
  ShieldCheck,
  ArrowRight,
  Shield,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  ArrowLeft,
  UserCheck,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

declare global {
  interface Window {
    google?: any;
  }
}

export default function SignUpPage() {
  const router = useRouter();
  const { loginWithGoogle, isAuthenticated, isAdmin } = useAuth();

  const [loading, setLoading] = useState(false);
  const [googleError, setGoogleError] = useState<string | null>(null);

  const googleBtnContainerRef = useRef<HTMLDivElement>(null);
  const googleClientId =
    process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ||
    "116946628146-1lsdqfh2ircjnkbg3nt2i5fkh48km7gm.apps.googleusercontent.com";

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      if (isAdmin) {
        router.replace("/admin");
      } else {
        router.replace("/dashboard");
      }
    }
  }, [isAuthenticated, isAdmin, router]);

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
        router.push("/dashboard");
      }
    } catch (err: any) {
      console.error("Google Signup failed:", err);
      setGoogleError("Google signup could not be completed. Please try again.");
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
            text: "signup_with",
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
    loginWithGoogle()
      .then((user) => {
        if (user.role === "ADMIN") {
          router.push("/admin");
        } else {
          router.push("/dashboard");
        }
      })
      .catch(() => {
        setGoogleError("Google authentication could not be completed. Please try again.");
      })
      .finally(() => setLoading(false));
  };

  return (
    <>
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        onLoad={initGoogleGsi}
      />

      <div className="min-h-screen bg-[#06090e] flex flex-col justify-center items-center p-4 relative overflow-hidden select-none">
        {/* Top Return to Home Link */}
        <div className="absolute top-6 left-6 z-20">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-mono text-gray-400 hover:text-white transition-colors px-3 py-1.5 rounded-lg bg-surface/60 border border-surface-border hover:bg-surface"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Homepage</span>
          </Link>
        </div>

        {/* Ambient Glows */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-10 right-10 w-80 h-80 bg-teal-500/5 rounded-full blur-3xl pointer-events-none" />

        {/* Signup Card */}
        <div className="w-full max-w-md bg-surface border border-surface-border rounded-2xl p-8 shadow-2xl z-10 space-y-6 relative">
          {/* Brand Header */}
          <div className="text-center space-y-3">
            <Link href="/" className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 mb-1 shadow-inner hover:scale-105 transition-transform">
              <ShieldCheck className="w-8 h-8" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center justify-center gap-1 font-sans">
                Create Advisor Account
              </h1>
              <p className="text-xs text-gray-400 mt-1 font-sans max-w-xs mx-auto">
                Sign up with Google to instantly provision your compliance-grounded advisory intelligence workspace.
              </p>
            </div>
          </div>

          {/* Provisioning Perks */}
          <div className="p-4 rounded-xl bg-surface-raised border border-surface-border space-y-2 text-xs text-gray-300">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold">
              <UserCheck className="w-4 h-4" />
              <span>Instant Advisory Role Provisioning</span>
            </div>
            <ul className="space-y-1.5 pl-6 list-disc text-gray-400 text-[11px]">
              <li>Access to approved institutional compliance manuals</li>
              <li>Persistent consultation threads and query history</li>
              <li>0.720 similarity guardrail protection on every query</li>
            </ul>
          </div>

          {/* Error notification */}
          {googleError && (
            <div className="p-3 rounded-xl bg-red-950/50 border border-red-800 text-xs text-red-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{googleError}</span>
            </div>
          )}

          {/* Single Primary Action: Sign up with Google */}
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
              <span>{loading ? "Creating Account..." : "Sign up with Google"}</span>
            </button>
          </div>

          {/* Switch to Sign In */}
          <div className="text-center text-xs text-gray-400">
            <span>Already have an account? </span>
            <Link href="/login" className="text-emerald-400 hover:underline font-semibold">
              Sign In
            </Link>
          </div>

          {/* Compliance Badges */}
          <div className="pt-4 border-t border-surface-border text-center">
            <div className="flex items-center justify-center gap-4 text-[11px] font-mono text-gray-500">
              <span className="flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> SOC-2 Aligned
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Shield className="w-3.5 h-3.5 text-emerald-500" /> AES-256
              </span>
              <span>•</span>
              <span>FINRA Grounded</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
