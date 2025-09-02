import React from "react";
import { Play } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Step4BasicTutorial() {
  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center">
        <h3 className="text-[2.625rem] font-semibold sm:text-[2.875rem] md:text-[3rem] lg:text-[3.25rem] xl:text-[3.5rem]">
          Basic Tutorial
        </h3>
        <p>Using Justice Transcribe is simple</p>
      </div>

      {/* Video Placeholder */}
      <div className="rounded-lg bg-gray-100 p-12 text-center">
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
      <div className="space-y-3">
        <div className="flex items-start space-x-3">
          <span className="text-lg font-semibold">1.</span>
          <span>
            Click start new meeting and select in person or virtual meeting
          </span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg font-semibold">2.</span>
          <span>Give permission to use your microphone</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg font-semibold">3.</span>
          <span>Click start recording</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg font-semibold">4.</span>
          <span>Click stop recording</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg font-semibold">5.</span>
          <span>
            We&apos;ll email you when your summary is ready for review
          </span>
        </div>
      </div>
    </div>
  );
}
