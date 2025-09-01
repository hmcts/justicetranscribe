import React from "react";
import { Button } from "@/components/ui/button";
import { ExternalLink } from "lucide-react";

interface LicenseCheckFailProps {
  onSignUp: () => void;
}

export default function LicenseCheckFail({ onSignUp }: LicenseCheckFailProps) {
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
            If you&apos;re wanting early access, click below to sign up. We&apos;ll let you know when we&apos;re ready.
          </p>
        </div>
      </div>

      <div className="pt-4">
        <Button
          onClick={onSignUp}
          className="inline-flex items-center gap-2 px-8 py-6 text-lg font-semibold"
        >
          Sign up for early access
          <ExternalLink className="h-5 w-5" />
        </Button>
      </div>

      <div className="pt-8 border-t border-gray-200">
        <p className="text-sm text-gray-500">
          Thank you for your interest in Justice Transcribe. We appreciate your patience as we expand access to all users.
        </p>
      </div>
    </div>
  );
}
