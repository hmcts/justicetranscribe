"use client";

import { Extension } from "@tiptap/core";
import Document from "@tiptap/extension-document";
import HardBreak from "@tiptap/extension-hard-break";
import Paragraph from "@tiptap/extension-paragraph";
import Text from "@tiptap/extension-text";
import type { Editor } from "@tiptap/react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import classNames from "classnames";
import { Plugin, PluginKey } from "prosemirror-state";
import { Decoration, DecorationSet } from "prosemirror-view";
import React, { useCallback, useEffect, useState } from "react";
import CharacterCount from "@tiptap/extension-character-count";

import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useTranscripts } from "@/providers/transcripts";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "@/components/ui/tooltip";
import { concatenateDialogueEntriesInTranscriptionJobs } from "@/lib/utils";
import {
  Bold as BoldIcon,
  Italic as ItalicIcon,
  List as UnorderedListIcon,
  ListOrdered as OrderedListIcon,
  RotateLeft,
  RotateRight,
} from "./Icons";
import CitationPopoverContent from "./citation-popover";

function SimpleEditor({
  initialContent,
  onContentChange,
  isEditing,
  onCitationClick,
  onEditorClick,
}: {
  initialContent: string;
  onContentChange: (newContent: string) => void;
  isEditing: boolean;
  onCitationClick: (index: number) => void;
  onEditorClick?: () => void;
}) {
  const [citationPopover, setCitationPopover] = useState<{
    index: number;
    x: number;
    y: number;
  } | null>(null);
  const { currentTranscription, transcriptionJobs } = useTranscripts();

  const [isPopoverOpen, setIsPopoverOpen] = useState(false);

  const CHARACTER_LIMIT = 4000;

  const handleCitationClick = (index: number, rect: DOMRect) => {
    setCitationPopover({
      index,
      x: rect.left,
      y: rect.bottom,
    });
    setIsPopoverOpen(true);
    onCitationClick(index);
  };

  const CitationExtension = Extension.create({
    name: "citation",
    addProseMirrorPlugins() {
      return [
        new Plugin({
          key: new PluginKey("citation"),
          props: {
            decorations(state) {
              const decorations: Decoration[] = [];
              const citationRegex = /\[(\d+)\]/g;

              state.doc.descendants((node, pos) => {
                if (node.isText) {
                  let match;
                  // eslint-disable-next-line no-cond-assign
                  while ((match = citationRegex.exec(node.text!)) !== null) {
                    const from = pos + match.index;
                    const to = from + match[0].length;
                    decorations.push(
                      Decoration.inline(from, to, {
                        class: "citation-link",
                        style:
                          "color: blue; cursor: pointer; text-decoration: underline;",
                      }),
                    );
                  }
                }
              });

              return DecorationSet.create(state.doc, decorations);
            },
            handleDOMEvents: {
              click: (view, event) => {
                const pos = view.posAtDOM(event.target as Node, 0);
                if (pos === null) return false;

                const domNode = event.target as HTMLElement;

                if (domNode.classList.contains("citation-link")) {
                  const match = domNode.textContent?.match(/\[(\d+)\]/);
                  if (match) {
                    const index = parseInt(match[1], 10);
                    const rect = domNode.getBoundingClientRect();
                    handleCitationClick(index, rect);
                    return true;
                  }
                }
                return false;
              },
            },
          },
        }),
      ];
    },
  });

  const editorObject = useEditor({
    extensions: [
      StarterKit,
      Document,
      Paragraph,
      Text,
      CitationExtension,
      HardBreak,
      CharacterCount,
    ],
    editable: isEditing,
    onUpdate: ({ editor }) => {
      onContentChange(editor.getHTML());
    },
  }) as Editor;

  useEffect(() => {
    if (editorObject && initialContent !== editorObject.getHTML()) {
      editorObject.commands.setContent(initialContent);
    }
  }, [editorObject, initialContent]);

  const toggleBold = useCallback(() => {
    editorObject.chain().focus().toggleBold().run();
  }, [editorObject]);

  const toggleItalic = useCallback(() => {
    editorObject.chain().focus().toggleItalic().run();
  }, [editorObject]);

  const toggleBulletList = useCallback(() => {
    editorObject.chain().focus().toggleBulletList().run();
  }, [editorObject]);

  const toggleOrderedList = useCallback(() => {
    editorObject.chain().focus().toggleOrderedList().run();
  }, [editorObject]);

  const characterCount = editorObject?.storage.characterCount.characters() ?? 0;
  const isOverLimit = characterCount > CHARACTER_LIMIT;

  if (!editorObject) {
    return null;
  }

  return (
    <TooltipProvider delayDuration={200}>
      <div className="relative">
        <div className="relative rounded-md border border-gray-300">
          {isEditing && (
            <div className="flex flex-wrap items-center gap-2 border-b border-gray-200 bg-white p-2">
              {/* History Group */}
              <div className="flex items-center gap-1">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      className="rounded-md p-1.5 transition-colors hover:bg-gray-100 disabled:opacity-40"
                      onClick={() => editorObject.chain().focus().undo().run()}
                      disabled={!editorObject.can().undo()}
                      type="button"
                    >
                      <RotateLeft size={20} />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>Undo</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      className="rounded-md p-1.5 transition-colors hover:bg-gray-100 disabled:opacity-40"
                      onClick={() => editorObject.chain().focus().redo().run()}
                      disabled={!editorObject.can().redo()}
                      type="button"
                    >
                      <RotateRight size={20} />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>Redo</TooltipContent>
                </Tooltip>
              </div>

              <div className="h-4 w-px bg-gray-200" aria-hidden="true" />

              {/* Text Formatting Group */}
              <div className="flex items-center gap-1">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      className={classNames(
                        "rounded-md p-1.5 hover:bg-gray-100 transition-colors",
                        {
                          "bg-gray-100 text-primary":
                            editorObject.isActive("bold"),
                        },
                      )}
                      onClick={toggleBold}
                      type="button"
                    >
                      <BoldIcon size={20} />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>Bold</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      className={classNames(
                        "rounded-md p-1.5 hover:bg-gray-100 transition-colors",
                        {
                          "bg-gray-100 text-primary":
                            editorObject.isActive("italic"),
                        },
                      )}
                      onClick={toggleItalic}
                      type="button"
                    >
                      <ItalicIcon size={20} />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>Italic</TooltipContent>
                </Tooltip>
              </div>

              <div className="h-4 w-px bg-gray-200" aria-hidden="true" />

              {/* List Formatting Group */}
              <div className="flex items-center gap-1">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      className={classNames(
                        "rounded-md p-1.5 hover:bg-gray-100 transition-colors",
                        {
                          "bg-gray-100 text-primary":
                            editorObject.isActive("bulletList"),
                        },
                      )}
                      onClick={toggleBulletList}
                      type="button"
                    >
                      <UnorderedListIcon size={20} />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>Bullet List</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      className={classNames(
                        "rounded-md p-1.5 hover:bg-gray-100 transition-colors",
                        {
                          "bg-gray-100 text-primary":
                            editorObject.isActive("orderedList"),
                        },
                      )}
                      onClick={toggleOrderedList}
                      type="button"
                    >
                      <OrderedListIcon size={20} />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>Numbered List</TooltipContent>
                </Tooltip>
              </div>

              <div className="h-4 w-px bg-gray-200" aria-hidden="true" />

              {/* Heading */}
              <div className="flex items-center gap-1">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      className={classNames(
                        "rounded-md px-2.5 py-1.5 hover:bg-gray-100 transition-colors font-medium",
                        {
                          "bg-gray-100 text-primary": editorObject.isActive(
                            "heading",
                            { level: 3 },
                          ),
                        },
                      )}
                      onClick={() =>
                        editorObject
                          .chain()
                          .focus()
                          .toggleHeading({ level: 3 })
                          .run()
                      }
                      type="button"
                    >
                      Heading
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>Add Heading</TooltipContent>
                </Tooltip>
              </div>
            </div>
          )}

          <EditorContent
            editor={editorObject}
            className={classNames("editor-content")}
            onClick={(e) => {
              if (
                e.target === e.currentTarget ||
                e.target instanceof HTMLParagraphElement
              ) {
                onEditorClick?.();
              }
            }}
          />

          {citationPopover && (
            <Popover
              open={isPopoverOpen}
              onOpenChange={(open) => {
                setIsPopoverOpen(open);
                if (!open) setCitationPopover(null);
              }}
            >
              <PopoverTrigger asChild>
                <div
                  style={{
                    position: "fixed",
                    left: citationPopover.x,
                    top: citationPopover.y,
                    width: 1,
                    height: 1,
                  }}
                />
              </PopoverTrigger>
              <PopoverContent className="w-[600px]">
                {currentTranscription && (
                  <CitationPopoverContent
                    dialogueEntries={concatenateDialogueEntriesInTranscriptionJobs(
                      transcriptionJobs,
                    )}
                    selectedIndex={citationPopover.index}
                  />
                )}
              </PopoverContent>
            </Popover>
          )}
        </div>
        <div className="mt-2 flex items-center gap-1 text-sm font-medium transition-colors">
          <span className={isOverLimit ? "text-red-500" : "text-gray-500"}>
            {characterCount}
          </span>
          <span className={isOverLimit ? "text-red-500" : "text-gray-500"}>
            /
          </span>
          <span className={isOverLimit ? "text-red-500" : "text-gray-500"}>
            {CHARACTER_LIMIT}
          </span>
          <span
            className={classNames(
              "ml-0.5",
              isOverLimit ? "text-red-500" : "text-gray-500",
            )}
          >
            characters
          </span>
        </div>
      </div>
    </TooltipProvider>
  );
}

SimpleEditor.defaultProps = {
  onEditorClick: undefined,
};

export default SimpleEditor;
