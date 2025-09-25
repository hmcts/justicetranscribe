"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";

// Step Components
import Step1Welcome from "@/components/onboarding/step1-welcome";
import Step2Setup from "@/components/onboarding/step2-setup";
import Step4BasicTutorial from "@/components/onboarding/step3-basic-tutorial";
import Step5ReviewEdit from "@/components/onboarding/step4-review-edit";
import Step6Ready from "@/components/onboarding/step5-ready";
import LicenseCheckFail from "@/components/onboarding/license-check-fail";

const TOTAL_STEPS = 6;

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [hasValidLicense, setHasValidLicense] = useState<boolean | null>(null);
  const [onboardingStatus, setOnboardingStatus] = useState<{
    force_onboarding_override?: boolean;
    environment?: string;
  } | null>(null);
  const [formData, setFormData] = useState({
    crissaTime: "",
    appointmentsPerWeek: "",
    acceptedPrivacy: false,
  });

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
        console.error("Failed to fetch onboarding status:", error);
      }
    };

    fetchOnboardingStatus();
  }, []);

  // Validation for step 2
  const isStep2Valid = () => {
    return formData.crissaTime && formData.appointmentsPerWeek;
  };

  const canContinue = () => {
    if (currentStep === 2) {
      return isStep2Valid();
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

        // Authentication is valid - continue to step 2
        setCurrentStep(2);
      } catch (error) {
        console.error("Auth check failed:", error);
        // Authentication failed - show sorry message
        setHasValidLicense(false);
      }
    } else if (currentStep < TOTAL_STEPS && canContinue()) {
      // Skip step 3 (device setup) - go from step 2 to step 4
      if (currentStep === 2) {
        setCurrentStep(4);
      } else if (currentStep === 4) {
        setCurrentStep(5);
      } else if (currentStep === 5) {
        setCurrentStep(6);
      }
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      // Handle back navigation with skipped step 3
      if (currentStep === 4) {
        setCurrentStep(2);
      } else if (currentStep === 5) {
        setCurrentStep(4);
      } else if (currentStep === 6) {
        setCurrentStep(5);
      } else {
        setCurrentStep(currentStep - 1);
      }
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
        console.log("Onboarding marked as complete:", response.data.message);
      }
    } catch (error) {
      console.error("Failed to mark onboarding as complete:", error);
      // Continue to home page even if API call fails
    }
    router.push("/"); // Return to home to start recording
  };


  const handleCrissaTimeChange = (time: string) => {
    setFormData({ ...formData, crissaTime: time });
  };

  const handleAppointmentsChange = (appointments: string) => {
    setFormData({ ...formData, appointmentsPerWeek: appointments });
  };

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
        return (
          <Step2Setup
            crissaTime={formData.crissaTime}
            appointmentsPerWeek={formData.appointmentsPerWeek}
            onCrissaTimeChange={handleCrissaTimeChange}
            onAppointmentsChange={handleAppointmentsChange}
          />
        );
      case 4:
        return <Step4BasicTutorial />;
      case 5:
        return <Step5ReviewEdit />;
      case 6:
        return (
          <Step6Ready
            onGetStarted={handleStartRecording}
            onBack={handleBack}
          />
        );
      default:
        return <div>Invalid step</div>;
    }
  };

  return (
    <div className="min-h-screen bg-background">
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

      <div className="container mx-auto max-w-2xl px-3 pb-16 pt-2">
        {/* Main heading for accessibility */}
        <h1 className="sr-only">Complete your Justice Transcribe setup</h1>
        

        {/* Step content */}
        <div className="mb-3">
          {renderStep()}
        </div>

        {/* Navigation - Only show for steps 1-5, step 6 has its own buttons, hide for license check fail */}
        {currentStep < 6 && hasValidLicense !== false && (
          <div className="fixed inset-x-0 bottom-0 z-40 border-t bg-background">
            <div className="container mx-auto max-w-2xl px-4 py-3">
              {currentStep === 1 ? (
                // Step 1: Centered Continue button only
                <div className="flex w-full items-center justify-center">
                  <Button
                    onClick={handleNext}
                    disabled={!canContinue()}
                    className={`px-8 py-3 text-base ${!canContinue() ? "cursor-not-allowed opacity-50" : ""}`}
                  >
                    Continue
                  </Button>
                </div>
              ) : (
                // Steps 2, 4, 5: Back on left, Continue on right
                <div className="flex items-center justify-between">
                  <Button onClick={handleBack} variant="outline">
                    Back
                  </Button>
                  <Button
                    onClick={handleNext}
                    disabled={!canContinue()}
                    className={!canContinue() ? "cursor-not-allowed opacity-50" : ""}
                  >
                    Continue
                  </Button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
