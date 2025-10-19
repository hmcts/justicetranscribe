/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Pydantic model for transcription metadata.
 */
export type TranscriptionMetadata = {
    id: string;
    title: string;
    created_datetime: (string | null);
    updated_datetime?: (string | null);
    is_showable_in_ui: boolean;
    speakers?: Array<string>;
};

