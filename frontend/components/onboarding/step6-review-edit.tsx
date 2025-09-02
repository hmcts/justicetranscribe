import React from "react";
import { Play } from "lucide-react";

export default function Step6ReviewEdit() {

  return (
    <div className="mx-auto max-w-[60rem] space-y-8">
      <div className="text-center space-y-4">
        <h3 className="text-[2.25rem] font-semibold bg-gradient-to-r from-blue-600 to-blue-400 bg-clip-text text-transparent">Review and edit</h3>
        <h4 className="text-[1.25rem] font-medium bg-gradient-to-r from-blue-600 to-blue-400 bg-clip-text text-transparent">Your professional judgement is key</h4>
      </div>

      {/* Main Content */}
      <div className="space-y-6">
        <p className="text-[1.125rem] leading-relaxed text-black">
          The AI summary is only a starting point. It captures what was said but it does not see body language, observations or understand the wider context. Edit the summary to make sure its accurate and useful.
        </p>
      </div>

      {/* Two Column Layout - Video Left, Examples Right */}
      <div className="grid gap-8 lg:grid-cols-2">
        {/* Left Column - Video */}
        <div className="rounded-lg bg-gray-100 p-[2rem] text-center">
          <div className="mb-[1rem] inline-flex h-[4rem] w-[4rem] items-center justify-center rounded-full bg-blue-600">
            <Play className="ml-1 h-[1.5rem] w-[1.5rem] text-white" />
          </div>
          <h4 className="mb-[0.5rem] text-[1.25rem] font-medium">How to make edits</h4>
          <p className="text-[1rem] text-black">
            Watch how to adjust these using the tool
          </p>
        </div>

        {/* Right Column - Examples */}
        <div className="space-y-[1rem]">
          <h4 className="text-[1.25rem] font-semibold text-black">Examples of common edits needed</h4>
          <div className="space-y-[0.75rem] text-[1rem] text-black">
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
