"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

interface FieldOption {
  value: string;
  label: string;
  allows_text?: boolean;
}

interface FormFieldSchema {
  id: string;
  type: "text" | "textarea" | "radio" | "dropdown" | "checkbox" | "number" | "date" | "file";
  label: string;
  required?: boolean;
  placeholder?: string;
  options?: FieldOption[];
  min?: number;
  max?: number;
  min_length?: number;
  max_length?: number;
  rows?: number;
  step?: number;
  accept?: string[];
  multiple?: boolean;
  max_size_mb?: number;
  show_if?: Record<string, any>;
}

interface FormFieldProps {
  field: FormFieldSchema;
  value: any;
  onChange: (value: any) => void;
  error?: string;
  disabled?: boolean;
}

export function FormField({
  field,
  value,
  onChange,
  error,
  disabled = false,
}: FormFieldProps) {
  const renderField = () => {
    switch (field.type) {
      case "text":
        return (
          <Input
            type="text"
            value={value || ""}
            onChange={(e) => onChange(e.target.value)}
            placeholder={field.placeholder}
            disabled={disabled}
            className={cn(error && "border-destructive")}
            minLength={field.min_length}
            maxLength={field.max_length}
          />
        );

      case "textarea":
        return (
          <Textarea
            value={value || ""}
            onChange={(e) => onChange(e.target.value)}
            placeholder={field.placeholder}
            disabled={disabled}
            rows={field.rows || 4}
            className={cn(error && "border-destructive")}
            minLength={field.min_length}
            maxLength={field.max_length}
          />
        );

      case "number":
        return (
          <Input
            type="number"
            value={value || ""}
            onChange={(e) => onChange(parseFloat(e.target.value))}
            placeholder={field.placeholder}
            disabled={disabled}
            className={cn(error && "border-destructive")}
            min={field.min}
            max={field.max}
            step={field.step || 1}
          />
        );

      case "date":
        return (
          <Input
            type="date"
            value={value || ""}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className={cn(error && "border-destructive")}
            min={field.min as string}
            max={field.max as string}
          />
        );

      case "radio":
        return (
          <RadioGroup
            value={value || ""}
            onValueChange={onChange}
            disabled={disabled}
            className="space-y-2"
          >
            {field.options?.map((option) => (
              <div key={option.value} className="flex items-center space-x-2">
                <RadioGroupItem value={option.value} id={`${field.id}-${option.value}`} />
                <Label
                  htmlFor={`${field.id}-${option.value}`}
                  className="font-normal cursor-pointer"
                >
                  {option.label}
                </Label>
              </div>
            ))}
          </RadioGroup>
        );

      case "dropdown":
        return (
          <Select value={value || ""} onValueChange={onChange} disabled={disabled}>
            <SelectTrigger className={cn(error && "border-destructive")}>
              <SelectValue placeholder={field.placeholder || "Select an option..."} />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case "checkbox":
        const selectedValues = Array.isArray(value) ? value : [];
        return (
          <div className="space-y-2">
            {field.options?.map((option) => {
              const isChecked = selectedValues.includes(option.value);
              return (
                <div key={option.value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`${field.id}-${option.value}`}
                    checked={isChecked}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        onChange([...selectedValues, option.value]);
                      } else {
                        onChange(selectedValues.filter((v: string) => v !== option.value));
                      }
                    }}
                    disabled={disabled}
                  />
                  <Label
                    htmlFor={`${field.id}-${option.value}`}
                    className="font-normal cursor-pointer"
                  >
                    {option.label}
                  </Label>
                </div>
              );
            })}
          </div>
        );

      case "file":
        return (
          <Input
            type="file"
            onChange={(e) => onChange(e.target.files)}
            disabled={disabled}
            className={cn(error && "border-destructive")}
            accept={field.accept?.join(",")}
            multiple={field.multiple}
          />
        );

      default:
        return <div className="text-muted-foreground">Unsupported field type: {field.type}</div>;
    }
  };

  return (
    <div className="space-y-2">
      <Label htmlFor={field.id} className={cn(field.required && "after:content-['*'] after:ml-0.5 after:text-destructive")}>
        {field.label}
      </Label>
      {renderField()}
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}
