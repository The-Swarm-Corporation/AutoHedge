import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aurum Synod · 550-Agent Market Terminal",
  description:
    "Reactive 3D AI trading terminal tracking gold, forex, USA and India markets with a swarm of 550 autonomous agents.",
};

export const viewport: Viewport = {
  themeColor: "#05060a",
  colorScheme: "dark",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-void text-ink antialiased">{children}</body>
    </html>
  );
}
