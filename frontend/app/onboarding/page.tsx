"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";

// Step Components
import Step1Welcome from "@/components/onboarding/step1-welcome";
import Step2BasicTutorial from "@/components/onboarding/step2-basic-tutorial";
import Step3ReviewEdit from "@/components/onboarding/step3-review-edit";
import Step4Ready from "@/components/onboarding/step4-ready";
import LicenseCheckFail from "@/components/onboarding/license-check-fail";

const TOTAL_STEPS = 4;

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [hasValidLicense, setHasValidLicense] = useState<boolean | null>(null);
  const [onboardingStatus, setOnboardingStatus] = useState<{
    force_onboarding_override?: boolean;
    environment?: string;
  } | null>(null);
  // Removed formData as step 2 is no longer used

  // Scroll to top when step changes
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [currentStep]);

  // Fetch onboarding status on page load to show warning banner
  useEffect(() => {
    const fetchOnboardingStatus = async () => {
      try {
        const response = await apiClient.request("/user/onboarding-status");
        if (response.data) {
          setOnboardingStatus(response.data);
        }
      } catch (error) {
        // Failed to fetch onboarding status, continue silently
      }
    };

    fetchOnboardingStatus();
  }, []);

  const canContinue = () => {
    // No validation needed as step 2 is removed
    return true;
  };

  const handleNext = async () => {
    // If we're on step 1 (Welcome), check authentication before proceeding
    if (currentStep === 1) {
      try {
        // Try to get current user - this will check Easy Auth
        const response = await apiClient.request("/user/onboarding-status");

        if (response.error || !response.data) {
          // No valid authentication - show sorry message
          setHasValidLicense(false);
          return;
        }

        // Store onboarding status for warning banner
        setOnboardingStatus(response.data);

        // Authentication is valid - go to step 2 (Basic Tutorial)
        setCurrentStep(2);
      } catch (error) {
        // Auth check failed - show sorry message
        setHasValidLicense(false);
      }
    } else if (currentStep < TOTAL_STEPS && canContinue()) {
      // Go to next step: 2->3, 3->4
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      // Simple back navigation: 4->3, 3->2, 2->1
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStartRecording = async () => {
    try {
      // Mark onboarding as complete
      const response = await apiClient.request<{
        success: boolean;
        message: string;
        has_completed_onboarding: boolean;
      }>("/user/complete-onboarding", {
        method: "POST",
      });

      if (response.data?.success) {
        // Onboarding marked as complete successfully
      }
    } catch (error) {
      // Failed to mark onboarding as complete, continue to home page anyway
    }
    router.push("/"); // Return to home to start recording
  };

  // Removed form handlers as step 2 is no longer used

  const handleLicenseRetry = () => {
    // Reset license check state to allow retry
    setHasValidLicense(null);
  };

  const renderStep = () => {
    // Show license check fail page if license check failed
    if (hasValidLicense === false) {
      return <LicenseCheckFail onRetry={handleLicenseRetry} />;
    }

    switch (currentStep) {
      case 1:
        return <Step1Welcome />;
      case 2:
        return <Step2BasicTutorial />;
      case 3:
        return <Step3ReviewEdit />;
      case 4:
        return <Step4Ready />;
      default:
        return <div>Invalid step</div>;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Skip to main content for screen readers */}
      <a
        href="#main-content"
        className="focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-blue-600 focus:px-4 focus:py-2 focus:text-white focus:shadow-lg sr-only"
      >
        Skip to main content
      </a>
      
      {/* Show warning banner if dev override is active */}
      {onboardingStatus?.force_onboarding_override && (
        <div className="fixed left-1/2 top-4 z-50 -translate-x-1/2 rounded-lg border border-orange-400 bg-orange-100 px-4 py-3 text-orange-800 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="font-medium">
              ⚠️ Warning: Onboarding flow override is active (dev mode)
            </span>
            <span className="ml-4 text-sm" style={{ color: "#2E1005BF" }}>
              Environment: {onboardingStatus.environment}
            </span>
          </div>
        </div>
      )}

      <div
        id="main-content"
        className="container mx-auto max-w-2xl px-3 pb-16 pt-4"
      >
        {/* Main heading for accessibility */}
        <h1 className="sr-only">Complete your Justice Transcribe setup</h1>
        
        {/* Step content - centered vertically */}
        <div className="flex min-h-[calc(100vh-200px)] flex-col justify-center">
          {renderStep()}
        </div>

        {/* Navigation - Show for all steps, hide for license check fail */}
        {hasValidLicense !== false && (
          <nav
            className="fixed inset-x-0 bottom-0 z-40 border-t bg-background"
            aria-label="Onboarding navigation"
          >
            <div className="container mx-auto max-w-2xl px-4 py-3">
              {(() => {
                if (currentStep === 1) {
                  // Step 1: Centered Continue button only
                  return (
                    <div className="flex w-full items-center justify-center">
                      <Button
                        onClick={handleNext}
                        disabled={!canContinue()}
                        className={`px-8 py-3 text-base ${!canContinue() ? "cursor-not-allowed opacity-50" : ""}`}
                      >
                        Continue
                      </Button>
                    </div>
                  );
                }
                if (currentStep === 4) {
                  // Step 4: Back on left, green Get Started on right
                  return (
                    <div className="flex items-center justify-between">
                      <Button onClick={handleBack} variant="outline">
                        Back
                      </Button>
                      <Button
                        onClick={handleStartRecording}
                        className="px-8 py-3 text-base text-white hover:opacity-90"
                        style={{ backgroundColor: "#10652F" }}
                      >
                        Get started
                      </Button>
                    </div>
                  );
                }
                // Steps 2, 3: Back on left, Continue on right
                return (
                  <div className="flex items-center justify-between">
                    <Button onClick={handleBack} variant="outline">
                      Back
                    </Button>
                    <Button
                      onClick={handleNext}
                      disabled={!canContinue()}
                      className={
                        !canContinue() ? "cursor-not-allowed opacity-50" : ""
                      }
                    >
                      Continue
                    </Button>
                  </div>
                );
              })()}
            </div>
          </nav>
        )}
      </div>
    </div>
  );
}
