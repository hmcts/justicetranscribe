import React from "react";

export default function Step1Welcome() {
  return (
    <div className="space-y-6">
      <div className="text-center space-y-4">
        <h2 className="text-3xl font-bold">Welcome to Justice Transcribe</h2>
        <p className="text-xl">
          Spend less time notetaking and more time listening.
        </p>
      </div>

      <div className="space-y-3">
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <span>Save hours of admin</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <span>Focus on the person, not the notes</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <span>Review your secure high quality notes</span>
        </div>
      </div>

      <div className="bg-gray-50 border-l-4 border-blue-500 p-6 rounded-r-lg">
        <blockquote className="italic">
          &quot;I&apos;m spending a lot more time with the people, which is what I wanted to do in the job.&quot;
        </blockquote>
        <cite className="text-sm mt-2 block">
          — Wales Probation Officer
        </cite>
      </div>
    </div>
  );
}
