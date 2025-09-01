import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface LicenseCheckFailProps {
  onSignUp: () => void;
}

export default function LicenseCheckFail({ onSignUp }: LicenseCheckFailProps) {
  const [email, setEmail] = useState("");
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSignUp = () => {
    if (email.trim()) {
      setIsSubmitted(true);
      // Call the original onSignUp prop if needed for any additional logic
      onSignUp();
    }
  };

  const isEmailValid = () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
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
            If you&apos;re wanting early access, enter your email below to sign
            up. We&apos;ll let you know when we&apos;re ready.
          </p>
        </div>
      </div>

      {!isSubmitted ? (
        <div className="space-y-4">
          <div className="mx-auto max-w-md">
            <Label
              htmlFor="early-access-email"
              className="mb-2 block text-left"
            >
              Email address
            </Label>
            <Input
              id="early-access-email"
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full"
            />
          </div>

          <div className="pt-4">
            <Button
              onClick={handleSignUp}
              disabled={!isEmailValid()}
              className={`px-8 py-6 text-lg font-semibold ${
                !isEmailValid() ? "cursor-not-allowed opacity-50" : ""
              }`}
            >
              Sign up for early access
            </Button>
          </div>
        </div>
      ) : (
        <div className="pt-4">
          <div className="rounded-lg border border-green-200 bg-green-50 p-6">
            <p className="text-lg font-semibold text-green-800">
              Submitted. We&apos;ll let you know when we&apos;re ready.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
