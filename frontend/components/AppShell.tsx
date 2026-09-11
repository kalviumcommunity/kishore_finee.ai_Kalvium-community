"use client";

import React, { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { useAuth } from "@/context/AuthContext";

const PUBLIC_ROUTES = [
  "/",
  "/platform",
  "/how-it-works",
  "/trust",
  "/solutions",
  "/about",
  "/contact",
  "/login",
  "/signin",
  "/signup",
];

export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, isAdmin, loading } = useAuth();

  const isPublic = PUBLIC_ROUTES.includes(pathname);
  const isChatask = pathname === "/chatask";

  useEffect(() => {
    if (loading) return;

    // 1. Unauthenticated users trying to access protected pages
    if (!isAuthenticated && !isPublic) {
      router.replace("/login");
      return;
    }

    // 2. Normal users cannot access admin pages
    if (isAuthenticated && !isAdmin && pathname.startsWith("/admin")) {
      router.replace("/dashboard");
      return;
    }
  }, [isAuthenticated, isAdmin, isPublic, pathname, loading, router]);

  // 1. Public marketing and auth pages render full-width without sidebar
  if (isPublic) {
    return <main className="min-h-screen w-full bg-background">{children}</main>;
  }

  // 2. /chatask renders standalone full-width (it has its own embedded header and conversation sidebar)
  if (isChatask) {
    return <main className="h-screen w-full bg-background overflow-hidden">{children}</main>;
  }

  // 3. Workspace pages (/dashboard, /sources, /profile, /admin/*) render with navigation sidebar
  return (
    <div className="flex min-h-screen w-full bg-background">
      <Sidebar />
      <div className="flex-1 ml-64 min-w-0 flex flex-col min-h-screen">
        {children}
      </div>
    </div>
  );
};
