import React from "react";

export default function Step1Welcome() {
  return (
    <div className="space-y-[3rem]">
      {/* Header and Description - Single Column */}
      <div className="space-y-[2rem] text-center">
        <h2 className="text-[2.25rem] font-bold tracking-tight bg-gradient-to-r from-blue-600 to-blue-400 bg-clip-text text-transparent">Welcome 👋</h2>
        <p className="mx-auto max-w-[60rem] text-[1.125rem] leading-relaxed text-black">
          Justice Transcribe is an AI assistant that transcribes and summarises
          meetings. Turning conversations into clear case notes in minutes so
          you can stay fully present with people.
        </p>
      </div>

      {/* Quote and Image - Two Columns */}
      <div className="grid items-center gap-[3rem] lg:grid-cols-2">
        {/* Quote */}
        <div className="rounded-2xl border border-blue-100 bg-gradient-to-r from-blue-50 to-indigo-50 p-[2rem]">
          <blockquote className="mb-[1rem] text-[1.125rem] font-medium italic text-black">
            &quot;I&apos;m spending a lot more time with the people, which is
            what I wanted to do in the job.&quot;
          </blockquote>
          <cite className="text-[1rem] font-medium text-black">
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
              style={{ maxHeight: "25rem", width: "auto" }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
