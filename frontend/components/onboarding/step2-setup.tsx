import React from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface Step2SetupProps {
  email: string;
  minutesSpent: string;
  onEmailChange: (email: string) => void;
  onMinutesChange: (minutes: string) => void;
}

export default function Step2Setup({ 
  email, 
  minutesSpent, 
  onEmailChange, 
  onMinutesChange 
}: Step2SetupProps) {
  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div>
          <Label htmlFor="email" className="text-base font-medium">
            Email address
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => onEmailChange(e.target.value)}
            className="mt-2"
            required
          />
        </div>

        <div>
          <Label htmlFor="minutes" className="text-base font-medium">
            How long do you spend writing CRISSA Notes in minutes?
          </Label>
          <Input
            id="minutes"
            type="number"
            placeholder="e.g 45"
            value={minutesSpent}
            onChange={(e) => onMinutesChange(e.target.value)}
            className="mt-2"
            min="1"
            required
          />
        </div>
      </div>
    </div>
  );
}
