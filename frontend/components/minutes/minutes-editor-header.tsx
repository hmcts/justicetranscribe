/* eslint-disable no-nested-ternary */
import { Edit, Loader2, Save, Wand2, FileText, Sparkles } from "lucide-react";
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select";
import { TemplateMetadata } from "@/src/api/generated";
import DownloadStyleCopyButton from "@/components/ui/copy-button";
import { MinuteVersion } from "@/lib/database";
import { Textarea } from "@/components/ui/textarea";
import RatingDialog from "./rating-dialog";

interface MinutesEditorHeaderProps {
  selectedTemplate: TemplateMetadata | null;
  onTemplateChange: (name: string) => void;
  isGenerating: boolean;
  templatesLoading: boolean;
  templatesError: any;
  templates: TemplateMetadata[];
  currentVersion: MinuteVersion | null | undefined;
  isEditing: boolean;
  onEditClick: () => void;
  onSaveEdit: () => void;
  generateAIMinutes: (template: TemplateMetadata) => void;
  onCopy: () => void;
  rating: number | null;
  ratingComment: string | null;
  onRatingSubmit: (rating: number, comment: string | null) => void;
  isRatingDialogOpen: boolean;
  setIsRatingDialogOpen: (open: boolean) => void;
  onAIEdit: (instructions: string) => void;
}

export default function MinutesEditorHeader({
  selectedTemplate,
  onTemplateChange,
  isGenerating,
  templatesLoading,
  templatesError,
  templates,
  currentVersion,
  isEditing,
  onEditClick,
  onSaveEdit,
  generateAIMinutes,
  onCopy,
  rating,
  ratingComment,
  onRatingSubmit,
  isRatingDialogOpen,
  setIsRatingDialogOpen,
  onAIEdit,
}: MinutesEditorHeaderProps) {
  const [isAIEditInlineOpen, setIsAIEditInlineOpen] = useState(false);
  const [aiEditInstructions, setAIEditInstructions] = useState("");

  const handleSubmitAIEdit = () => {
    if (aiEditInstructions.trim()) {
      onAIEdit(aiEditInstructions);
      setIsAIEditInlineOpen(false);
      setAIEditInstructions("");
    }
  };

  const handleQuickSuggestionClick = (prompt: string) => {
    setAIEditInstructions(prompt);
  };

  const quickSuggestions = [
    {
      label: "Make more concise",
      prompt:
        "Update the summary to make it more concise and focused. Remove any repetition.",
    },
    {
      label: "Rewrite as an email",
      prompt: "Rewrite as email",
    },
    {
      label: "Add names and age",
      prompt:
        "Update the summary to include the names and ages of any people mentioned during the meeting especially children or dependents",
    },
    {
      label: "Change names",
      prompt:
        "Change the name of 'A' to 'B' and their gender is male or female",
    },
  ];

  return (
    <div className="space-y-4">
      <div className="relative flex flex-col space-y-4 md:flex-row md:items-center md:space-x-4 md:space-y-0">
        <div className="relative z-10 md:w-[200px]">
          <Select
            value={selectedTemplate?.name}
            onValueChange={onTemplateChange}
            disabled={isGenerating || templatesLoading}
          >
            <SelectTrigger className="h-12 w-full justify-between px-4 text-left font-normal">
              <div className="flex items-center gap-2">
                <FileText className="size-4" />
                {templatesLoading ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="size-4 animate-spin" />
                    Loading...
                  </span>
                ) : selectedTemplate ? (
                  <span className="truncate">{selectedTemplate.name}</span>
                ) : (
                  <span>Select a template</span>
                )}
              </div>
            </SelectTrigger>
            <SelectContent className="max-h-[300px]">
              {templatesLoading ? (
                <div className="flex items-center justify-center p-4">
                  <Loader2 className="mr-2 size-4 animate-spin" />
                  <span>Loading templates...</span>
                </div>
              ) : templatesError ? (
                <div className="p-4 text-red-500">Error loading templates</div>
              ) : templates.length === 0 ? (
                <div className="p-4 text-gray-500">No templates available</div>
              ) : (
                templates.map((template) => (
                  <SelectItem
                    key={template.name}
                    value={template.name}
                    className="py-2"
                  >
                    <div className="space-y-1">
                      <p className="font-medium">{template.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {template.description}
                      </p>
                    </div>
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
        </div>

        <div className="relative z-10 grid w-full grid-cols-1 gap-2 sm:grid-cols-2 md:flex md:w-auto md:gap-4">
          {isGenerating ? (
            <Button className="flex h-12 w-full items-center justify-center gap-2 rounded-md bg-red-100 px-4 text-red-700 shadow-sm hover:bg-red-200">
              <Loader2 className="size-4 animate-spin" />
              <span>Generating...</span>
            </Button>
          ) : !currentVersion && selectedTemplate ? (
            <Button
              onClick={() => generateAIMinutes(selectedTemplate)}
              className="flex h-12 w-full items-center justify-center gap-2 rounded-md bg-green-600 px-4 text-white shadow-sm hover:bg-green-700"
            >
              <Wand2 className="mr-2 size-4" />
              <span>Generate Summary</span>
            </Button>
          ) : (
            <>
              {isEditing ? (
                <Button
                  onClick={onSaveEdit}
                  className="flex h-12 w-full items-center justify-center rounded-md bg-blue-600 px-4 text-white shadow-sm hover:bg-blue-700"
                >
                  <Save className="size-5 md:mr-2" />
                  <span className="hidden md:inline">Save</span>
                  <span className="md:hidden">💾</span>
                </Button>
              ) : (
                <Button
                  onClick={onEditClick}
                  className="flex h-12 w-full items-center justify-center rounded-md bg-blue-600 px-4 text-white shadow-sm hover:bg-blue-700"
                  disabled={isGenerating || !currentVersion}
                >
                  <Edit className="size-5 md:mr-2" />
                  <span className="hidden md:inline">Edit</span>
                </Button>
              )}

              {currentVersion && (
                <>
                  <Button
                    className="flex h-12 w-full items-center justify-center gap-2 rounded-md bg-rose-600 px-4 text-white shadow-sm hover:bg-rose-700"
                    disabled={isGenerating}
                    onClick={() => {
                      if (isEditing) {
                        onSaveEdit();
                      }
                      setIsAIEditInlineOpen(!isAIEditInlineOpen);
                    }}
                  >
                    <Sparkles className="mr-2 size-4" />
                    <span className="hidden md:inline">Update Summary</span>
                  </Button>

                  <DownloadStyleCopyButton
                    textToCopy={currentVersion.html_content}
                    posthogEventName="minutes_copied"
                    onCopy={onCopy}
                  />
                </>
              )}
            </>
          )}
        </div>

        <div className="static z-0 mt-2 flex w-full justify-end md:absolute md:right-4 md:top-1/2 md:mt-0 md:-translate-y-1/2">
          <RatingDialog
            rating={rating}
            comment={ratingComment}
            onSubmit={onRatingSubmit}
            isOpen={isRatingDialogOpen}
            onOpenChange={setIsRatingDialogOpen}
          />
        </div>
      </div>

      {isAIEditInlineOpen && currentVersion && (
        <div className="rounded-lg border bg-white p-6 shadow-sm">
          <div className="space-y-4">
            <div className="text-center">
              <h3 className="text-lg font-semibold text-gray-900">
                What would you like to change?
              </h3>
              <p className="text-sm text-gray-600">
                Tell AI exactly what to change in your summary
              </p>
            </div>

            <div className="space-y-4">
              <Textarea
                placeholder="Describe the changes you want to make"
                value={aiEditInstructions}
                onChange={(e) => setAIEditInstructions(e.target.value)}
                className="min-h-[80px] resize-none"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                    handleSubmitAIEdit();
                  }
                }}
              />

              <div className="space-y-3">
                <p className="text-sm font-medium text-gray-700">
                  Quick suggestions:
                </p>
                <div className="flex flex-wrap gap-2">
                  {quickSuggestions.map((suggestion) => (
                    <Button
                      key={suggestion.label}
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        handleQuickSuggestionClick(suggestion.prompt)
                      }
                      className="text-xs"
                    >
                      + {suggestion.label}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <Button
                  variant="outline"
                  onClick={() => {
                    setIsAIEditInlineOpen(false);
                    setAIEditInstructions("");
                  }}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSubmitAIEdit}
                  disabled={!aiEditInstructions.trim()}
                  className="bg-blue-600 text-white hover:bg-blue-700"
                >
                  <Sparkles className="mr-2 size-4" />
                  Update
                </Button>
              </div>

              <div className="text-center">
                <p className="text-xs text-gray-500">
                  Press{" "}
                  <kbd className="rounded bg-gray-100 px-1 py-0.5 text-xs">
                    ⌘
                  </kbd>{" "}
                  +{" "}
                  <kbd className="rounded bg-gray-100 px-1 py-0.5 text-xs">
                    Enter
                  </kbd>{" "}
                  to update
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
