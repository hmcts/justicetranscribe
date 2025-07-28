import { useState, useEffect } from "react";
import { TemplateMetadata } from "@/src/api/generated";

interface TemplateResponse {
  templates: TemplateMetadata[];
}

export default function useTemplates() {
  const [templates, setTemplates] = useState<TemplateMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchTemplates() {
      try {
        setIsLoading(true);
        const response = await fetch("/api/proxy/templates");

        if (!response.ok) {
          throw new Error("Failed to fetch templates");
        }

        const data: TemplateResponse = await response.json();

        setTemplates(data.templates);
      } catch (err) {
        console.error("Error fetching templates:", err);
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setIsLoading(false);
      }
    }

    fetchTemplates();
  }, []);

  return { templates, isLoading, error };
}
