import React from "react";
import { Play, Check } from "lucide-react";

export default function Step5ReviewEdit() {
  return (
    <div className="mx-auto max-w-2xl space-y-3">
      <div className="space-y-1 text-center">
        <h2 className="text-2xl font-semibold sm:text-3xl">
          Review and edit
        </h2>
        <h3 className="bg-gradient-to-r from-purple-600 to-purple-400 bg-clip-text text-xl font-medium text-transparent">
          Your professional judgement is key
        </h3>
      </div>

      {/* Main Content */}
      <div className="space-y-1.5">
        <p className="text-center leading-relaxed text-black">
          The AI summary is only a starting point. Use your professional
          judgement to finalise summaries.
        </p>
      </div>

      {/* Single Column Layout */}
      <div className="space-y-3">
        {/* Video Section */}
        <div className="rounded-lg bg-gray-100 p-5 text-center">
          <div className="mb-4 inline-flex size-16 items-center justify-center rounded-full bg-blue-600">
            <Play className="ml-1 size-6 text-white" />
          </div>
          <h3 className="mb-2 text-lg font-medium">How to make edits</h3>
          <p className="text-sm text-gray-600">
            Watch how to adjust these using the tool
          </p>
        </div>

        {/* Checklist Section */}
        <div className="space-y-2.5">
          <h3 className="text-center text-lg font-semibold text-black">
            Common corrections
          </h3>
          <div className="mx-auto max-w-lg space-y-3 text-black">
            <div className="flex items-start space-x-3">
              <Check className="mt-0.5 size-5 shrink-0 text-green-600" />
              <p>Verify names, pronouns, places, and acronyms.</p>
            </div>
            <div className="flex items-start space-x-3">
              <Check className="mt-0.5 size-5 shrink-0 text-green-600" />
              <p>Add missing specifics (risk-relevant facts, DOBs).</p>
            </div>
            <div className="flex items-start space-x-3">
              <Check className="mt-0.5 size-5 shrink-0 text-green-600" />
              <p>Stay under 4,000 characters for NDelius.</p>
            </div>
            <div className="flex items-start space-x-3">
              <Check className="mt-0.5 size-5 shrink-0 text-green-600" />
              <p>Describe body language, observations and wider context.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
