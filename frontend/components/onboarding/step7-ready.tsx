import React from "react";
import { Button } from "@/components/ui/button";

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
  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center">
        <h3 className="text-2xl font-semibold">You&apos;re ready 🎉</h3>
        <p>
          Start today to spend less time note taking and more time listening
        </p>
      </div>

      {/* Features */}
      <div className="space-y-3">
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <span>Record sessions with a few clicks</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <span>Get email alert when ready</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <span>
            Review and edit summaries to add your professional judgement
          </span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <button
            type="button"
            onClick={onNeedHelp}
            className="text-left text-blue-600 hover:underline"
          >
            Need help? Visit support
          </button>
        </div>
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
