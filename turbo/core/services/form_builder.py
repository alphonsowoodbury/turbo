"""Form Builder API for creating form schemas programmatically."""

from typing import Any, Literal


class FormBuilder:
    """
    Builder API for creating form schemas safely.

    Provides structured methods for LLMs and developers to construct forms
    without needing to manually write JSON schemas.

    Example:
        >>> form = FormBuilder("User Preferences")
        >>> form.add_text("name", "Your Name", required=True)
        >>> form.add_radio("role", "Your Role", ["Developer", "Designer", "Manager"])
        >>> schema = form.build()
    """

    def __init__(self, title: str, description: str = ""):
        """Initialize form builder."""
        self.title = title
        self.description = description
        self.fields: list[dict[str, Any]] = []
        self.on_submit: dict[str, Any] | None = None

    def add_text(
        self,
        field_id: str,
        label: str,
        placeholder: str = "",
        required: bool = False,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        show_if: dict[str, Any] | None = None,
    ) -> "FormBuilder":
        """
        Add a text input field.

        Args:
            field_id: Unique field identifier
            label: Human-readable label
            placeholder: Placeholder text
            required: Whether field is required
            min_length: Minimum character length
            max_length: Maximum character length
            pattern: Regex pattern for validation
            show_if: Conditional display logic

        Returns:
            Self for method chaining
        """
        field = {
            "id": field_id,
            "type": "text",
            "label": label,
            "required": required,
        }

        if placeholder:
            field["placeholder"] = placeholder
        if min_length is not None:
            field["min_length"] = min_length
        if max_length is not None:
            field["max_length"] = max_length
        if pattern:
            field["pattern"] = pattern
        if show_if:
            field["show_if"] = show_if

        self.fields.append(field)
        return self

    def add_textarea(
        self,
        field_id: str,
        label: str,
        placeholder: str = "",
        required: bool = False,
        min_length: int | None = None,
        max_length: int | None = None,
        rows: int = 4,
        show_if: dict[str, Any] | None = None,
    ) -> "FormBuilder":
        """
        Add a multi-line textarea field.

        Args:
            field_id: Unique field identifier
            label: Human-readable label
            placeholder: Placeholder text
            required: Whether field is required
            min_length: Minimum character length
            max_length: Maximum character length
            rows: Number of visible rows
            show_if: Conditional display logic

        Returns:
            Self for method chaining
        """
        field = {
            "id": field_id,
            "type": "textarea",
            "label": label,
            "required": required,
            "rows": rows,
        }

        if placeholder:
            field["placeholder"] = placeholder
        if min_length is not None:
            field["min_length"] = min_length
        if max_length is not None:
            field["max_length"] = max_length
        if show_if:
            field["show_if"] = show_if

        self.fields.append(field)
        return self

    def add_radio(
        self,
        field_id: str,
        label: str,
        options: list[str] | list[dict[str, Any]],
        required: bool = False,
        default: str | None = None,
        show_if: dict[str, Any] | None = None,
    ) -> "FormBuilder":
        """
        Add a radio button group (single choice).

        Args:
            field_id: Unique field identifier
            label: Human-readable label
            options: List of option values or dicts with {value, label, allows_text}
            required: Whether field is required
            default: Default selected value
            show_if: Conditional display logic

        Returns:
            Self for method chaining
        """
        # Normalize options format
        normalized_options = []
        for opt in options:
            if isinstance(opt, str):
                normalized_options.append({"value": opt, "label": opt})
            else:
                normalized_options.append(opt)

        field = {
            "id": field_id,
            "type": "radio",
            "label": label,
            "required": required,
            "options": normalized_options,
        }

        if default:
            field["default"] = default
        if show_if:
            field["show_if"] = show_if

        self.fields.append(field)
        return self

    def add_dropdown(
        self,
        field_id: str,
        label: str,
        options: list[str] | list[dict[str, str]],
        required: bool = False,
        default: str | None = None,
        placeholder: str = "Select an option...",
        show_if: dict[str, Any] | None = None,
    ) -> "FormBuilder":
        """
        Add a dropdown/select field (single choice).

        Args:
            field_id: Unique field identifier
            label: Human-readable label
            options: List of option values or dicts with {value, label}
            required: Whether field is required
            default: Default selected value
            placeholder: Placeholder text
            show_if: Conditional display logic

        Returns:
            Self for method chaining
        """
        # Normalize options format
        normalized_options = []
        for opt in options:
            if isinstance(opt, str):
                normalized_options.append({"value": opt, "label": opt})
            else:
                normalized_options.append(opt)

        field = {
            "id": field_id,
            "type": "dropdown",
            "label": label,
            "required": required,
            "options": normalized_options,
            "placeholder": placeholder,
        }

        if default:
            field["default"] = default
        if show_if:
            field["show_if"] = show_if

        self.fields.append(field)
        return self

    def add_checkbox(
        self,
        field_id: str,
        label: str,
        options: list[str] | list[dict[str, str]],
        required: bool = False,
        min_selections: int | None = None,
        max_selections: int | None = None,
        show_if: dict[str, Any] | None = None,
    ) -> "FormBuilder":
        """
        Add a checkbox group (multiple choice).

        Args:
            field_id: Unique field identifier
            label: Human-readable label
            options: List of option values or dicts with {value, label}
            required: Whether at least one must be selected
            min_selections: Minimum number of selections
            max_selections: Maximum number of selections
            show_if: Conditional display logic

        Returns:
            Self for method chaining
        """
        # Normalize options format
        normalized_options = []
        for opt in options:
            if isinstance(opt, str):
                normalized_options.append({"value": opt, "label": opt})
            else:
                normalized_options.append(opt)

        field = {
            "id": field_id,
            "type": "checkbox",
            "label": label,
            "required": required,
            "options": normalized_options,
        }

        if min_selections is not None:
            field["min_selections"] = min_selections
        if max_selections is not None:
            field["max_selections"] = max_selections
        if show_if:
            field["show_if"] = show_if

        self.fields.append(field)
        return self

    def add_number(
        self,
        field_id: str,
        label: str,
        required: bool = False,
        min_value: float | None = None,
        max_value: float | None = None,
        step: float = 1.0,
        placeholder: str = "",
        show_if: dict[str, Any] | None = None,
    ) -> "FormBuilder":
        """
        Add a number input field.

        Args:
            field_id: Unique field identifier
            label: Human-readable label
            required: Whether field is required
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            step: Increment step
            placeholder: Placeholder text
            show_if: Conditional display logic

        Returns:
            Self for method chaining
        """
        field = {
            "id": field_id,
            "type": "number",
            "label": label,
            "required": required,
            "step": step,
        }

        if placeholder:
            field["placeholder"] = placeholder
        if min_value is not None:
            field["min"] = min_value
        if max_value is not None:
            field["max"] = max_value
        if show_if:
            field["show_if"] = show_if

        self.fields.append(field)
        return self

    def add_date(
        self,
        field_id: str,
        label: str,
        required: bool = False,
        min_date: str | None = None,
        max_date: str | None = None,
        show_if: dict[str, Any] | None = None,
    ) -> "FormBuilder":
        """
        Add a date picker field.

        Args:
            field_id: Unique field identifier
            label: Human-readable label
            required: Whether field is required
            min_date: Minimum allowed date (ISO format)
            max_date: Maximum allowed date (ISO format)
            show_if: Conditional display logic

        Returns:
            Self for method chaining
        """
        field = {
            "id": field_id,
            "type": "date",
            "label": label,
            "required": required,
        }

        if min_date:
            field["min"] = min_date
        if max_date:
            field["max"] = max_date
        if show_if:
            field["show_if"] = show_if

        self.fields.append(field)
        return self

    def add_file(
        self,
        field_id: str,
        label: str,
        required: bool = False,
        accept: list[str] | None = None,
        max_size_mb: float = 10.0,
        multiple: bool = False,
        show_if: dict[str, Any] | None = None,
    ) -> "FormBuilder":
        """
        Add a file upload field.

        Args:
            field_id: Unique field identifier
            label: Human-readable label
            required: Whether field is required
            accept: List of accepted file types (e.g., ['.pdf', '.png', 'image/*'])
            max_size_mb: Maximum file size in MB
            multiple: Allow multiple file uploads
            show_if: Conditional display logic

        Returns:
            Self for method chaining
        """
        field = {
            "id": field_id,
            "type": "file",
            "label": label,
            "required": required,
            "max_size_mb": max_size_mb,
            "multiple": multiple,
        }

        if accept:
            field["accept"] = accept
        if show_if:
            field["show_if"] = show_if

        self.fields.append(field)
        return self

    def set_on_submit(
        self,
        action: str | None = None,
        event: str | None = None,
        workflow: str | None = None,
        notify: str | list[str] | None = None,
        **kwargs: Any,
    ) -> "FormBuilder":
        """
        Configure what happens when form is submitted.

        Args:
            action: Simple action to perform (e.g., "close_issue")
            event: Event name to emit
            workflow: Workflow ID to trigger
            notify: User(s) to notify
            **kwargs: Additional configuration

        Returns:
            Self for method chaining
        """
        self.on_submit = {}

        if action:
            self.on_submit["action"] = action
        if event:
            self.on_submit["emit_event"] = event
        if workflow:
            self.on_submit["workflow"] = workflow
        if notify:
            self.on_submit["notify"] = notify if isinstance(notify, list) else [notify]

        # Add any additional kwargs
        self.on_submit.update(kwargs)

        return self

    def build(self) -> dict[str, Any]:
        """
        Build and return the form schema.

        Returns:
            Complete form schema as dictionary
        """
        schema = {
            "title": self.title,
            "description": self.description,
            "fields": self.fields,
        }

        if self.on_submit:
            schema["on_submit"] = self.on_submit

        return schema

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the form schema.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if not self.title:
            errors.append("Form title is required")

        if not self.fields:
            errors.append("Form must have at least one field")

        # Check for duplicate field IDs
        field_ids = [f["id"] for f in self.fields]
        if len(field_ids) != len(set(field_ids)):
            errors.append("Duplicate field IDs found")

        # Validate each field
        for field in self.fields:
            if "id" not in field:
                errors.append(f"Field missing ID: {field}")
            if "type" not in field:
                errors.append(f"Field {field.get('id', '?')} missing type")
            if "label" not in field:
                errors.append(f"Field {field.get('id', '?')} missing label")

        return len(errors) == 0, errors
