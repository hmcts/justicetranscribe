import React from "react";

export default function Step1Welcome() {
  return (
    <div className="space-y-12">
      {/* Header */}
      <div className="text-center space-y-6">
        <h2 className="text-4xl font-bold tracking-tight">Welcome to Justice Transcribe</h2>
        <p className="text-2xl font-light text-gray-900 max-w-2xl mx-auto">
          Spend less time notetaking and more time listening.
        </p>
      </div>

      {/* Main Content with Image */}
      <div className="grid lg:grid-cols-2 gap-12 items-center">
        {/* Benefits */}
        <div className="space-y-8">
          <div className="space-y-6">
            <div className="space-y-2">
              <h3 className="text-xl font-semibold">Save hours of admin</h3>
              <p className="text-gray-700 leading-relaxed">
                Transform lengthy note-taking sessions into streamlined summaries.
              </p>
            </div>
            
            <div className="space-y-2">
              <h3 className="text-xl font-semibold">Focus on the person, not the notes</h3>
              <p className="text-gray-700 leading-relaxed">
                Maintain eye contact and build rapport while AI handles the documentation.
              </p>
            </div>
            
            <div className="space-y-2">
              <h3 className="text-xl font-semibold">Review your secure high quality notes</h3>
              <p className="text-gray-700 leading-relaxed">
                Get accurate transcriptions with professional-grade security standards.
              </p>
            </div>
          </div>
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

      {/* Quote */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl p-8 text-center">
        <blockquote className="text-lg italic font-medium text-gray-900 mb-4">
          &quot;I&apos;m spending a lot more time with the people, which is what I wanted to do in the job.&quot;
        </blockquote>
        <cite className="text-sm font-medium text-gray-600">
          — Wales Probation Officer
        </cite>
      </div>
    </div>
  );
}
