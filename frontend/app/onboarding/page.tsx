"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";

// Step Components
import Step1Welcome from "@/components/onboarding/step1-welcome";
import Step2BasicTutorial from "@/components/onboarding/step2-transcribe";
import Step3ReviewEdit from "@/components/onboarding/step3-review-edit";
import Step4Ready from "@/components/onboarding/step4-ready";
import LicenseCheckFail from "@/components/onboarding/license-check-fail";

const TOTAL_STEPS = 4;
// Gating: required watch time in seconds (hardcoded, change as needed)
const STEP2_REQUIRED_SECONDS = 30;
const STEP3_REQUIRED_SECONDS = 30;

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [hasValidLicense, setHasValidLicense] = useState<boolean | null>(null);
  const [onboardingStatus, setOnboardingStatus] = useState<{
    force_onboarding_override?: boolean;
    environment?: string;
  } | null>(null);
  // Removed formData as step 2 is no longer used

  // Countdown gating state
  const [step2RemainingSeconds, setStep2RemainingSeconds] = useState<number>(0);
  const [step2GateActive, setStep2GateActive] = useState<boolean>(false);
  const [step2Completed, setStep2Completed] = useState<boolean>(false);
  const [step3RemainingSeconds, setStep3RemainingSeconds] = useState<number>(0);
  const [step3GateActive, setStep3GateActive] = useState<boolean>(false);
  const [step3Completed, setStep3Completed] = useState<boolean>(false);

  // Scroll to top when step changes
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [currentStep]);

  // Start/stop the Step 2/3 countdown when entering/leaving those steps
  useEffect(() => {
    let intervalId2: ReturnType<typeof setInterval> | null = null;
    let intervalId3: ReturnType<typeof setInterval> | null = null;
    if (currentStep === 2) {
      // Only start timer if user hasn't already completed it
      if (!step2Completed) {
        setStep2GateActive(true);
        setStep2RemainingSeconds(STEP2_REQUIRED_SECONDS);
        intervalId2 = setInterval(() => {
          setStep2RemainingSeconds((prev) => {
            const next = Math.max(0, prev - 1);
            if (next === 0) {
              setStep2GateActive(false);
              setStep2Completed(true);
              if (intervalId2) clearInterval(intervalId2);
            }
            return next;
          });
        }, 1000);
      } else {
        // Already completed, no gate needed
        setStep2GateActive(false);
        setStep2RemainingSeconds(0);
      }
    } else if (currentStep === 3) {
      // Only start timer if user hasn't already completed it
      if (!step3Completed) {
        setStep3GateActive(true);
        setStep3RemainingSeconds(STEP3_REQUIRED_SECONDS);
        intervalId3 = setInterval(() => {
          setStep3RemainingSeconds((prev) => {
            const next = Math.max(0, prev - 1);
            if (next === 0) {
              setStep3GateActive(false);
              setStep3Completed(true);
              if (intervalId3) clearInterval(intervalId3);
            }
            return next;
          });
        }, 1000);
      } else {
        // Already completed, no gate needed
        setStep3GateActive(false);
        setStep3RemainingSeconds(0);
      }
    } else {
      // Reset gate state when navigating off steps 2 and 3
      setStep2GateActive(false);
      setStep2RemainingSeconds(0);
      setStep3GateActive(false);
      setStep3RemainingSeconds(0);
    }
    return () => {
      if (intervalId2) clearInterval(intervalId2);
      if (intervalId3) clearInterval(intervalId3);
    };
  }, [currentStep, step2Completed, step3Completed]);

  // Update page title for accessibility (WCAG 2.4.2 Page Titled)
  useEffect(() => {
    if (hasValidLicense === false) {
      document.title = "Justice Transcribe coming soon – access pending";
      return;
    }

    const titlesByStep = {
      1: "Welcome – Justice Transcribe onboarding (step 1 of 4)",
      2: "Transcribe a meeting – Justice Transcribe onboarding (step 2 of 4)",
      3: "Review and edit – Justice Transcribe onboarding (step 3 of 4)",
      4: "You're ready – Justice Transcribe onboarding (step 4 of 4)",
    } as const;

    document.title =
      titlesByStep[currentStep as 1 | 2 | 3 | 4] || "Justice Transcribe";
  }, [currentStep, hasValidLicense]);

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
    // Gate step 2 until countdown completes
    if (currentStep === 2 && step2GateActive) {
      return false;
    }
    if (currentStep === 3 && step3GateActive) {
      return false;
    }
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
    <div className="bg-background">
      {/* Skip to main content for screen readers */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-blue-600 focus:px-4 focus:py-2 focus:text-white focus:shadow-lg"
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
        className={
          (currentStep === 2 || currentStep === 3) && hasValidLicense !== false
            ? "mx-auto w-full max-w-7xl px-4 pb-24 pt-6 md:pb-0"
            : "container mx-auto max-w-2xl px-3 pb-0 pt-4"
        }
      >
        {/* Main heading for accessibility */}
        <h1 className="sr-only">Complete your Justice Transcribe setup</h1>
        {/* Step content - centered vertically */}
        {((currentStep === 2 || currentStep === 3) &&
          hasValidLicense !== false) ||
        currentStep === 1 ||
        currentStep === 4 ? (
          <>{renderStep()}</>
        ) : (
          <div className="flex min-h-[calc(100svh-64px)] flex-col justify-center">
            {renderStep()}
          </div>
        )}

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
                    <div className="flex items-center gap-3">
                      {currentStep === 2 && step2GateActive && (
                        <span
                          className="text-sm text-muted-foreground"
                          aria-live="polite"
                        >
                          You can continue in{" "}
                          {`${Math.floor(step2RemainingSeconds / 60)}:${String(step2RemainingSeconds % 60).padStart(2, "0")}`}
                        </span>
                      )}
                      {currentStep === 3 && step3GateActive && (
                        <span
                          className="text-sm text-muted-foreground"
                          aria-live="polite"
                        >
                          You can continue in{" "}
                          {`${Math.floor(step3RemainingSeconds / 60)}:${String(step3RemainingSeconds % 60).padStart(2, "0")}`}
                        </span>
                      )}
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
