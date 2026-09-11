"use client";

import React, { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { useAuth } from "@/context/AuthContext";
import { RefreshCw } from "lucide-react";

export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, isAdmin, loading } = useAuth();

  const isAuthPage = pathname === "/login" || pathname === "/signin" || pathname === "/signup";

  useEffect(() => {
    if (loading) return;

    // 1. Unauthenticated users cannot access protected pages
    if (!isAuthenticated && !isAuthPage && pathname !== "/") {
      router.replace("/login");
      return;
    }

    // 2. Normal users cannot access admin pages
    if (isAuthenticated && !isAdmin && pathname.startsWith("/admin")) {
      router.replace("/chatask");
      return;
    }
  }, [isAuthenticated, isAdmin, isAuthPage, pathname, loading, router]);

  if (isAuthPage) {
    return <main className="min-h-screen w-full bg-background">{children}</main>;
  }

  return (
    <div className="flex min-h-screen w-full bg-background">
      <Sidebar />
      <div className="flex-1 ml-64 min-w-0 flex flex-col min-h-screen">
        {children}
      </div>
    </div>
  );
};
