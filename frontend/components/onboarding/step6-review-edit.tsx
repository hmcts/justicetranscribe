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
            <p className="text-sm leading-relaxed">
              AI can sometimes mishear things, such as names. For example, Louee
              might actually be Louis or Louie. Always check and correct these
              before finalising.
            </p>

            {/* Placeholder Video */}
            <div className="rounded-lg bg-gray-100 p-6 text-center">
              <div className="mb-3 inline-flex size-12 items-center justify-center rounded-full bg-blue-600">
                <Play className="ml-1 size-5 text-white" />
              </div>
              <h4 className="mb-1 font-medium">Example Edits Video</h4>
              <p className="text-xs text-gray-600">
                Watch examples of common AI corrections and professional
                judgement additions
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
