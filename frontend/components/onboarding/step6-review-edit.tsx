import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp, Play } from "lucide-react";

export default function Step6ReviewEdit() {
  const [showExample, setShowExample] = useState(false);

  return (
    <div className="space-y-8 max-w-3xl mx-auto">
      <div className="text-center">
        <h3 className="text-2xl font-semibold mb-6">Review and edit</h3>
      </div>

      {/* Main Content */}
      <div className="space-y-6">
        <p className="text-lg leading-relaxed">
          The AI summary is only a starting point. It captures what was said but it does not see body language or understand the wider context.
        </p>

        <p className="text-lg leading-relaxed">
          Your professional judgement is essential. Add or remove details, include your own observations, and make sure the summary is accurate and useful.
        </p>
      </div>

      {/* Optional Example Toggle */}
      <div className="border border-gray-200 rounded-lg p-4">
        <Button
          variant="ghost"
          onClick={() => setShowExample(!showExample)}
          className="w-full flex items-center justify-between text-left p-0 h-auto font-medium"
        >
          <span>See examples of common edits needed</span>
          {showExample ? (
            <ChevronUp className="h-5 w-5" />
          ) : (
            <ChevronDown className="h-5 w-5" />
          )}
        </Button>

        {showExample && (
          <div className="mt-4 space-y-4">
            <p className="leading-relaxed">
              AI can sometimes mishear things, such as names. For example, Louee might actually be Louis or Louie. Always check and correct these before finalising.
            </p>
            
            {/* Placeholder Video */}
            <div className="bg-gray-100 rounded-lg p-8 text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-full mb-4">
                <Play className="h-6 w-6 text-white ml-1" />
              </div>
              <h4 className="font-semibold mb-2">Example Edits Video</h4>
              <p className="text-sm text-gray-600">
                Watch examples of common AI corrections and professional judgement additions
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
          className="rounded-2xl max-w-full h-auto object-cover"
          style={{ maxHeight: "400px", width: "auto" }}
        />
      </div>
    </div>
  );
}
