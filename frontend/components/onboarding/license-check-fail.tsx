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
    <div className="space-y-8 max-w-2xl mx-auto text-center">
      <div className="space-y-6">
        <h2 className="text-3xl font-bold text-gray-900">
          Sorry, Justice Transcribe will be coming soon! 🚀
        </h2>
        
        <div className="space-y-4">
          <p className="text-lg leading-relaxed text-gray-700">
            To support our rollout, we&apos;re doing a phased allocation of licenses.
          </p>
          
          <p className="text-lg leading-relaxed text-gray-700">
            If you&apos;re wanting early access, enter your email below to sign up. We&apos;ll let you know when we&apos;re ready.
          </p>
        </div>
      </div>

      {!isSubmitted ? (
        <div className="space-y-4">
          <div className="max-w-md mx-auto">
            <Label htmlFor="early-access-email" className="text-left block mb-2">
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
                !isEmailValid() ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              Sign up for early access
            </Button>
          </div>
        </div>
      ) : (
        <div className="pt-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <p className="text-lg font-semibold text-green-800">
              Submitted. We&apos;ll let you know when we&apos;re ready.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
