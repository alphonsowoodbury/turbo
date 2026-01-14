"use client";

import { useIssueForms } from "@/hooks/use-forms";
import { FormRenderer } from "./form-renderer";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, FileText } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface IssueFormsSectionProps {
  issueId: string;
}

export function IssueFormsSection({ issueId }: IssueFormsSectionProps) {
  const { data: forms, isLoading, error } = useIssueForms(issueId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">Loading forms...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Failed to load forms. Please try again later.
        </AlertDescription>
      </Alert>
    );
  }

  if (!forms || forms.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <FileText className="h-12 w-12 text-muted-foreground/30 mb-4" />
        <p className="text-sm text-muted-foreground mb-1">No forms attached to this issue</p>
        <p className="text-xs text-muted-foreground">
          Forms can be added to collect structured information
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-1">Forms</h3>
        <p className="text-sm text-muted-foreground">
          Fill out the forms below to provide structured feedback and information.
        </p>
      </div>

      {forms.map((form) => (
        <div key={form.id} className="space-y-2">
          {form.status === "archived" && (
            <Alert>
              <AlertDescription>
                This form has been archived and is read-only.
              </AlertDescription>
            </Alert>
          )}

          <FormRenderer
            formId={form.id}
            schema={form.schema}
            readOnly={form.status === "archived"}
            onSubmit={(responses) => {
              console.log("Form submitted:", { formId: form.id, responses });
            }}
          />
        </div>
      ))}
    </div>
  );
}
