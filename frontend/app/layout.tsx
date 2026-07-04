import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agent Chat",
  description: "AI agent chat — frontend",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
