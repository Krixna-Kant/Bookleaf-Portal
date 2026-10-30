import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BookLeaf Author Support",
  description: "Author support and operations portal",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
