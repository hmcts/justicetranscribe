import React from "react";
import { Play, Check } from "lucide-react";

export default function Step6ReviewEdit() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="space-y-2 text-center">
        <h3 className="text-[2.625rem] font-semibold sm:text-[2.875rem] md:text-[3rem] lg:text-[3.25rem] xl:text-[3.5rem]">
          Review and edit
        </h3>
        <h4 className="bg-gradient-to-r from-purple-600 to-purple-400 bg-clip-text text-xl font-medium text-transparent">
          Your professional judgement is key
        </h4>
      </div>

      {/* Main Content */}
      <div className="space-y-4">
        <p className="text-center leading-relaxed text-black">
          The AI summary is only a starting point. Use your professional
          judgement to finalise summaries.
        </p>
      </div>

      {/* Single Column Layout */}
      <div className="space-y-8">
        {/* Video Section */}
        <div className="rounded-lg bg-gray-100 p-8 text-center">
          <div className="mb-4 inline-flex size-16 items-center justify-center rounded-full bg-blue-600">
            <Play className="ml-1 size-6 text-white" />
          </div>
          <h4 className="mb-2 text-lg font-medium">How to make edits</h4>
          <p className="text-sm text-gray-600">
            Watch how to adjust these using the tool
          </p>
        </div>

        {/* Checklist Section */}
        <div className="space-y-4">
          <h4 className="text-center text-lg font-semibold text-black">
            Common corrections
          </h4>
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
