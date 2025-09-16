"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import WelcomePage from "@/components/welcome-page";
import DialogueManager from "@/components/dialogue-manager";
import { useBrowserNavigation } from "@/hooks/use-browser-navigation";
import { apiClient } from "@/lib/api-client";

interface OnboardingStatus {
  has_completed_onboarding: boolean;
  force_onboarding_override: boolean;
  should_show_onboarding: boolean;
  user_id: string;
  environment: string;
}

function MainParentComponent() {
  const { currentParams } = useBrowserNavigation();
  const router = useRouter();
  const [onboardingStatus, setOnboardingStatus] = useState<OnboardingStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check if we're directly accessing a transcript via URL
  const transcriptId = currentParams?.get("id");

  useEffect(() => {
    checkOnboardingStatus();
  }, []);

  const checkOnboardingStatus = async () => {
    try {
      const response = await apiClient.request<OnboardingStatus>("/user/onboarding-status");
      
      if (response.data) {
        setOnboardingStatus(response.data);
        
        // Only redirect to onboarding if we're not already there and should show onboarding
        const isOnOnboardingPage = window.location.pathname.includes("/onboarding");
        
        if (response.data.should_show_onboarding && !isOnOnboardingPage && !transcriptId) {
          router.push("/onboarding");
          return;
        }
      }
    } catch (error) {
      console.error("Failed to check onboarding status:", error);
      // Continue without onboarding check on error
    } finally {
      setIsLoading(false);
    }
  };

  // Show loading while checking onboarding status
  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="text-lg text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="flex">
      {/* Show warning modal if dev override is active */}
      {onboardingStatus?.force_onboarding_override && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 bg-orange-100 border border-orange-400 text-orange-800 px-4 py-3 rounded-lg shadow-lg z-50">
          <div className="flex items-center justify-between">
            <span className="font-medium">
              ⚠️ Warning: Onboarding flow override is active (dev mode)
            </span>
            <span className="ml-4 text-sm opacity-75">
              Environment: {onboardingStatus.environment}
            </span>
          </div>
        </div>
      )}
      
      <div className="mx-auto flex w-full items-center justify-center">
        {!transcriptId && (
          <div className="w-full">
            <WelcomePage />
          </div>
        )}
        {transcriptId && (
          <div className="w-full">
            <DialogueManager />
          </div>
        )}
      </div>
    </div>
  );
}

export default MainParentComponent;
