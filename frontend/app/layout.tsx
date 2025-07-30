import React from "react";

import "./globals.css";

import type { Metadata } from "next";
import { Inter } from "next/font/google";

import Header from "@/components/layout/header";

import { TranscriptsProvider } from "@/providers/transcripts";
import { UserSettingsProvider } from "@/providers/user-settings";
import PosthogProvider from "../providers/posthog";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Justice Transcribe",
  description: "Justice Transcribe",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <UserSettingsProvider>
          <PosthogProvider>
            <TranscriptsProvider>
              {/* <BeforeUnloadGuard /> */}
              <div className="flex min-h-screen flex-col">
                <Header className="fixed top-0 z-50 w-full" />
                <div className="mt-[50px] flex flex-1">
                  <main className="w-full pb-[50px]">{children}</main>
                </div>
              </div>
            </TranscriptsProvider>
          </PosthogProvider>
        </UserSettingsProvider>
      </body>
    </html>
  );
}
