import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CLAI - AI Dev Team",
  description: "Multi-agent AI orchestration for software development",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full antialiased font-sans bg-clai-bg text-clai-text">
        {children}
      </body>
    </html>
  );
}
