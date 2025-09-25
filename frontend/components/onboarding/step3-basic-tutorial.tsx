import React from "react";
import { Play } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Step4BasicTutorial() {
  return (
    <div className="space-y-3">
      <div className="space-y-1 text-center">
        <h2 className="text-2xl font-semibold sm:text-3xl">
          Basic Tutorial
        </h2>
        <p>Using Justice Transcribe is simple</p>
      </div>

      {/* Video Placeholder */}
      <div className="rounded-lg bg-gray-100 p-5 text-center">
        <div className="mx-auto mb-4 flex size-16 items-center justify-center rounded-full bg-gray-200">
          <Play className="size-8 text-gray-500" />
        </div>
        <p className="mb-4 text-gray-600">Basic Tutorial Video</p>
        <Button variant="outline" disabled>
          <Play className="mr-2 size-4" />
          Play Video (Coming Soon)
        </Button>
      </div>

      {/* Steps */}
      <div className="space-y-1.5">
        <div className="flex items-start space-x-3">
          <span className="text-base font-semibold">1.</span>
          <span>
            Click start new meeting and select in person or virtual meeting
          </span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-base font-semibold">2.</span>
          <span>Give permission to use your microphone</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-base font-semibold">3.</span>
          <span>Click start recording</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-base font-semibold">4.</span>
          <span>Click stop recording</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-base font-semibold">5.</span>
          <span>
            We&apos;ll email you when your summary is ready for review
          </span>
        </div>
      </div>
    </div>
  );
}
