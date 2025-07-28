// // frontend/components/chat/ai-chat.tsx

// "use client";

// import React, { useEffect, useRef } from "react";
// import {
//   AssistantModalPrimitive,
//   AssistantRuntimeProvider,
//   Thread,
//   useEdgeRuntime,
//   useThread,
// } from "@assistant-ui/react";
// import { useTranscripts } from "@/providers/transcripts";
// import posthog from "posthog-js";
// import { makeMarkdownText } from "@assistant-ui/react-markdown";
// import { DialogueEntry } from "@/src/api/generated";

// const MarkdownText = makeMarkdownText();

// const SYSTEM_PROMPT = `You are an AI assistant inside the app Minute built by the UK government to help public servants transcribe and summarise meetings.
// Here are some rules:
// - You must always respond in British English.
// - You must not hallucinate any details about Minute's features if the user asks about them. The most you should say is that Minute is a tool to help transcribe and summarise meetings.`;

// function ChatModal() {
//   const threadState = useThread();
//   const lastMessageCount = useRef(threadState.messages.length);
//   const toggleButton = useRef<HTMLButtonElement>(null);

//   useEffect(() => {
//     if (threadState.messages.length === 1) {
//       lastMessageCount.current = 1;
//     }

//     const currentCount = threadState.messages.length;
//     if (currentCount - lastMessageCount.current >= 2) {
//       posthog.capture("chat_turn_completed", {
//         messages_count: currentCount,
//       });
//       lastMessageCount.current = currentCount;
//     }

//     // close the modal if the user presses the escape key
//     document.body.addEventListener("keydown", (evt) => {
//       if (
//         evt.key === "Escape" &&
//         toggleButton.current?.dataset.state === "open"
//       ) {
//         toggleButton.current.click();
//         toggleButton.current.focus();
//       }
//     });
//   }, [threadState.messages.length]);

//   return (
//     <div className="fixed bottom-6 right-6 z-50 mb-10">
//       <AssistantModalPrimitive.Root>
//         <AssistantModalPrimitive.Trigger
//           ref={toggleButton}
//           className="rounded-full bg-blue-600 text-white shadow-lg transition-all duration-200 hover:bg-blue-700 hover:shadow-xl focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
//         >
//           <div className="flex items-center gap-2 px-4 py-2">
//             <svg
//               xmlns="http://www.w3.org/2000/svg"
//               viewBox="0 0 24 24"
//               fill="currentColor"
//               className="size-5"
//             >
//               <path d="M4.913 2.658c2.075-.27 4.19-.408 6.337-.408 2.147 0 4.262.139 6.337.408 1.922.25 3.291 1.861 3.405 3.727a4.403 4.403 0 00-1.032-.211 50.89 50.89 0 00-8.42 0c-2.358.196-4.04 2.19-4.04 4.434v4.286a4.47 4.47 0 002.433 3.984L7.28 21.53A.75.75 0 016 21v-4.03a48.527 48.527 0 01-1.087-.128C2.905 16.58 1.5 14.833 1.5 12.862V6.638c0-1.97 1.405-3.718 3.413-3.979z" />
//               <path d="M15.75 7.5c-1.376 0-2.739.057-4.086.169C10.124 7.797 9 9.103 9 10.609v4.285c0 1.507 1.128 2.814 2.67 2.94 1.243.102 2.5.157 3.768.165l2.782 2.781a.75.75 0 001.28-.53v-2.39l.33-.026c1.542-.125 2.67-1.433 2.67-2.94v-4.286c0-1.505-1.125-2.811-2.664-2.94A49.392 49.392 0 0015.75 7.5z" />
//             </svg>
//             AI Chat
//           </div>
//         </AssistantModalPrimitive.Trigger>
//         <AssistantModalPrimitive.Content
//           className="z-50 mb-2 h-[500px] w-[400px] rounded border border-gray-200 bg-white shadow-2xl"
//           dissmissOnInteractOutside
//         >
//           <Thread assistantMessage={{ components: { Text: MarkdownText } }} />
//         </AssistantModalPrimitive.Content>
//       </AssistantModalPrimitive.Root>
//     </div>
//   );
// }

// export default function AIChat() {
//   const { currentTranscription } = useTranscripts();

//   const runtime = useEdgeRuntime({
//     api: "/api/chat",
//     initialMessages: [
//       {
//         role: "system",
//         content: [
//           {
//             type: "text",
//             text: SYSTEM_PROMPT,
//           },
//         ] as [{ type: "text"; text: string }],
//       },
//     ],
//   });

//   useEffect(() => {
//     const systemMessage = {
//       role: "system" as const,
//       content: [
//         {
//           type: "text" as const,
//           text: currentTranscription
//             ? `${SYSTEM_PROMPT}\n\nBelow is the transcript of a meeting that you should use to answer questions:\n\n${currentTranscription.dialogue_entries
//                 .map(
//                   (entry: DialogueEntry) => `${entry.speaker}: ${entry.text}`,
//                 )
//                 .join("\n")}`
//             : `${SYSTEM_PROMPT} No meeting transcript is currently loaded. If the user asks questions about the meeting, ask them to either record a new meeting or load an existing one from the sidebar.`,
//         },
//       ] as [{ type: "text"; text: string }],
//     };

//     runtime.reset({
//       initialMessages: [systemMessage],
//     });
//   }, [currentTranscription, currentTranscription?.id, runtime]);

//   return (
//     <AssistantRuntimeProvider runtime={runtime}>
//       <ChatModal />
//     </AssistantRuntimeProvider>
//   );
// }
