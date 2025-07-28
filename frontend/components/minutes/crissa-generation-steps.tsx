// /* eslint-disable no-promise-executor-return */
// /* eslint-disable no-await-in-loop */
// /* eslint-disable react/no-array-index-key */
// /* eslint-disable react/button-has-type */
// /* eslint-disable @typescript-eslint/no-use-before-define */

// "use client";

// import React, { useState } from "react";
// import SimpleEditor from "@/components/editor/tiptap-editor";
// import { useTranscripts } from "@/providers/transcripts";
// import { removeCitations } from "@/app/utils/download-word-doc";
// import { CopyCrissaButton } from "@/components/ui/copy-button";
// import { pollLLMOutput } from "@/lib/polling";

// const TOTAL_PROMPTS = 6;

// export default function CrissaGenerationSteps() {
//   const { currentTranscription } = useTranscripts();
//   const [currentStep, setCurrentStep] = useState(0);
//   const [outputs, setOutputs] = useState<string[]>(Array(6).fill(""));
//   const [originalOutputs, setOriginalOutputs] = useState<string[]>(
//     Array(6).fill(""),
//   );
//   const [editingIndex, setEditingIndex] = useState<number | null>(null);
//   const [lastStepApproved, setLastStepApproved] = useState(false);
//   const [isLoading, setIsLoading] = useState(false);
//   // eslint-disable-next-line @typescript-eslint/no-unused-vars
//   const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
//   const [sectionTraceIds, setSectionTraceIds] = useState<(string | null)[]>(
//     Array(6).fill(null),
//   );

//   const handleContentChangeInEditor = (index: number, newContent: string) => {
//     const newOutputs = [...outputs];
//     newOutputs[index] = newContent;
//     setOutputs(newOutputs);
//   };

//   const generateSection = async (step: number) => {
//     if (!currentTranscription?.dialogue_entries) return;

//     try {
//       setIsLoading(true);
//       const response = await fetch("/api/proxy/generate-crissa-section", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({
//           transcript: currentTranscription.dialogue_entries,
//           step,
//           previous_outputs: outputs.slice(0, step),
//         }),
//       });

//       const data = await response.json();
//       setCurrentTaskId(data.task_id);

//       try {
//         const llmOutput = await pollLLMOutput(data.task_id);

//         // Store in both arrays
//         const newOutputs = [...outputs];
//         const newOriginalOutputs = [...originalOutputs];
//         newOutputs[step] = llmOutput;
//         newOriginalOutputs[step] = llmOutput;
//         setOutputs(newOutputs);
//         setOriginalOutputs(newOriginalOutputs);

//         // Store trace ID
//         const newTraceIds = [...sectionTraceIds];
//         newTraceIds[step] = data.trace_id;
//         setSectionTraceIds(newTraceIds);

//         setCurrentTaskId(null);
//       } catch (error) {
//         console.error("Error generating section:", error);
//       }
//     } catch (error) {
//       console.error("Error generating section:", error);
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const logSectionEdit = async (step: number) => {
//     const traceId = sectionTraceIds[step];
//     if (!traceId) return;

//     // Only log if content has changed from original
//     if (outputs[step] !== originalOutputs[step]) {
//       try {
//         await fetch("/api/log-crissa-edit", {
//           method: "POST",
//           headers: { "Content-Type": "application/json" },
//           body: JSON.stringify({
//             trace_id: traceId,
//             step,
//             edited_content: outputs[step],
//           }),
//         });
//       } catch (error) {
//         console.error("Error logging edit:", error);
//       }
//     }
//   };

//   const handleNextStep = async () => {
//     if (currentStep < TOTAL_PROMPTS) {
//       if (currentStep > 0) {
//         await logSectionEdit(currentStep - 1);
//       }
//       await generateSection(currentStep);
//       if (currentStep === TOTAL_PROMPTS - 1) {
//         setLastStepApproved(true);
//       }
//       setCurrentStep(currentStep + 1);
//     }
//   };

//   const handleRegenerate = async (index: number) => {
//     setCurrentStep(index);
//     const newOutputs = [...outputs];
//     newOutputs[index] = "";
//     setOutputs(newOutputs);
//     await generateSection(index);
//     setCurrentStep(index + 1);
//   };

//   // Modify the getAllContent function
//   const getAllContent = () => {
//     return outputs
//       .filter((output) => output)
//       .map((output) => output.trim()) // Trim any extra whitespace
//       .join("\n\n"); // Add a markdown-style separator between sections
//   };

//   if (!currentTranscription) {
//     return <div>Please select a transcription first</div>;
//   }

//   return (
//     <div className="mx-auto max-w-3xl p-4">
//       {/* Add Start Generating button when no outputs exist */}
//       {outputs.every((output) => !output) && (
//         <button
//           onClick={handleNextStep}
//           disabled={isLoading}
//           className="mb-4 w-full rounded-lg bg-blue-500 px-4 py-3 text-lg font-medium text-white transition-colors hover:bg-blue-600 disabled:bg-blue-300"
//         >
//           {isLoading ? "Generating..." : "Start Generating CRISSA"}
//         </button>
//       )}

//       {Array(TOTAL_PROMPTS)
//         .fill(null)
//         .map((_, index) =>
//           outputs[index] || index === currentStep - 1 ? (
//             <div key={index} className="relative rounded-lg p-4 pb-12">
//               <SimpleEditor
//                 initialContent={outputs[index]}
//                 onContentChange={(content) =>
//                   handleContentChangeInEditor(index, content)
//                 }
//                 isEditing={editingIndex === index}
//                 showCopyButton={false}
//                 onCitationClick={(idx) => console.log("Citation clicked:", idx)}
//               />

//               {index === currentStep - 1 && (
//                 <div className="absolute bottom-3 right-4">
//                   <div className="flex items-center gap-1 rounded-md border border-gray-200 bg-white px-1 py-0.5 shadow-sm">
//                     <button
//                       onClick={() =>
//                         setEditingIndex(editingIndex === index ? null : index)
//                       }
//                       className={`rounded-md px-3 py-1 text-sm font-medium transition-colors hover:bg-gray-50 ${
//                         editingIndex === index
//                           ? "bg-blue-50 text-blue-500"
//                           : "text-gray-500"
//                       }`}
//                       title="Edit"
//                     >
//                       Edit
//                     </button>
//                     <div className="h-4 w-px bg-gray-200" />
//                     <button
//                       className="rounded-md px-3 py-1 text-sm font-medium text-gray-500 transition-colors hover:bg-gray-50"
//                       title="Regenerate"
//                       onClick={() => handleRegenerate(index)}
//                     >
//                       Regenerate
//                     </button>
//                     <div className="h-4 w-px bg-gray-200" />
//                     {index === TOTAL_PROMPTS - 1 && lastStepApproved ? (
//                       <button
//                         disabled
//                         className="cursor-not-allowed rounded-md px-3 py-1 text-sm font-medium text-gray-300"
//                         title="Approved"
//                       >
//                         Approved ✓
//                       </button>
//                     ) : (
//                       <button
//                         onClick={() => {
//                           if (index === TOTAL_PROMPTS - 1) {
//                             setLastStepApproved(true);
//                           }
//                           handleNextStep();
//                         }}
//                         disabled={isLoading}
//                         className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
//                           isLoading
//                             ? "text-blue-300"
//                             : "text-blue-500 hover:bg-blue-50"
//                         }`}
//                         title="Approve"
//                       >
//                         {isLoading ? "..." : "Approve"}
//                       </button>
//                     )}
//                   </div>
//                 </div>
//               )}
//             </div>
//           ) : null,
//         )}

//       {/* Show copy button only when last step is approved */}
//       {lastStepApproved && (
//         <div className="mt-4 flex justify-end">
//           <CopyCrissaButton
//             textToCopy={removeCitations(getAllContent())}
//             posthogEventName="crissa_content_copied"
//           />
//         </div>
//       )}
//     </div>
//   );
// }
