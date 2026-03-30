import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Apothecary — Your Full Stack, Understood",
  description:
    "Understand how your medications and supplements work together. Check interactions, optimize timing, identify gaps.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
