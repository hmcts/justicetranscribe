import React from "react";

export default function Step6ReviewEdit() {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h3 className="text-2xl font-semibold mb-6">Review and edit</h3>
      </div>

      {/* Main Content with Image */}
      <div className="grid lg:grid-cols-2 gap-8 items-start">
        {/* Content */}
        <div className="space-y-6">
          <p className="leading-relaxed">
            You need to add your professional judgement to the AI generated summary. 
            Choose what to keep, change, delete and add as AI only captures what&apos;s been said! 
            It doesn&apos;t see or know body language, context and your observations.
          </p>

          <p className="leading-relaxed">
            Sometimes AI will be wrong for example the name sounding Louwee could be spelt Louis or Louie.
          </p>
        </div>

        {/* Image */}
        <div className="flex justify-center lg:justify-end">
          <img
            src="/Probation Officer reading.png"
            alt="Probation officer reading and reviewing documents"
            className="rounded-2xl max-w-full h-auto object-cover"
            style={{ maxHeight: "500px", width: "auto" }}
          />
        </div>
      </div>
    </div>
  );
}
