import React, { useState } from "react";
import { Button } from "@/components/ui/button";

export default function LicenseCheckFail() {
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSignUp = () => {
    setIsSubmitted(true);
  };

  return (
    <div className="mx-auto max-w-2xl space-y-8 text-center">
      <div className="space-y-6">
        <h2 className="text-3xl font-bold text-gray-900">
          Sorry, Justice Transcribe will be coming soon! 🚀
        </h2>

        <div className="space-y-4">
          <p className="text-lg leading-relaxed text-gray-700">
            To support our rollout, we&apos;re doing a phased allocation of
            licenses.
          </p>

          <p className="text-lg leading-relaxed text-gray-700">
            If you&apos;re wanting early access, click below to join our waiting
            list.
          </p>
        </div>
      </div>

      <div className="pt-4">
        <Button
          onClick={handleSignUp}
          disabled={isSubmitted}
          className={`px-8 py-6 text-lg font-semibold transition-all ${
            isSubmitted
              ? "cursor-default bg-green-600 text-white"
              : "bg-blue-600 text-white hover:bg-blue-700"
          }`}
        >
          {isSubmitted ? "You've signed up" : "Join the waiting list"}
        </Button>
      </div>
    </div>
  );
}
