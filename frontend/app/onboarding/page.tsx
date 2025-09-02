"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

// Step Components
import Step1Welcome from "@/components/onboarding/step1-welcome";
import Step2Setup from "@/components/onboarding/step2-setup";
import Step3DeviceSetup from "@/components/onboarding/step3-device-setup";
import Step4BasicTutorial from "@/components/onboarding/step4-basic-tutorial";

import Step6ReviewEdit from "@/components/onboarding/step6-review-edit";
import Step7Ready from "@/components/onboarding/step7-ready";
import LicenseCheckFail from "@/components/onboarding/license-check-fail";

// TODO: Update these placeholder routes once Help page PR is merged
const HELP_PAGE_ROUTE = "/help"; // Will be updated after Help page PR merge

const TOTAL_STEPS = 6;

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [hasValidLicense, setHasValidLicense] = useState<boolean | null>(null);
  const [formData, setFormData] = useState({
    email: "",
    minutesSpent: "",
    acceptedPrivacy: false,
  });

  // Validation for step 2
  const isStep2Valid = () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return (
      emailRegex.test(formData.email) &&
      formData.minutesSpent &&
      parseInt(formData.minutesSpent, 10) > 0
    );
  };

  const canContinue = () => {
    if (currentStep === 2) {
      return isStep2Valid();
    }
    return true;
  };

  // Check if user has valid license
  const checkLicense = (email: string) => {
    // Simulate license check - if email is 'fake@fake.com', deny access
    return email.toLowerCase() !== "fake@fake.com";
  };

  const handleNext = () => {
    if (currentStep === 2 && canContinue()) {
      // Check license after step 2 (Get Started)
      const licenseValid = checkLicense(formData.email);
      setHasValidLicense(licenseValid);

      if (!licenseValid) {
        // Don't proceed to step 3, stay on license check fail page
        return;
      }
    }

    if (currentStep < TOTAL_STEPS && canContinue()) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStartRecording = () => {
    router.push("/"); // Return to home to start recording
  };

  const handleNeedHelp = () => {
    // TODO: Update this route once Help page PR is merged
    router.push(HELP_PAGE_ROUTE);
  };

  const handleSignUpForEarlyAccess = () => {
    // TODO: Replace with actual early access signup URL
    window.open("https://example.com/early-access-signup", "_blank");
  };

  const handleBackFromLicenseCheck = () => {
    setHasValidLicense(null);
    // Stay on step 2 to allow user to try different email
  };

  const getStepClassName = (stepNum: number) => {
    if (stepNum === currentStep) {
      return "bg-black text-white";
    }
    if (stepNum < currentStep) {
      return "bg-gray-200";
    }
    return "border";
  };

  const handleEmailChange = (email: string) => {
    setFormData({ ...formData, email });
  };

  const handleMinutesChange = (minutes: string) => {
    setFormData({ ...formData, minutesSpent: minutes });
  };

  const renderStep = () => {
    // Show license check fail page if license check failed
    if (hasValidLicense === false) {
      return <LicenseCheckFail onSignUp={handleSignUpForEarlyAccess} />;
    }

    switch (currentStep) {
      case 1:
        return <Step1Welcome />;
      case 2:
        return (
          <Step2Setup
            email={formData.email}
            minutesSpent={formData.minutesSpent}
            onEmailChange={handleEmailChange}
            onMinutesChange={handleMinutesChange}
          />
        );
      case 3:
        return <Step3DeviceSetup />;
      case 4:
        return <Step4BasicTutorial />;
      case 5:
        return <Step6ReviewEdit />;
      case 6:
        return (
          <Step7Ready
            onStartRecording={handleStartRecording}
            onNeedHelp={handleNeedHelp}
            onBack={handleBack}
          />
        );
      default:
        return <div>Invalid step</div>;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto max-w-[90rem] px-4 py-8">
        {/* Progress indicator - Hide when showing license check fail */}
        {hasValidLicense !== false && (
          <div className="mb-8">
            <div className="flex items-center justify-between">
              {Array.from({ length: TOTAL_STEPS }, (_, i) => i + 1).map(
                (stepNum) => (
                  <div
                    key={stepNum}
                    className={`flex size-8 items-center justify-center rounded-full ${getStepClassName(
                      stepNum,
                    )}`}
                  >
                    {stepNum}
                  </div>
                ),
              )}
            </div>
          </div>
        )}

        {/* Step content */}
        <div className="mb-8">{renderStep()}</div>

        {/* Navigation - Only show for steps 1-5, step 6 has its own buttons, hide for license check fail */}
        {currentStep < 6 && hasValidLicense !== false && (
          <div className="flex justify-between pt-6">
            {currentStep > 1 && (
              <Button onClick={handleBack} variant="outline">
                Back
              </Button>
            )}
            {currentStep === 1 ? (
              <Button
                onClick={handleNext}
                disabled={!canContinue()}
                className={`mx-auto px-12 py-6 text-lg ${!canContinue() ? "cursor-not-allowed opacity-50" : ""}`}
              >
                Continue
              </Button>
            ) : (
              <Button
                onClick={handleNext}
                disabled={!canContinue()}
                className={`ml-auto ${!canContinue() ? "cursor-not-allowed opacity-50" : ""}`}
              >
                Continue
              </Button>
            )}
          </div>
        )}

        {/* Back button for license check fail page */}
        {hasValidLicense === false && (
          <div className="flex justify-center pt-6">
            <Button onClick={handleBackFromLicenseCheck} variant="outline">
              Try Different Email
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
