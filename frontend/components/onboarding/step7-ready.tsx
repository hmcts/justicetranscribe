import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ChevronDown, ChevronUp, Play } from "lucide-react";

interface Step7ReadyProps {
  onStartRecording: () => void;
  onNeedHelp: () => void;
  onBack: () => void;
}

export default function Step7Ready({
  onStartRecording,
  onNeedHelp,
  onBack,
}: Step7ReadyProps) {
  const [showExamples, setShowExamples] = useState(false);

  return (
    <div className="space-y-8">
      <div className="space-y-2 text-center">
        <h3 className="text-2xl font-semibold">You&apos;re ready 🎉</h3>
        <p>
          Start today to spend less time note taking and more time listening
        </p>
      </div>

      {/* 4-Step Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Step 1 */}
        <Card className="p-4">
          <div className="space-y-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
              1
            </div>
            <h4 className="font-semibold">Record the session</h4>
            <p className="text-sm text-gray-600">
              Click start and stop on your work mobile or laptop. You can also dictate after a session if recording isn&apos;t appropriate.
            </p>
          </div>
        </Card>

        {/* Step 2 */}
        <Card className="p-4">
          <div className="space-y-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-600 text-sm font-bold text-white">
              2
            </div>
            <h4 className="font-semibold">We&apos;ll email when it&apos;s ready</h4>
            <p className="text-sm text-gray-600">
              Open the summary from your inbox.
            </p>
          </div>
        </Card>

        {/* Step 3 */}
        <Card className="p-4">
          <div className="space-y-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-orange-600 text-sm font-bold text-white">
              3
            </div>
            <h4 className="font-semibold">Review & edit</h4>
            <p className="text-sm text-gray-600">
              Add your professional judgement and correct anything the AI misheard or missed
            </p>
            
            {/* Examples Dropdown */}
            <div className="mt-3 border border-gray-200 rounded-lg">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setShowExamples(!showExamples)}
                className="w-full flex items-center justify-between text-left p-3 h-auto text-sm"
              >
                <span>Examples of common edits needed</span>
                {showExamples ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>

              {showExamples && (
                <div className="px-3 pb-3 space-y-3">
                  <div className="space-y-2 text-xs text-gray-700">
                    <p>• Verify names, pronouns, places, and acronyms.</p>
                    <p>• Add missing specifics (risk-relevant facts, DOBs).</p>
                    <p>• Stay under 4,000 characters for NDelius.</p>
                    <p className="font-medium">You are the author! Don&apos;t copy and paste without review.</p>
                  </div>
                  
                  {/* Video Placeholder */}
                  <div className="bg-gray-100 rounded-lg p-4 text-center">
                    <div className="inline-flex items-center justify-center w-10 h-10 bg-blue-600 rounded-full mb-2">
                      <Play className="h-4 w-4 text-white ml-0.5" />
                    </div>
                    <p className="text-xs font-medium">How to make edits</p>
                    <p className="text-xs text-gray-600">
                      Watch how to adjust these using the tool
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* Step 4 */}
        <Card className="p-4">
          <div className="space-y-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-purple-600 text-sm font-bold text-white">
              4
            </div>
            <h4 className="font-semibold">Copy and paste 🎉</h4>
            <p className="text-sm text-gray-600">
              <button
                type="button"
                onClick={onNeedHelp}
                className="text-blue-600 hover:underline"
              >
                Need help? Visit support
              </button>
            </p>
          </div>
        </Card>
      </div>

      {/* Quote */}
      <div className="rounded-r-lg border-l-4 border-green-500 bg-gray-50 p-6">
        <blockquote className="italic">
          &quot;The Justice Transcribe AI has been life-saving… the amount of
          time it saves is invaluable.&quot;
        </blockquote>
        <cite className="mt-2 block text-sm">
          — KSS Probation Service Officer
        </cite>
      </div>

      {/* Action Buttons */}
      <div className="space-y-6 pt-4">
        <div className="flex items-center justify-between">
          <Button onClick={onBack} variant="outline">
            Back
          </Button>

          <div className="flex flex-1 justify-center">
            <Button
              onClick={onStartRecording}
              className="bg-black px-12 py-6 text-lg text-white hover:bg-black/90"
            >
              Start first recording
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
