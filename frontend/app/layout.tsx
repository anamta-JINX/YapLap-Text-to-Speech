import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "YapLab — Make It Yap",
  description: "Turn any text into expressive speech with voices, accents and emotional tones.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">{children}</body>
    </html>
  );
}
