"use client";

import React, { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface AnnouncementModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function AnnouncementModal({ isOpen, onClose }: AnnouncementModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Focus management - move focus to modal when it opens
  useEffect(() => {
    if (isOpen && closeButtonRef.current) {
      closeButtonRef.current.focus();
    }
  }, [isOpen]);

  // ESC key handler
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape" && isOpen) {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  // Focus trap
  useEffect(() => {
    if (!isOpen || !modalRef.current) return;

    const modal = modalRef.current;
    const focusableElements = modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    };

    modal.addEventListener("keydown", handleTab as EventListener);
    return () => modal.removeEventListener("keydown", handleTab as EventListener);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="announcement-title"
        aria-describedby="announcement-description"
        className="relative w-full max-w-md rounded-lg bg-white dark:bg-gray-800 p-6 shadow-lg sm:mx-4"
      >
        {/* Close button */}
        <button
          ref={closeButtonRef}
          onClick={onClose}
          className="absolute right-4 top-4 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
          aria-label="Close announcement"
        >
          <X className="size-5" />
        </button>

        {/* Content */}
        <div className="pr-8">
          <h2 id="announcement-title" className="mb-4 text-2xl font-bold text-gray-900 dark:text-gray-100">
            Week 1 updates
          </h2>

          <div id="announcement-description" className="space-y-4 text-gray-700 dark:text-gray-300">
            <div className="flex items-start space-x-3">
              <span className="text-xl" aria-hidden="true">🐛</span>
              <div>
                <p className="font-semibold">We squashed bugs for a smoother experience</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  If you see an error, try Retry upload.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <span className="text-xl" aria-hidden="true">⏱️</span>
              <div>
                <p className="font-semibold">You can now record up to 115 minutes</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  We&apos;ll auto-upload and transcribe when you&apos;re done.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <span className="text-xl" aria-hidden="true">🙏</span>
              <div>
                <p className="font-semibold">Thanks for 350+ reviews and an average 4.7/5 rating</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Tell us what you love and what needs work.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Button */}
        <div className="mt-6 flex justify-end gap-3">
          <Button 
            onClick={onClose} 
            className="min-h-[44px] bg-blue-600 text-white hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-400"
          >
            Got it!
          </Button>
        </div>
      </div>
    </div>
  );
}

export default AnnouncementModal;
