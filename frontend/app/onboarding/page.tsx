"use client";

import React, { useState, useEffect } from "react";
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

const HELP_PAGE_ROUTE = "/help";

const TOTAL_STEPS = 6;

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [hasValidLicense, setHasValidLicense] = useState<boolean | null>(null);
  const [formData, setFormData] = useState({
    email: "",
    crissaTime: "",
    appointmentsPerWeek: "",
    acceptedPrivacy: false,
  });

  // Scroll to top when step changes
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [currentStep]);

  // Validation for step 2
  const isStep2Valid = () => {
    return (
      formData.crissaTime &&
      formData.appointmentsPerWeek
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
    if (currentStep < TOTAL_STEPS && canContinue()) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleNoAuth = () => {
    setHasValidLicense(false);
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

  const handleCrissaTimeChange = (time: string) => {
    setFormData({ ...formData, crissaTime: time });
  };

  const handleAppointmentsChange = (appointments: string) => {
    setFormData({ ...formData, appointmentsPerWeek: appointments });
  };

  const renderStep = () => {
    // Show license check fail page if license check failed
    if (hasValidLicense === false) {
      return <LicenseCheckFail onSignUp={handleSignUpForEarlyAccess} />;
    }

    switch (currentStep) {
      case 1:
        return <Step1Welcome onNoAuth={handleNoAuth} />;
      case 2:
        return (
          <Step2Setup
            email={formData.email}
            crissaTime={formData.crissaTime}
            appointmentsPerWeek={formData.appointmentsPerWeek}
            onEmailChange={handleEmailChange}
            onCrissaTimeChange={handleCrissaTimeChange}
            onAppointmentsChange={handleAppointmentsChange}
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
      <div className="container mx-auto max-w-2xl px-4 pt-6 pb-12 sm:pt-8 md:pt-10 lg:pt-12 xl:pt-14">
        {/* Progress indicator - Hide when showing license check fail */}
        {hasValidLicense !== false && (
          <div className="mb-3 sm:mb-4 md:mb-5 lg:mb-6 xl:mb-8">
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
        <div className="mb-3 sm:mb-4 md:mb-5 lg:mb-6 xl:mb-8">
          {renderStep()}
        </div>

        {/* Navigation - Only show for steps 1-5, step 6 has its own buttons, hide for license check fail */}
        {currentStep < 6 && hasValidLicense !== false && (
          <div className="flex justify-between pt-4 sm:pt-5 md:pt-6 lg:pt-8 xl:pt-10">
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


      </div>
    </div>
  );
}
