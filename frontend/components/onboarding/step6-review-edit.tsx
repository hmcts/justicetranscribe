import React from "react";

export default function Step6ReviewEdit() {
  return (
    <div className="space-y-12 max-w-3xl mx-auto">
      <div className="text-center">
        <h3 className="text-2xl font-semibold mb-6">Review and edit</h3>
      </div>

      {/* Main Content */}
      <div className="space-y-6">
        <p className="text-lg leading-relaxed">
          The AI summary is only a starting point. It captures what was said but it does not see body language or understand the wider context.
        </p>

        <p className="text-lg leading-relaxed">
          Your professional judgement is essential. Add or remove details, include your own observations, and make sure the summary is accurate and useful.
        </p>

        <p className="text-lg leading-relaxed">
          AI can sometimes mishear things, such as names. For example, Louee might actually be Louis or Louie. Always check and correct these before finalising.
        </p>
      </div>

      {/* Image */}
      <div className="flex justify-center">
        <img
          src="/Probation Officer reading.png"
          alt="Probation officer reading and reviewing documents"
          className="rounded-2xl max-w-full h-auto object-cover"
          style={{ maxHeight: "600px", width: "auto" }}
        />
      </div>
    </div>
  );
}
