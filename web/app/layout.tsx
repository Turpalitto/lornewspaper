import type { Metadata } from "next";
import { Providers } from "./providers";
import { Header } from "@/components/layout/header";
import { Feedback } from "@/components/layout/feedback";
import "./globals.css";

export const metadata: Metadata = {
  title: "LORNEWS",
  description: "Academic research platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">
        <Providers>
          <div className="flex min-h-screen flex-col">
            <Header />
            <main className="flex-1">{children}</main>
            <Feedback />
          </div>
        </Providers>
      </body>
    </html>
  );
}
