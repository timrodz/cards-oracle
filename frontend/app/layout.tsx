import type { Metadata } from "next";
import { Inter as FontSans, Geist_Mono as FontMono } from "next/font/google";
import { OracleSidebar } from "@/components/oracle-sidebar";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import "./globals.css";
import { cn } from "@/lib/utils";

const fontSans = FontSans({
  variable: "--font-sans",
  subsets: ["latin"],
});

const fontMono = FontMono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Card Oracle - Magic: The Gathering",
  description:
    "An agentic application that helps you find Magic: The Gathering cards.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={cn([
          "antialiased",
          "overflow-hidden",
          fontSans.variable,
          fontMono.variable,
        ])}
      >
        <SidebarProvider>
          <OracleSidebar />
          <SidebarInset className="h-svh overflow-y-auto">
            <header className="p-4">
              <SidebarTrigger />
            </header>
            {children}
          </SidebarInset>
        </SidebarProvider>
      </body>
    </html>
  );
}
