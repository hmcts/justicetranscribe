import React from "react";
import { Play } from "lucide-react";

export default function Step6ReviewEdit() {

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div className="text-center space-y-4">
        <h3 className="text-[2.625rem] font-semibold">Review and edit</h3>
        <h4 className="text-xl font-medium bg-gradient-to-r from-blue-600 to-blue-400 bg-clip-text text-transparent">
          Your professional judgement is key
        </h4>
      </div>

      {/* Main Content */}
      <div className="space-y-6">
        <p className="leading-relaxed text-black">
          The AI summary is only a starting point. It captures what was said but it does not see body language, observations or understand the wider context. Edit the summary to make sure its accurate and useful.
        </p>
      </div>

      {/* Two Column Layout - Video Left, Examples Right */}
      <div className="grid gap-8 lg:grid-cols-2">
        {/* Left Column - Video */}
        <div className="rounded-lg bg-gray-100 p-8 text-center">
          <div className="mb-4 inline-flex size-16 items-center justify-center rounded-full bg-blue-600">
            <Play className="ml-1 size-6 text-white" />
          </div>
          <h4 className="mb-2 text-lg font-medium">How to make edits</h4>
          <p className="text-sm text-gray-600">
            Watch how to adjust these using the tool
          </p>
        </div>

        {/* Right Column - Examples */}
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-black">Examples of common edits needed</h4>
          <div className="space-y-2 text-black">
            <p>• Verify names, pronouns, places, and acronyms.</p>
            <p>• Add missing specifics (risk-relevant facts, DOBs).</p>
            <p>• Stay under 4,000 characters for NDelius.</p>
            <p className="font-medium">
              You are the author! Don&apos;t copy and paste without review.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
