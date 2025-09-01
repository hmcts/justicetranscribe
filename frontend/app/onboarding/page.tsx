"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

// Step Components
import Step1Welcome from "@/components/onboarding/step1-welcome";
import Step2Setup from "@/components/onboarding/step2-setup";
import Step3DeviceSetup from "@/components/onboarding/step3-device-setup";
import Step4BasicTutorial from "@/components/onboarding/step4-basic-tutorial";
import Step5EmailNotifications from "@/components/onboarding/step5-email-notifications";
import Step6ReviewEdit from "@/components/onboarding/step6-review-edit";
import Step7Ready from "@/components/onboarding/step7-ready";

// TODO: Update these placeholder routes once Help page PR is merged
const HELP_PAGE_ROUTE = "/help";  // Will be updated after Help page PR merge

const TOTAL_STEPS = 7;

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    email: "",
    minutesSpent: "",
    acceptedPrivacy: false,
  });

  // Validation for step 2
  const isStep2Valid = () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(formData.email) && 
           formData.minutesSpent && 
           parseInt(formData.minutesSpent) > 0;
  };

  const canContinue = () => {
    if (currentStep === 2) {
      return isStep2Valid();
    }
    return true;
  };

  const handleNext = () => {
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
    router.push("/");  // Return to home to start recording
  };

  const handleNeedHelp = () => {
    // TODO: Update this route once Help page PR is merged
    router.push(HELP_PAGE_ROUTE);
  };

  const handleEmailChange = (email: string) => {
    setFormData({ ...formData, email });
  };

  const handleMinutesChange = (minutes: string) => {
    setFormData({ ...formData, minutesSpent: minutes });
  };

  const renderStep = () => {
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
        return <Step5EmailNotifications email={formData.email} />;
      case 6:
        return <Step6ReviewEdit />;
      case 7:
        return (
          <Step7Ready 
            onStartRecording={handleStartRecording}
            onNeedHelp={handleNeedHelp}
          />
        );
      default:
        return <div>Invalid step</div>;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {/* Progress indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {Array.from({ length: TOTAL_STEPS }, (_, i) => i + 1).map((stepNum) => (
              <div
                key={stepNum}
                className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  stepNum === currentStep
                    ? "bg-black text-white"
                    : stepNum < currentStep
                    ? "bg-gray-200"
                    : "border"
                }`}
              >
                {stepNum}
              </div>
            ))}
          </div>
        </div>

        {/* Step content */}
        <div className="mb-8">
          {renderStep()}
        </div>

        {/* Navigation - Only show for steps 1-6, step 7 has its own buttons */}
        {currentStep < 7 && (
          <div className="flex justify-between pt-6">
            {currentStep > 1 && (
              <Button
                onClick={handleBack}
                variant="outline"
              >
                Back
              </Button>
            )}
            <Button
              onClick={handleNext}
              disabled={!canContinue()}
              className={`ml-auto ${!canContinue() ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              Continue
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
