import React from "react";
import { Play } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Step4BasicTutorial() {
  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h3 className="text-2xl font-semibold">Basic Tutorial</h3>
        <p>
          Using Justice Transcribe is simple
        </p>
      </div>

      {/* Video Placeholder */}
      <div className="bg-gray-100 rounded-lg p-12 text-center">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-200 flex items-center justify-center">
          <Play className="w-8 h-8 text-gray-500" />
        </div>
        <p className="text-gray-600 mb-4">Basic Tutorial Video</p>
        <Button variant="outline" disabled>
          <Play className="w-4 h-4 mr-2" />
          Play Video (Coming Soon)
        </Button>
      </div>

      {/* Steps */}
      <div className="space-y-3">
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <span>Click start new meeting and select in person or virtual meeting</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <span>Give permission to use your microphone</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <span>Click start recording</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <span>Click stop recording</span>
        </div>
      </div>
    </div>
  );
}
