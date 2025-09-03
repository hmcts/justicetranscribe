/* eslint-disable react/button-has-type */

"use client";

/* eslint-disable react/require-default-props */
/* eslint-disable react/react-in-jsx-scope */
import Link from "next/link";
import Image from "next/image";
import { useRouter, usePathname } from "next/navigation";
import { useTranscripts } from "@/providers/transcripts";
import { Home, HelpCircle } from "lucide-react";
import { useCallback } from "react";
import { cn } from "@/lib/utils";

export default function Header({ className }: { className?: string }) {
  const { newTranscription, selectedRecordingMode } = useTranscripts();
  const router = useRouter();
  const pathname = usePathname();

  const handleHomeClick = useCallback(() => {
    if (pathname === "/help") {
      // Navigate to root page when on help page
      router.push("/");
    } else {
      // Use default new transcription behavior for other pages
      newTranscription();
    }
  }, [pathname, router, newTranscription]);

  return (
    <header className={cn("z-50 bg-white dark:border-gray-800", className)}>
      <div className="mx-auto max-w-full">
        <div className="flex h-14 items-center justify-between px-4">
          <div className={cn("flex items-center", "pl-0 ")}>
            <Link
              href="/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-black"
            >
              <span
                className="font-medium text-black"
                style={{ fontSize: "1.4rem" }}
              >
                Transcriber
              </span>
            </Link>
          </div>
          <div className="flex items-center gap-4">
            {!selectedRecordingMode && (
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleHomeClick}
                  className="flex h-8 items-center justify-center rounded-full px-3 hover:bg-gray-100"
                  aria-label="Go to home"
                  title="Go to home"
                >
                  <Home className="mr-1 size-4" />
                  <span className="text-sm">Home</span>
                </button>
                <Link
                  href="/help"
                  className="flex h-8 items-center justify-center rounded-full px-3 hover:bg-gray-100"
                  aria-label="Go to help"
                  title="Go to help"
                >
                  <HelpCircle className="mr-1 size-4" />
                  <span className="text-sm">Help</span>
                </Link>
              </div>
            )}
            <Link
              href="https://ai.justice.gov.uk/"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Image
                src="/justice-ai-logo-bnw.png"
                width={160}
                height={100}
                alt="Justice AI"
                className="h-20 w-auto object-contain"
                priority
              />
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
