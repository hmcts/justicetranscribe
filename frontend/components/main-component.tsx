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
  const [isLoading, setIsLoading] = useState(true);

  // Check if we're directly accessing a transcript via URL
  const transcriptId = currentParams?.get("id");

  useEffect(() => {
    const checkOnboardingStatus = async () => {
      try {
        const response = await apiClient.request<OnboardingStatus>(
          "/user/onboarding-status",
        );

        if (response.data) {
          // Only redirect to onboarding if we're not already there and should show onboarding
          const isOnOnboardingPage =
            window.location.pathname.includes("/onboarding");

          if (
            response.data.should_show_onboarding &&
            !isOnOnboardingPage &&
            !transcriptId
          ) {
            router.push("/onboarding");
          }
        }
      } catch (error) {
        console.error("Failed to check onboarding status:", error);
        // Continue without onboarding check on error
      } finally {
        setIsLoading(false);
      }
    };

    checkOnboardingStatus();
  }, [router, transcriptId]);

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
