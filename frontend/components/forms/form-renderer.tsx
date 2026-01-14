"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FormField } from "./form-field";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

interface FormSchema {
  title: string;
  description?: string;
  fields: Array<{
    id: string;
    type: string;
    label: string;
    required?: boolean;
    show_if?: Record<string, any>;
    [key: string]: any;
  }>;
  on_submit?: {
    action?: string;
    emit_event?: string;
    workflow?: string;
    notify?: string[];
  };
}

interface FormRendererProps {
  formId: string;
  schema: FormSchema;
  initialValues?: Record<string, any>;
  onSubmit?: (responses: Record<string, any>) => void;
  onCancel?: () => void;
  readOnly?: boolean;
}

export function FormRenderer({
  formId,
  schema,
  initialValues = {},
  onSubmit,
  onCancel,
  readOnly = false,
}: FormRendererProps) {
  const [responses, setResponses] = useState<Record<string, any>>(initialValues);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Initialize responses with default values
  useEffect(() => {
    const defaults: Record<string, any> = {};
    schema.fields.forEach((field) => {
      if (field.default && !responses[field.id]) {
        defaults[field.id] = field.default;
      }
    });
    if (Object.keys(defaults).length > 0) {
      setResponses((prev) => ({ ...defaults, ...prev }));
    }
  }, [schema.fields]);

  // Check if a field should be shown based on conditional logic
  const shouldShowField = (field: any): boolean => {
    if (!field.show_if) return true;

    for (const [fieldId, expectedValues] of Object.entries(field.show_if)) {
      const actualValue = responses[fieldId];
      const expected = Array.isArray(expectedValues) ? expectedValues : [expectedValues];

      if (!expected.includes(actualValue)) {
        return false;
      }
    }

    return true;
  };

  // Validate form responses
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    schema.fields.forEach((field) => {
      if (!shouldShowField(field)) return;

      const value = responses[field.id];

      // Required validation
      if (field.required && (value === undefined || value === null || value === "")) {
        newErrors[field.id] = `${field.label} is required`;
      }

      // Min length validation
      if (field.min_length && typeof value === "string" && value.length < field.min_length) {
        newErrors[field.id] = `${field.label} must be at least ${field.min_length} characters`;
      }

      // Max length validation
      if (field.max_length && typeof value === "string" && value.length > field.max_length) {
        newErrors[field.id] = `${field.label} must be at most ${field.max_length} characters`;
      }

      // Min/max value validation for numbers
      if (field.type === "number" && typeof value === "number") {
        if (field.min !== undefined && value < field.min) {
          newErrors[field.id] = `${field.label} must be at least ${field.min}`;
        }
        if (field.max !== undefined && value > field.max) {
          newErrors[field.id] = `${field.label} must be at most ${field.max}`;
        }
      }

      // Checkbox min/max selections
      if (field.type === "checkbox" && Array.isArray(value)) {
        if (field.min_selections && value.length < field.min_selections) {
          newErrors[field.id] = `Select at least ${field.min_selections} options`;
        }
        if (field.max_selections && value.length > field.max_selections) {
          newErrors[field.id] = `Select at most ${field.max_selections} options`;
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) {
      toast.error("Please fix the errors before submitting");
      return;
    }

    setIsSubmitting(true);

    try {
      // Submit to API
      const response = await axios.post(
        `http://localhost:8001/api/v1/forms/${formId}/responses`,
        {
          responses,
          responded_by: "user", // TODO: Get from auth context
          responded_by_type: "user",
        }
      );

      toast.success("Form submitted successfully!");

      // Call onSubmit callback if provided
      if (onSubmit) {
        onSubmit(responses);
      }
    } catch (error: any) {
      console.error("Failed to submit form:", error);
      toast.error(error.response?.data?.detail || "Failed to submit form");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFieldChange = (fieldId: string, value: any) => {
    setResponses((prev) => ({
      ...prev,
      [fieldId]: value,
    }));

    // Clear error for this field when user starts typing
    if (errors[fieldId]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[fieldId];
        return newErrors;
      });
    }
  };

  const visibleFields = schema.fields.filter(shouldShowField);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{schema.title}</CardTitle>
        {schema.description && <CardDescription>{schema.description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
          className="space-y-6"
        >
          {visibleFields.map((field) => (
            <FormField
              key={field.id}
              field={field}
              value={responses[field.id]}
              onChange={(value) => handleFieldChange(field.id, value)}
              error={errors[field.id]}
              disabled={readOnly || isSubmitting}
            />
          ))}

          {!readOnly && (
            <div className="flex justify-end gap-2 pt-4">
              {onCancel && (
                <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
                  Cancel
                </Button>
              )}
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Submit
              </Button>
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
