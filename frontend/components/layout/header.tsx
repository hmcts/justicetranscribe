/* eslint-disable react/button-has-type */

"use client";

/* eslint-disable react/require-default-props */
/* eslint-disable react/react-in-jsx-scope */
import Link from "next/link";
import { useTranscripts } from "@/providers/transcripts";
import { Home, ChevronLeft, ChevronRight } from "lucide-react";
import { useCallback } from "react";
import { cn } from "@/lib/utils";

export default function Header({ className }: { className?: string }) {
  const { newTranscription, selectedRecordingMode } = useTranscripts();

  // Use browser's built-in history navigation
  const goBack = useCallback(() => {
    window.history.back();
  }, []);

  const goForward = useCallback(() => {
    window.history.forward();
  }, []);

  return (
    <>
      <header
        className={cn(
          "z-50 border-b border-gray-200 bg-black dark:border-gray-800",
          className,
        )}
      >
        <div className="mx-auto max-w-full">
          <div className="flex h-14 items-center justify-between px-4">
            <div className={cn("flex items-center", "pl-0 ")}>
              <Link
                href="/"
                target="_blank"
                rel="noopener noreferrer"
                className="font-gds-transport flex items-center gap-2 text-3xl text-white"
              >
                <svg
                  width="160"
                  height="52"
                  viewBox="0 0 148 48"
                  fill="white"
                  xmlns="http://www.w3.org/2000/svg"
                  className="ml-0 mt-3"
                >
                  <path d="M22.6 10.4c-1 .4-2-.1-2.4-1-.4-.9.1-2 1-2.4.9-.4 2 .1 2.4 1s-.1 2-1 2.4m-5.9 6.7c-.9.4-2-.1-2.4-1-.4-.9.1-2 1-2.4.9-.4 2 .1 2.4 1s-.1 2-1 2.4m10.8-3.7c-1 .4-2-.1-2.4-1-.4-.9.1-2 1-2.4.9-.4 2 .1 2.4 1s0 2-1 2.4m3.3 4.8c-1 .4-2-.1-2.4-1-.4-.9.1-2 1-2.4.9-.4 2 .1 2.4 1s-.1 2-1 2.4M17 4.7l2.3 1.2V2.5l-2.3.7-.2-.2.9-3h-3.4l.9 3-.2.2c-.1.1-2.3-.7-2.3-.7v3.4L15 4.7c.1.1.1.2.2.2l-1.3 4c-.1.2-.1.4-.1.6 0 1.1.8 2 1.9 2.2h.7c1-.2 1.9-1.1 1.9-2.1 0-.2 0-.4-.1-.6l-1.3-4c-.1-.2 0-.2.1-.3m-7.6 5.7c.9.4 2-.1 2.4-1 .4-.9-.1-2-1-2.4-.9-.4-2 .1-2.4 1s0 2 1 2.4m-5 3c.9.4 2-.1 2.4-1 .4-.9-.1-2-1-2.4-.9-.4-2 .1-2.4 1s.1 2 1 2.4m-3.2 4.8c.9.4 2-.1 2.4-1 .4-.9-.1-2-1-2.4-.9-.4-2 .1-2.4 1s0 2 1 2.4m14.8 11c4.4 0 8.6.3 12.3.8 1.1-4.5 2.4-7 3.7-8.8l-2.5-.9c.2 1.3.3 1.9 0 2.7-.4-.4-.8-1.1-1.1-2.3l-1.2 4c.7-.5 1.3-.8 2-.9-1.1 2.5-2.6 3.1-3.5 3-1.1-.2-1.7-1.2-1.5-2.1.3-1.2 1.5-1.5 2.1-.1 1.1-2.3-.8-3-2-2.3 1.9-1.9 2.1-3.5.6-5.6-2.1 1.6-2.1 3.2-1.2 5.5-1.2-1.4-3.2-.6-2.5 1.6.9-1.4 2.1-.5 1.9.8-.2 1.1-1.7 2.1-3.5 1.9-2.7-.2-2.9-2.1-2.9-3.6.7-.1 1.9.5 2.9 1.9l.4-4.3c-1.1 1.1-2.1 1.4-3.2 1.4.4-1.2 2.1-3 2.1-3h-5.4s1.7 1.9 2.1 3c-1.1 0-2.1-.2-3.2-1.4l.4 4.3c1-1.4 2.2-2 2.9-1.9-.1 1.5-.2 3.4-2.9 3.6-1.9.2-3.4-.8-3.5-1.9-.2-1.3 1-2.2 1.9-.8.7-2.3-1.2-3-2.5-1.6.9-2.2.9-3.9-1.2-5.5-1.5 2-1.3 3.7.6 5.6-1.2-.7-3.1 0-2 2.3.6-1.4 1.8-1.1 2.1.1.2.9-.3 1.9-1.5 2.1-.9.2-2.4-.5-3.5-3 .6 0 1.2.3 2 .9l-1.2-4c-.3 1.1-.7 1.9-1.1 2.3-.3-.8-.2-1.4 0-2.7l-2.9.9C1.3 23 2.6 25.5 3.7 30c3.7-.5 7.9-.8 12.3-.8" />
                </svg>
                <span className="font-gds-transport -ml-[7.5rem] text-3xl text-white">
                  Transcriber
                </span>
              </Link>
            </div>
            <div>
              <Link
                href="https://ai.gov.uk"
                target="_blank"
                rel="noopener noreferrer"
              >
                <img
                  src="/justice-ai-logo.jpeg"
                  width="65"
                  height="40"
                  alt="i.AI"
                  className="h-10 w-auto object-contain"
                />
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation buttons below header */}
      <div className="sticky top-14 z-40 flex h-10 w-full items-center justify-between border-b border-gray-200 bg-white px-4 shadow-sm">
        {!selectedRecordingMode && (
          <div className="flex items-center space-x-2">
            <button
              onClick={goBack}
              className="flex size-8 items-center justify-center rounded-full hover:bg-gray-100"
              aria-label="Go back"
              title="Go back"
            >
              <ChevronLeft className="size-5" />
            </button>
            <button
              onClick={goForward}
              className="flex size-8 items-center justify-center rounded-full hover:bg-gray-100"
              aria-label="Go forward"
              title="Go forward"
            >
              <ChevronRight className="size-5" />
            </button>
            <button
              onClick={() => newTranscription()}
              className="flex h-8 items-center justify-center rounded-full px-3 hover:bg-gray-100"
              aria-label="Go to home"
              title="Go to home"
            >
              <Home className="mr-1 size-4" />
              <span className="text-sm">Home</span>
            </button>
          </div>
        )}
      </div>
    </>
  );
}
