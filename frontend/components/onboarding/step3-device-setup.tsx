import React, { useState } from "react";
import { Monitor, Smartphone } from "lucide-react";

export default function Step3DeviceSetup() {
  const [selectedDevice, setSelectedDevice] = useState<"desktop" | "mobile">(
    "desktop",
  );

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center">
        <h3 className="text-2xl font-semibold">Device setup</h3>
        <p>Optimise your device for the best recording experience.</p>
      </div>

      {/* Device Toggle */}
      <div className="flex justify-center">
        <div className="grid w-full max-w-md grid-cols-2 gap-4">
          <button
            type="button"
            onClick={() => setSelectedDevice("desktop")}
            className={`flex items-center justify-center space-x-2 rounded-lg border p-4 transition-colors ${
              selectedDevice === "desktop"
                ? "border-black bg-black text-white"
                : "border-gray-200 bg-gray-50 hover:bg-gray-100"
            }`}
          >
            <Monitor className="size-5" />
            <span>Desktop</span>
          </button>
          <button
            type="button"
            onClick={() => setSelectedDevice("mobile")}
            className={`flex items-center justify-center space-x-2 rounded-lg border p-4 transition-colors ${
              selectedDevice === "mobile"
                ? "border-black bg-black text-white"
                : "border-gray-200 bg-gray-50 hover:bg-gray-100"
            }`}
          >
            <Smartphone className="size-5" />
            <span>Mobile</span>
          </button>
        </div>
      </div>

      {/* Desktop Content */}
      {selectedDevice === "desktop" && (
        <div className="space-y-4">
          <h4 className="text-lg font-semibold">Save as bookmark</h4>
          <p>Save as bookmark to find JT easily</p>
          <div className="space-y-2">
            <div className="flex items-start space-x-3">
              <span className="text-lg">•</span>
              <span>Press Ctrl+D (Windows) or Cmd+D (Mac)</span>
            </div>
            <div className="flex items-start space-x-3">
              <span className="text-lg">•</span>
              <span>Save to bookmarks bar for quick access</span>
            </div>
            <div className="flex items-start space-x-3">
              <span className="text-lg">•</span>
              <span>Use external microphone for better quality</span>
            </div>
          </div>
        </div>
      )}

      {/* Mobile Content */}
      {selectedDevice === "mobile" && (
        <div className="space-y-4">
          <h4 className="text-lg font-semibold">
            Do these things to avoid losing your recording
          </h4>
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <span className="font-semibold">1.</span>
              <span>
                Turn on &apos;Do Not Disturb&apos; to stop calls or
                notifications from interrupting. Do this by swiping down from
                top right corner and tap the moon icon.
              </span>
            </div>
            <div className="flex items-start space-x-3">
              <span className="font-semibold">2.</span>
              <span>
                Don&apos;t refresh the page as this will delete the recording.
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
