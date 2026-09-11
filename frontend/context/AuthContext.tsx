"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { UserProfile } from "@/types";
import { ragApi, setAuthToken, getAuthToken } from "@/services/ragApi";

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  loading: boolean;
  loginWithGoogle: (payload?: { email?: string; name?: string; token?: string }) => Promise<UserProfile>;
  loginAdmin: (credentials: { email: string; password: string }) => Promise<UserProfile>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  // Initialize and validate session from server on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = getAuthToken();
        const storedUser = localStorage.getItem("finee_auth_user");

        if (token) {
          try {
            const liveUser = await ragApi.getMe();
            setUser(liveUser);
            localStorage.setItem("finee_auth_user", JSON.stringify(liveUser));
          } catch {
            if (storedUser) {
              setUser(JSON.parse(storedUser));
            } else {
              setUser(null);
            }
          }
        } else if (storedUser) {
          setUser(JSON.parse(storedUser));
        } else {
          setUser(null);
        }
      } catch (err) {
        console.warn("[AuthContext] Failed to restore session:", err);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const loginWithGoogle = async (payload?: { email?: string; name?: string; token?: string }) => {
    setLoading(true);
    try {
      const email = payload?.email || "advisor@finee.ai";
      const name = payload?.name || "Financial Advisor";

      const res = await ragApi.googleLogin({
        email,
        name,
        token: payload?.token,
        firm: "Apex Global Wealth",
        department: "Private Wealth Advisory",
      });

      setUser(res.user);
      localStorage.setItem("finee_auth_user", JSON.stringify(res.user));
      return res.user;
    } catch (err: any) {
      console.error("[AuthContext] Google login failed:", err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const loginAdmin = async (credentials: { email: string; password: string }) => {
    setLoading(true);
    try {
      const res = await ragApi.adminLogin(credentials);
      setUser(res.user);
      localStorage.setItem("finee_auth_user", JSON.stringify(res.user));
      return res.user;
    } catch (err: any) {
      console.error("[AuthContext] Admin login failed:", err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await ragApi.logoutSession();
    } catch (err) {
      console.warn("[AuthContext] Error during logout:", err);
    } finally {
      setUser(null);
      setAuthToken(null);
      localStorage.removeItem("finee_auth_user");
      localStorage.removeItem("finee_auth_token");
      setLoading(false);
    }
  };

  const isAdmin = user?.role === "ADMIN" || user?.role?.toLowerCase().includes("admin") || false;

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isAdmin,
        loading,
        loginWithGoogle,
        loginAdmin,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
