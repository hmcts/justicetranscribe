import React from "react";
import { Button } from "@/components/ui/button";

interface Step6ReadyProps {
  onGetStarted: () => void;
  onBack: () => void;
}

export default function Step6Ready({
  onGetStarted,
  onBack,
}: Step6ReadyProps) {
  return (
    <div className="space-y-8">
      <div className="space-y-2 text-center">
        <h2 className="text-[2.625rem] font-semibold sm:text-[2.875rem] md:text-[3rem] lg:text-[3.25rem] xl:text-[3.5rem]">
          You&apos;re ready 🎉
        </h2>
        <p className="text-black">
          Start today to spend less time note taking and more time listening
        </p>
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
        {/* Back button positioned absolutely left */}
        <div className="relative">
          <Button
            onClick={onBack}
            variant="outline"
            className="absolute left-0"
          >
            Back
          </Button>

          {/* Centered main action */}
          <div className="flex justify-center">
            <Button
              onClick={onGetStarted}
              className="bg-black px-12 py-6 text-lg text-white hover:bg-black/90"
            >
              Get started
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
