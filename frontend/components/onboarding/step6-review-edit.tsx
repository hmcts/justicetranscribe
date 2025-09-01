import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp, Play } from "lucide-react";

export default function Step6ReviewEdit() {
  const [showExample, setShowExample] = useState(false);

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div className="text-center">
        <h3 className="mb-6 text-2xl font-semibold">Review and edit</h3>
      </div>

      {/* Main Content */}
      <div className="space-y-6">
        <p className="leading-relaxed">
          The AI summary is only a starting point. It captures what was said but
          it does not see body language or understand the wider context.
        </p>

        <p className="leading-relaxed">
          Your professional judgement is essential. Add or remove details,
          include your own observations, and make sure the summary is accurate
          and useful.
        </p>
      </div>

      {/* Optional Example Toggle */}
      <div className="rounded-lg border border-gray-200 p-4">
        <Button
          variant="ghost"
          onClick={() => setShowExample(!showExample)}
          className="flex h-auto w-full items-center justify-between p-0 text-left"
        >
          <span>See examples of common edits needed</span>
          {showExample ? (
            <ChevronUp className="size-5" />
          ) : (
            <ChevronDown className="size-5" />
          )}
        </Button>

        {showExample && (
          <div className="mt-4 space-y-4">
            <div className="space-y-2 text-sm text-gray-700">
              <p>• Verify names, pronouns, places, and acronyms.</p>
              <p>• Add missing specifics (risk-relevant facts, DOBs).</p>
              <p>• Stay under 4,000 characters for NDelius.</p>
              <p className="font-medium">
                You are the author! Don&apos;t copy and paste without review.
              </p>
            </div>

            {/* Placeholder Video */}
            <div className="rounded-lg bg-gray-100 p-6 text-center">
              <div className="mb-3 inline-flex size-12 items-center justify-center rounded-full bg-blue-600">
                <Play className="ml-1 size-5 text-white" />
              </div>
              <h4 className="mb-1 font-medium">How to make edits</h4>
              <p className="text-xs text-gray-600">
                Watch how to adjust these using the tool
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Image */}
      <div className="flex justify-center">
        <img
          src="/Probation Officer reading.png"
          alt="Probation officer reading and reviewing documents"
          className="h-auto max-w-full rounded-2xl object-cover"
          style={{ maxHeight: "320px", width: "auto" }}
        />
      </div>
    </div>
  );
}
