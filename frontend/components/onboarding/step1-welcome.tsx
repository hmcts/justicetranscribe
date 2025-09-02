import React from "react";

export default function Step1Welcome() {
  return (
    <div className="space-y-12">
      {/* Header and Description - Single Column */}
      <div className="space-y-8 text-center">
        <h2 className="text-[2.625rem] font-bold tracking-tight sm:text-[2.875rem] md:text-[3rem] lg:text-[3.25rem] xl:text-[3.5rem]">
          Welcome 👋
        </h2>
        <p className="mx-auto max-w-3xl text-lg leading-relaxed text-gray-900">
          Justice Transcribe is an AI assistant that transcribes and summarises
          meetings. Turning conversations into clear case notes in minutes so
          you can stay fully present with people.
        </p>
      </div>

      {/* Quote and Image - Two Columns */}
      <div className="grid items-center gap-12 lg:grid-cols-2">
        {/* Quote */}
        <div className="rounded-2xl border border-blue-100 bg-gradient-to-r from-blue-50 to-indigo-50 p-8">
          <blockquote className="mb-4 text-lg font-medium italic text-gray-900">
            &quot;I&apos;m spending a lot more time with the people, which is
            what I wanted to do in the job.&quot;
          </blockquote>
          <cite className="text-sm font-medium text-gray-600">
            — Wales Probation Officer
          </cite>
        </div>

        {/* Image */}
        <div className="flex justify-center lg:justify-end">
          <div className="relative">
            <img
              src="/Probation officer listening.png"
              alt="Probation officer listening attentively to client"
              className="h-auto max-w-full rounded-2xl object-cover"
              style={{ maxHeight: "400px", width: "auto" }}
            />
          </div>
        </div>
      </div>

      {/* Action Buttons moved to bottom navigation in onboarding/page.tsx */}
    </div>
  );
}
