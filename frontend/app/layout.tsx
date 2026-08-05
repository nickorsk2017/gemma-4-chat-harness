import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Gemma 4 chat",
  description: "",
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
