import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "FINEE.ai — Compliance-Grounded Knowledge Control",
  description: "Enterprise Knowledge Control System for Financial Advisory & Compliance",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-gray-100 min-h-screen flex antialiased selection:bg-emerald-500/30 selection:text-emerald-200">
        <Sidebar />
        <div className="flex-1 ml-64 min-w-0 flex flex-col min-h-screen">
          {children}
        </div>
      </body>
    </html>
  );
}
