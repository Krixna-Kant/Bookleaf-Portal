import type { Metadata } from "next";
import { Caveat, Courier_Prime, Literata, Playfair_Display, Source_Sans_3 } from "next/font/google";
import "./globals.css";

const playfair = Playfair_Display({ subsets: ["latin"], variable: "--font-playfair" });
const sourceSans = Source_Sans_3({ subsets: ["latin"], variable: "--font-source" });
const caveat = Caveat({ subsets: ["latin"], variable: "--font-caveat" });
const courier = Courier_Prime({ weight: ["400", "700"], subsets: ["latin"], variable: "--font-courier" });
const literata = Literata({ subsets: ["latin"], variable: "--font-literata" });

export const metadata: Metadata = {
  title: "BookLeaf Author Support",
  description: "Author support and operations portal",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${playfair.variable} ${sourceSans.variable} ${caveat.variable} ${courier.variable} ${literata.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
