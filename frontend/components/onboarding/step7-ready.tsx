import React from "react";
import { Button } from "@/components/ui/button";
import { Mic, Mail, Edit, Copy } from "lucide-react";

interface Step7ReadyProps {
  onStartRecording: () => void;
  onBack: () => void;
}

export default function Step7Ready({
  onStartRecording,
  onBack,
}: Step7ReadyProps) {
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

      {/* Horizontal Checklist */}
      <div className="space-y-6">
        {/* Step 1 */}
        <div className="flex items-start space-x-4">
          <div className="flex size-10 items-center justify-center rounded-full bg-blue-100">
            <Mic className="size-5 text-blue-600" />
          </div>
          <div className="flex-1">
            <h4 className="text-lg font-semibold text-black">
              Record the session
            </h4>
            <p className="text-black">
              Click start and stop on your work mobile or laptop. You can also
              dictate after a session if recording isn&apos;t appropriate.
            </p>
          </div>
        </div>

        {/* Step 2 */}
        <div className="flex items-start space-x-4">
          <div className="flex size-10 items-center justify-center rounded-full bg-green-100">
            <Mail className="size-5 text-green-600" />
          </div>
          <div className="flex-1">
            <h4 className="text-lg font-semibold text-black">
              We&apos;ll email when it&apos;s ready
            </h4>
            <p className="text-black">Open the summary from your inbox.</p>
          </div>
        </div>

        {/* Step 3 */}
        <div className="flex items-start space-x-4">
          <div className="flex size-10 items-center justify-center rounded-full bg-orange-100">
            <Edit className="size-5 text-orange-600" />
          </div>
          <div className="flex-1">
            <h4 className="text-lg font-semibold text-black">Review & edit</h4>
            <p className="text-black">
              Add your professional judgement and correct anything the AI
              misheard or missed
            </p>
          </div>
        </div>

        {/* Step 4 */}
        <div className="flex items-start space-x-4">
          <div className="flex size-10 items-center justify-center rounded-full bg-purple-100">
            <Copy className="size-5 text-purple-600" />
          </div>
          <div className="flex-1">
            <h4 className="text-lg font-semibold text-black">
              Copy and paste 🎉
            </h4>
            <p className="text-black">
              You&apos;re all set to create professional case notes in minutes.
            </p>
          </div>
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
