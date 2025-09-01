import React from "react";

export default function Step6ReviewEdit() {
  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h3 className="text-2xl font-semibold">Review and edit</h3>
        <p>
          You need to add your professional judgement to the AI generated summary. 
          You choose what to keep, change, delete and add.
        </p>
      </div>

      {/* Key Message */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
        <p className="text-blue-900 font-medium">
          AI captures what&apos;s said. You add what&apos;s not said - body language, context, and observations
        </p>
      </div>

      {/* Example */}
      <div className="space-y-4">
        <h4 className="text-lg font-semibold">Example: Adding context</h4>
        
        <div className="space-y-4">
          <div className="bg-gray-50 border rounded-lg p-4">
            <p className="text-sm font-medium text-gray-600 mb-2">Original AI summary:</p>
            <p className="italic">&quot;Session proceeded normally.&quot;</p>
          </div>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-sm font-medium text-green-700 mb-2">Your enhanced version:</p>
            <p className="italic">
              &quot;Session proceeded normally. Client has a black eye but refused to discuss it when asked directly.&quot;
            </p>
          </div>
        </div>
      </div>

      {/* Guidelines */}
      <div className="space-y-3">
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <span>Add the observations not captured in audio</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <span>Remove irrelevant information</span>
        </div>
        <div className="flex items-start space-x-3">
          <span className="text-lg">•</span>
          <span>Your professional judgement completes the picture</span>
        </div>
      </div>
    </div>
  );
}
