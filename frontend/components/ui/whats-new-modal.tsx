"use client";

import React, { useState, useEffect } from "react";
import { X } from "lucide-react";

interface WhatsNewModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function WhatsNewModal({ isOpen, onClose }: WhatsNewModalProps) {
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Trigger animation on mount
      const timer = setTimeout(() => setIsAnimating(true), 10);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 z-40 transition-opacity duration-300 ${
          isAnimating ? "bg-black/30" : "bg-black/0"
        }`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className={`relative w-full max-w-md transform rounded-2xl bg-white shadow-2xl transition-all duration-300 ${
            isAnimating
              ? "scale-100 opacity-100"
              : "scale-95 opacity-0"
          }`}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Close Button */}
          <button
            type="button"
            onClick={onClose}
            className="absolute right-4 top-4 rounded-full p-1.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 focus:outline-none"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>

          {/* Content */}
          <div className="px-8 py-8">
            {/* Header */}
            <div className="mb-6">
              <h2 className="text-2xl font-semibold tracking-tight text-gray-900">
                What's New
              </h2>
            </div>

            {/* Message */}
            <div className="space-y-4">
              <p className="text-base leading-relaxed text-gray-600">
                Record up to 2 hours per meeting. New reliability improvements
                and bug fixes.
              </p>
            </div>

            {/* Footer Button */}
            <div className="mt-8 flex gap-3">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-center text-sm font-semibold text-white transition-colors hover:bg-blue-700 active:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Got It
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

/**
 * Hook to manage one-time display of the What's New modal
 * Uses localStorage to persist the state across sessions
 */
export function useWhatsNewModal() {
  const STORAGE_KEY = "whats_new_modal_dismissed";

  const [showModal, setShowModal] = useState(false);

  // Check if modal has been dismissed on mount
  useEffect(() => {
    const isDismissed = localStorage.getItem(STORAGE_KEY) === "true";
    if (!isDismissed) {
      setShowModal(true);
    }
  }, []);

  const handleDismiss = () => {
    setShowModal(false);
    localStorage.setItem(STORAGE_KEY, "true");
  };

  return {
    showModal,
    handleDismiss,
    resetModal: () => {
      localStorage.removeItem(STORAGE_KEY);
      setShowModal(true);
    },
  };
}
