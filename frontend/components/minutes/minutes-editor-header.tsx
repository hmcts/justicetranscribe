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
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
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
  const [isSpellingFixPopoverOpen, setIsSpellingFixPopoverOpen] =
    useState(false);
  const [spellingInstructions, setSpellingInstructions] = useState("");

  // const latestUpdatedTime =
  //   transcriptionJobs.length > 0
  //     ? new Date(
  //         Math.max(
  //           ...transcriptionJobs
  //             .map((job) =>
  //               job.updated_datetime
  //                 ? new Date(job.updated_datetime).getTime()
  //                 : 0,
  //             )
  //             .filter((time) => !Number.isNaN(time)),
  //         ),
  //       )
  //     : null;

  const handleSubmitSpellingFix = () => {
    if (spellingInstructions.trim()) {
      onAIEdit(spellingInstructions);
      setIsSpellingFixPopoverOpen(false);
      setSpellingInstructions("");
    }
  };

  return (
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

      {/* Action buttons */}
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
                <Popover
                  open={isSpellingFixPopoverOpen}
                  onOpenChange={(open) => {
                    setIsSpellingFixPopoverOpen(open);
                    if (!open) setSpellingInstructions("");
                  }}
                >
                  <PopoverTrigger asChild>
                    <Button
                      className="flex h-12 w-full items-center justify-center gap-2 rounded-md bg-rose-600 px-4 text-white shadow-sm hover:bg-rose-700"
                      disabled={isGenerating}
                      onClick={() => {
                        if (isEditing) {
                          onSaveEdit();
                        }
                      }}
                    >
                      <Sparkles className="mr-2 size-4" />
                      <span className="hidden md:inline">Update Summary</span>
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent
                    className="w-80 p-0"
                    align="end"
                    side="bottom"
                    sideOffset={8}
                  >
                    <div className="space-y-3 p-3">
                      <div className="space-y-1">
                        <h4 className="text-sm font-medium">
                          Tell AI exactly what to improve
                        </h4>
                        <p className="text-xs text-muted-foreground">
                          e.g, Fix spelling and names, make more concise
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Textarea
                          placeholder="e.g., Change 'John Smith' to 'Jon Smyth'..."
                          value={spellingInstructions}
                          onChange={(e) =>
                            setSpellingInstructions(e.target.value)
                          }
                          className="min-h-[60px] resize-none text-sm"
                          onKeyDown={(e) => {
                            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                              handleSubmitSpellingFix();
                            }
                          }}
                        />
                        <div className="flex gap-2">
                          <Button
                            onClick={handleSubmitSpellingFix}
                            disabled={!spellingInstructions.trim()}
                            className="flex-1 bg-rose-600 hover:bg-rose-700"
                            size="sm"
                          >
                            <Sparkles className="mr-1 size-3" />
                            Fix
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setIsSpellingFixPopoverOpen(false);
                              setSpellingInstructions("");
                            }}
                            className="px-3"
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    </div>
                  </PopoverContent>
                </Popover>

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

      <div
        className="
          static z-0 mt-2 flex
          w-full justify-end md:absolute md:right-4 md:top-1/2 md:mt-0
          md:-translate-y-1/2
        "
      >
        <RatingDialog
          rating={rating}
          comment={ratingComment}
          onSubmit={onRatingSubmit}
          isOpen={isRatingDialogOpen}
          onOpenChange={setIsRatingDialogOpen}
        />
      </div>
    </div>
  );
}
