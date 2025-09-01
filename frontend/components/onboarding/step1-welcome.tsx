import React from "react";

export default function Step1Welcome() {
  return (
    <div className="space-y-12">
      {/* Header and Description - Single Column */}
      <div className="text-center space-y-8">
        <h2 className="text-4xl font-bold tracking-tight">Welcome 👋</h2>
        <p className="text-lg leading-relaxed text-gray-900 max-w-3xl mx-auto">
          Justice Transcribe is an AI assistant that transcribes and summarises meetings. 
          Turning conversations into clear case notes in minutes so you can stay fully present with people.
        </p>
      </div>

      {/* Quote and Image - Two Columns */}
      <div className="grid lg:grid-cols-2 gap-12 items-center">
        {/* Quote */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl p-8">
          <blockquote className="text-lg italic font-medium text-gray-900 mb-4">
            &quot;I&apos;m spending a lot more time with the people, which is what I wanted to do in the job.&quot;
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
              className="rounded-2xl max-w-full h-auto object-cover"
              style={{ maxHeight: "400px", width: "auto" }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
