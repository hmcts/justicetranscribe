import React from "react";
import { Button } from "@/components/ui/button";

interface Step7ReadyProps {
  onStartRecording: () => void;
  onNeedHelp: () => void;
  onBack: () => void;
}

export default function Step7Ready({ onStartRecording, onNeedHelp, onBack }: Step7ReadyProps) {
  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h3 className="text-2xl font-semibold">You&apos;re ready</h3>
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
          <span>Review and edit summaries to add your professional judgement</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <button
            onClick={onNeedHelp}
            className="text-blue-600 hover:underline text-left"
          >
            Need help? Visit support
          </button>
        </div>
      </div>

      {/* Quote */}
      <div className="bg-gray-50 border-l-4 border-green-500 p-6 rounded-r-lg">
        <blockquote className="italic">
          &quot;The Justice Transcribe AI has been life-saving… the amount of time it saves is invaluable.&quot;
        </blockquote>
        <cite className="text-sm mt-2 block">
          — KSS Probation Service Officer
        </cite>
      </div>

      {/* Action Buttons */}
      <div className="space-y-6 pt-4">
        <div className="flex justify-between items-center">
          <Button 
            onClick={onBack}
            variant="outline"
          >
            Back
          </Button>
          
          <div className="flex-1 flex justify-center">
            <Button 
              onClick={onStartRecording}
              className="bg-black text-white hover:bg-black/90 py-6 text-lg px-12"
            >
              Start first recording
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
