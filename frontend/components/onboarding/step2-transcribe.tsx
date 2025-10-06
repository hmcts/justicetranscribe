import React from "react";
import { Play } from "lucide-react";

export default function Step2BasicTutorial() {
  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div className="space-y-3 text-center">
        <h1 className="text-3xl font-semibold sm:text-4xl">Transcribe a Meeting</h1>
        <h2 className="bg-gradient-to-r from-blue-600 to-blue-400 bg-clip-text text-xl font-medium text-transparent">
          Using Justice Transcribe is simple
        </h2>
      </div>

      {/* Two Column Layout */}
      <div className="grid gap-8 lg:grid-cols-2">
        {/* Video Section */}
        <div className="rounded-lg bg-gray-100 p-6 text-center">
          <div className="mb-4 inline-flex size-20 items-center justify-center rounded-full bg-blue-600">
            <Play className="ml-1 size-8 text-white" />
          </div>
          <h3 className="mb-2 text-xl font-medium">How to record a meeting</h3>
          <p className="text-gray-600">
            Watch how to use the recording tool
          </p>
        </div>

        {/* Steps Section */}
        <div className="space-y-4">
          <div className="space-y-4 text-black" aria-label="How to record a meeting steps">
            <p className="text-base">
              <span className="mr-2 font-semibold text-blue-600">1.</span>
              Click start new meeting and select in person or virtual meeting
            </p>
            <p className="text-base">
              <span className="mr-2 font-semibold text-blue-600">2.</span>
              Give permission to use your microphone
            </p>
            <p className="text-base">
              <span className="mr-2 font-semibold text-blue-600">3.</span>
              Click start recording
            </p>
            <p className="text-base">
              <span className="mr-2 font-semibold text-blue-600">4.</span>
              Click stop recording
            </p>
            <p className="text-base">
              <span className="mr-2 font-semibold text-blue-600">5.</span>
              We&apos;ll email you when your summary is ready for review
            </p>
            <p className="mt-6 text-base text-black">
              You can record for up to 2 hours per session.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

