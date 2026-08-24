import type { Metadata } from "next";
import "./globals.css";
import { ThreeBackground } from "@/components/canvas/ThreeBackground";

export const metadata: Metadata = {
  title: "AI Job Hunter (Jhunter) — Autonomous Recruitment Intelligence Suite",
  description:
    "Executive autonomous AI job hunting platform with multi-source ingestion, dual weighted matching radar, anti-fabrication materials generator, Gmail OAuth2, and Telegram Bot orchestration.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Outfit:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-[#080B11] text-gray-100 antialiased min-h-screen relative selection:bg-cyan-500/30 selection:text-cyan-200">
        {/* Three.js Interactive 3D Background */}
        <ThreeBackground />
        <div className="relative z-10 flex flex-col min-h-screen">
          {children}
        </div>
      </body>
    </html>
  );
}
