/* eslint-disable no-plusplus */
/* eslint-disable no-promise-executor-return */
/* eslint-disable no-await-in-loop */
/* eslint-disable no-nested-ternary */
import { Wand2, FileText } from "lucide-react";
import posthog from "posthog-js";
import React, { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { TemplateMetadata } from "@/src/api/generated";
import useTemplates from "@/hooks/use-templates";
import { apiClient } from "@/lib/api-client";
import {
  findExistingMinuteVersionForTemplate,
  pollMinuteVersion,
  submitLangfuseScore,
} from "@/lib/utils";
import { useTranscripts } from "@/providers/transcripts";
import {
  getMinuteVersions,
  MinuteVersion,
  saveMinuteVersion,
} from "@/lib/database";
import SimpleEditor from "../editor/tiptap-editor";
import MinutesEditorHeader from "./minutes-editor-header";

interface MinutesEditorProps {
  onCitationClick: (index: number) => void;
}

function MinutesEditor({ onCitationClick }: MinutesEditorProps) {
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [currentVersion, setCurrentVersion] = useState<
    MinuteVersion | undefined
  >();
  const [selectedTemplate, setSelectedTemplate] =
    useState<TemplateMetadata | null>(null);
  const [isRatingDialogOpen, setIsRatingDialogOpen] = useState(false);

  const { currentTranscription } = useTranscripts();
  const {
    templates,
    isLoading: templatesLoading,
    error: templatesError,
  } = useTemplates();

  const handleSaveEdit = async () => {
    if (!currentVersion?.id || !currentTranscription?.id) return;

    setIsEditing(false);

    try {
      const savedVersion = await saveMinuteVersion(currentTranscription.id, {
        ...currentVersion,
      });

      setCurrentVersion(savedVersion);

      posthog.capture("minutes_manual_edit_saved", {
        version_id: currentVersion?.id,
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? `Failed to save changes: ${error.message}`
          : "Failed to save changes. Please try again.";
      alert(errorMessage);
      throw error;
    }
  };

  const generateAIMinutes = useCallback(
    async (template: TemplateMetadata) => {
      if (!currentTranscription?.id) {
        throw new Error("No active transcription");
      }
      setIsGenerating(true);
      try {
        posthog.capture("generate_ai_minutes_started", {
          style: template.name,
        });

        const result = await apiClient.generateOrEditMinutes({
          transcription_id: currentTranscription.id,
          template,
          action_type: "generate",
        });
        if (result.error) {
          throw new Error("Failed to initiate AI minutes generation");
        }
        // eslint-disable-next-line @typescript-eslint/naming-convention
        const { minute_version_id } = result.data!;

        const minuteVersion = await pollMinuteVersion(
          currentTranscription.id,
          minute_version_id
        );

        setCurrentVersion(minuteVersion);
      } catch (error) {
        const errorMessage =
          error instanceof Error
            ? error.message
            : "Failed to generate AI minutes. Please try again.";
        alert(errorMessage);
        throw error;
      } finally {
        setIsGenerating(false);
      }
    },
    [currentTranscription?.id, setIsGenerating, setCurrentVersion]
  );

  const handleAIEdit = useCallback(
    async (editInstructions: string) => {
      if (
        !currentVersion?.id ||
        !currentTranscription?.id ||
        !selectedTemplate
      ) {
        return;
      }
      handleSaveEdit();

      setIsGenerating(true);
      try {
        posthog.capture("ai_edit_started", {
          style: selectedTemplate.name,
        });

        const result = await apiClient.generateOrEditMinutes({
          transcription_id: currentTranscription.id,
          template: selectedTemplate,
          current_minute_version_id: currentVersion.id,
          edit_instructions: editInstructions,
          action_type: "edit",
        });

        if (result.error) {
          throw new Error("Failed to initiate AI edit");
        }

        // eslint-disable-next-line @typescript-eslint/naming-convention
        const { minute_version_id } = result.data!;

        const minuteVersion = await pollMinuteVersion(
          currentTranscription.id,
          minute_version_id
        );

        setCurrentVersion(minuteVersion);
      } catch (error) {
        const errorMessage =
          error instanceof Error
            ? error.message
            : "Failed to generate AI edit. Please try again.";
        alert(errorMessage);
        throw error;
      } finally {
        setIsGenerating(false);
      }
    },
    [currentTranscription?.id, currentVersion, selectedTemplate]
  );

  const handleTemplateChange = useCallback(
    async (name: string) => {
      const template = templates.find((t) => t.name === name);
      if (!template || !currentTranscription?.id) return;

      setSelectedTemplate(template);
      const minuteVersions = await getMinuteVersions(currentTranscription.id);
      const existingVersion = findExistingMinuteVersionForTemplate(
        minuteVersions,
        template.name
      );
      if (
        existingVersion &&
        existingVersion.id &&
        !existingVersion.is_generating
      ) {
        setCurrentVersion(existingVersion);
      } else if (
        existingVersion &&
        existingVersion.id &&
        currentTranscription?.id
      ) {
        setIsGenerating(true);

        const minuteVersion = await pollMinuteVersion(
          currentTranscription.id,
          existingVersion.id
        );
        setCurrentVersion(minuteVersion);
        setIsGenerating(false);
      } else {
        generateAIMinutes(template);
      }
    },
    [templates, currentTranscription?.id, generateAIMinutes]
  );

  useEffect(() => {
    const loadMinuteVersions = async () => {
      if (!currentTranscription?.id) {
        setCurrentVersion(undefined);
        if (templates.length > 0) {
          handleTemplateChange(templates[0].name);
        }
        return;
      }

      try {
        const versions = await getMinuteVersions(currentTranscription.id);
        if (versions.length > 0) {
          const minuteVersion =
            versions
              .filter((version) => !version.is_generating)
              .sort((a, b) => {
                const dateA = new Date(a.created_datetime || "").getTime();
                const dateB = new Date(b.created_datetime || "").getTime();
                return dateB - dateA; // Sort in descending order (newest first)
              })[0] || versions[versions.length - 1];
          handleTemplateChange(minuteVersion.template.name);
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error
            ? `Failed to fetch minute versions: ${error.message}`
            : "Failed to fetch minute versions. Please try again.";
        alert(errorMessage);
      }
    };

    loadMinuteVersions();
  }, [currentTranscription?.id, handleTemplateChange, templates]);

  const handleRatingSubmit = async (rating: number, comment: string | null) => {
    if (!currentVersion?.id || !currentTranscription?.id) return;

    try {
      const savedVersion = await saveMinuteVersion(currentTranscription.id, {
        ...currentVersion,
        star_rating: rating,
        star_rating_comment: comment,
      });
      setCurrentVersion(savedVersion);

      if (currentVersion.trace_id) {
        await submitLangfuseScore({
          traceId: currentVersion.trace_id,
          name: "user-feedback",
          value: rating,
          comment: comment ?? undefined,
        });
      }

      posthog.capture("minutes_rating_submitted", {
        version_id: currentVersion?.id,
        rating,
        comment,
      });
    } catch (error) {
      alert("Failed to save rating. Please try again.");
      throw error;
    }
  };

  const handleCopy = () => {
    if (!currentVersion?.star_rating) {
      setTimeout(() => {
        setIsRatingDialogOpen(true);
      }, 1000); // 1 second delay
    }
  };

  return (
    <Card className="relative mt-6 bg-white shadow-lg">
      <CardHeader className="bg-gray-50 p-4">
        <MinutesEditorHeader
          selectedTemplate={selectedTemplate}
          onTemplateChange={handleTemplateChange}
          isGenerating={isGenerating}
          templatesLoading={templatesLoading}
          templatesError={templatesError}
          templates={templates}
          currentVersion={currentVersion}
          isEditing={isEditing}
          onEditClick={() => setIsEditing(true)}
          onSaveEdit={handleSaveEdit}
          generateAIMinutes={generateAIMinutes}
          onAIEdit={handleAIEdit}
          onCopy={handleCopy}
          rating={currentVersion?.star_rating ?? null}
          ratingComment={currentVersion?.star_rating_comment ?? ""}
          onRatingSubmit={handleRatingSubmit}
          isRatingDialogOpen={isRatingDialogOpen}
          setIsRatingDialogOpen={setIsRatingDialogOpen}
        />
      </CardHeader>

      <CardContent className="p-6">
        {!currentVersion && !isGenerating && (
          <div className="flex flex-col items-center justify-center space-y-6 rounded-lg border border-dashed border-gray-300 p-12 text-center text-gray-500">
            <FileText className="size-16" />
            <div>
              <h3 className="text-xl font-medium">No summary generated yet</h3>
              <p className="mt-2 text-gray-500">
                Select a template and generate summary to get started
              </p>

              {selectedTemplate && (
                <Button
                  onClick={() => generateAIMinutes(selectedTemplate)}
                  className="mt-4 flex items-center justify-center gap-2 bg-green-600 px-6 py-2 text-white hover:bg-green-700"
                >
                  <Wand2 className="size-5" />
                  <span>Generate with {selectedTemplate.name}</span>
                </Button>
              )}
            </div>
          </div>
        )}
        {currentVersion && (
          <div className="w-full overflow-visible ph-mask">
            <SimpleEditor
              initialContent={currentVersion?.html_content ?? ""}
              isEditing={isEditing}
              onContentChange={(newContent) => {
                setCurrentVersion({
                  ...currentVersion,
                  html_content: newContent,
                });
              }}
              onCitationClick={onCitationClick}
              onEditorClick={() => {
                if (!isEditing && !isGenerating && currentVersion) {
                  setIsEditing(true);
                }
              }}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default MinutesEditor;
