/* eslint-disable react/button-has-type */
/* eslint-disable jsx-a11y/no-static-element-interactions */
/* eslint-disable jsx-a11y/click-events-have-key-events */

"use client";

import React from "react";
import { Clock, Plus, Pencil, Trash2 } from "lucide-react";
import { format, isToday, isYesterday, formatDistanceToNow } from "date-fns";
import { Button } from "@/components/ui/button";
import { useTranscripts } from "@/providers/transcripts";
import posthog from "posthog-js";

function MeetingsList({
  showAllMeetings,
  setShowAllMeetings,
  handleNewMeeting,
  isLoading,
  meetings,
}: {
  showAllMeetings: boolean;
  setShowAllMeetings: (show: boolean) => void;
  handleNewMeeting: () => void;
  isLoading: boolean;
  meetings: any[];
}) {
  const { loadTranscription, deleteTranscription, renameTranscription } =
    useTranscripts();

  const [showDeleteModal, setShowDeleteModal] = React.useState<string | null>(
    null,
  );
  const [showRenameModal, setShowRenameModal] = React.useState<string | null>(
    null,
  );
  const [renameTitle, setRenameTitle] = React.useState("");

  const sortedMeetings = [...meetings]
    .filter((transcript) => transcript.is_showable_in_ui)
    .sort(
      (a, b) =>
        new Date(b.created_datetime).getTime() -
        new Date(a.created_datetime).getTime(),
    );

  // Show only 5 meetings if not showing all
  const displayedMeetings = showAllMeetings
    ? sortedMeetings
    : sortedMeetings.slice(0, 5);

  const handleMeetingClick = (meetingId: string) => {
    posthog.capture("opened_existing_transcript", {
      transcriptId: meetingId,
    });
    loadTranscription(meetingId);
  };

  const handleDelete = async (id: string) => {
    try {
      posthog.capture("deleted_transcript", {
        transcriptId: id,
      });
      await deleteTranscription(id);
      setShowDeleteModal(null);
    } catch (error) {
      console.error("Error deleting transcript:", error);
    }
  };

  const handleRename = async (id: string) => {
    try {
      posthog.capture("renamed_transcript", {
        transcriptId: id,
      });
      await renameTranscription(id, renameTitle);
      setShowRenameModal(null);
    } catch (error) {
      console.error("Error renaming transcript:", error);
    }
  };

  // Function to format date in a more readable way
  const formatReadableDate = (date: Date | string) => {
    const meetingDate = new Date(date);

    if (isToday(meetingDate)) {
      return `Today at ${format(meetingDate, "p")}`;
    }
    if (isYesterday(meetingDate)) {
      return `Yesterday at ${format(meetingDate, "p")}`;
    }
    if (meetingDate > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)) {
      return `${formatDistanceToNow(meetingDate, { addSuffix: true })} at ${format(meetingDate, "p")}`;
    }
    return format(meetingDate, "PP 'at' p");
  };

  return (
    <>
      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setShowDeleteModal(null)}
          />
          <div className="relative rounded-lg bg-white p-6 shadow-lg">
            <h3 className="mb-4 text-lg font-medium">Delete Meeting</h3>
            <p className="mb-6 text-sm text-gray-600">
              Are you sure you want to delete this meeting? This action cannot
              be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                className="rounded px-3 py-2 text-sm text-gray-600 hover:bg-gray-100"
                onClick={() => setShowDeleteModal(null)}
              >
                Cancel
              </button>
              <button
                className="rounded px-3 py-2 text-sm text-white hover:bg-red-700" style={{backgroundColor: '#B21010'}}
                onClick={() => handleDelete(showDeleteModal)}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rename Modal */}
      {showRenameModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setShowRenameModal(null)}
          />
          <div className="relative rounded-lg bg-white p-6 shadow-lg">
            <h3 className="mb-4 text-lg font-medium">Rename Meeting</h3>
            <input
              type="text"
              value={renameTitle}
              onChange={(e) => setRenameTitle(e.target.value)}
              className="mb-6 w-full rounded-md border border-gray-300 p-2"
              placeholder="Enter new title"
            />
            <div className="flex justify-end gap-3">
              <button
                className="rounded px-3 py-2 text-sm text-gray-600 hover:bg-gray-100"
                onClick={() => setShowRenameModal(null)}
              >
                Cancel
              </button>
              <button
                className="rounded bg-blue-500 px-3 py-2 text-sm text-white hover:bg-blue-600"
                onClick={() => handleRename(showRenameModal)}
              >
                Rename
              </button>
            </div>
          </div>
        </div>
      )}

      <div>
        <h2 className="mb-4 text-xl font-semibold">
          {showAllMeetings ? "All Meetings" : "Recent Meetings"}
        </h2>
        {isLoading && (
          <div className="py-8 text-center">Loading your meetings...</div>
        )}
        {!isLoading && displayedMeetings.length === 0 && (
          <div className="py-8 text-center text-gray-500">
            You don&apos;t have any meetings yet. Start by creating a new one!
          </div>
        )}
        {!isLoading && displayedMeetings.length > 0 && (
          <div className="space-y-3">
            {displayedMeetings.map((meeting) => (
              <div
                key={meeting.id}
                className="group rounded-lg border border-gray-200 p-4 transition-colors hover:bg-gray-50"
              >
                <div className="flex items-start justify-between">
                  <div
                    className="flex-1 cursor-pointer"
                    onClick={() => handleMeetingClick(meeting.id)}
                  >
                    <div className="mb-1 font-medium">
                      {meeting.title || "Untitled Meeting"}
                    </div>
                    <div className="flex items-center text-sm text-gray-500">
                      <Clock className="mr-1.5 size-3.5" />
                      {formatReadableDate(meeting.created_datetime)}
                    </div>
                  </div>
                  <div className="flex opacity-0 transition-opacity group-hover:opacity-100">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="size-8 p-0"
                      onClick={() => {
                        setRenameTitle(meeting.title || "");
                        setShowRenameModal(meeting.id);
                      }}
                    >
                      <span className="sr-only">Rename</span>
                      <Pencil className="size-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="size-8 p-0 hover:bg-red-100" style={{color: '#B21010'}}
                      onClick={() => setShowDeleteModal(meeting.id)}
                    >
                      <span className="sr-only">Delete</span>
                      <Trash2 className="size-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}

            {!showAllMeetings && sortedMeetings.length > 5 && (
              <Button
                variant="outline"
                className="mt-4 w-full"
                onClick={() => setShowAllMeetings(true)}
              >
                View All Meetings
              </Button>
            )}

            {showAllMeetings && (
              <Button
                onClick={handleNewMeeting}
                className="mt-4 w-full bg-blue-500 hover:bg-blue-600"
              >
                <Plus className="mr-2 size-4" />
                Start New Meeting
              </Button>
            )}
          </div>
        )}
      </div>
    </>
  );
}

export default MeetingsList;
