import React from "react";
import { Play, Check } from "lucide-react";

export default function Step3ReviewEdit() {
  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div className="space-y-3 text-center">
        <h2 className="text-3xl font-semibold sm:text-4xl">Review and edit</h2>
        <h3 className="bg-gradient-to-r from-purple-600 to-purple-400 bg-clip-text text-xl font-medium text-transparent">
          Your professional judgement is key
        </h3>
        <p className="mx-auto max-w-2xl text-lg leading-relaxed text-gray-700">
          The AI summary is only a starting point. Use your professional
          judgement to finalise summaries.
        </p>
      </div>

      {/* Two Column Layout */}
      <div className="grid gap-8 lg:grid-cols-2">
        {/* Video Section */}
        <div className="rounded-lg bg-gray-100 p-6 text-center">
          <div className="mb-4 inline-flex size-20 items-center justify-center rounded-full bg-blue-600">
            <Play className="ml-1 size-8 text-white" />
          </div>
          <h3 className="mb-2 text-xl font-medium">How to make edits</h3>
          <p className="text-gray-600">
            Watch how to adjust these using the tool
          </p>
        </div>

        {/* Checklist Section */}
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-black">
            Common corrections
          </h3>
          <div className="space-y-4 text-black">
            <div className="flex items-start space-x-3">
              <Check className="mt-1 size-5 shrink-0 text-green-600" />
              <p className="text-base">
                Verify names, pronouns, places, and acronyms.
              </p>
            </div>
            <div className="flex items-start space-x-3">
              <Check className="mt-1 size-5 shrink-0 text-green-600" />
              <p className="text-base">
                Add missing specifics (risk-relevant facts, DOBs).
              </p>
            </div>
            <div className="flex items-start space-x-3">
              <Check className="mt-1 size-5 shrink-0 text-green-600" />
              <p className="text-base">
                Stay under 4,000 characters for NDelius.
              </p>
            </div>
            <div className="flex items-start space-x-3">
              <Check className="mt-1 size-5 shrink-0 text-green-600" />
              <p className="text-base">
                Describe body language, observations and wider context.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
