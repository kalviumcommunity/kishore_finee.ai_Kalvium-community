"""Core prompt templating utilities and base classes for FInee.ai."""

import re
from typing import Any, Set, Dict


class PromptTemplateError(ValueError):
    """Exception raised when prompt template rendering or validation fails."""
    pass


class PromptTemplate:
    """Reusable prompt template with placeholder validation and rendering.

    Enables defining prompts with named placeholders, validating required input
    variables, and rendering consistent prompts across API endpoints, batch jobs,
    evaluation pipelines, and CLI tools.
    """

    def __init__(self, template: str, name: str = "prompt_template"):
        """Initialize a PromptTemplate.

        Args:
            template: The raw prompt string containing format placeholders (e.g. {context}).
            name: Optional descriptive name for the template.
        """
        if not isinstance(template, str):
            raise PromptTemplateError("Template must be a string.")
        self.template = template
        self.name = name
        self.input_variables: Set[str] = self._extract_variables(template)

    @staticmethod
    def _extract_variables(template_str: str) -> Set[str]:
        """Extract variable names enclosed in single curly braces {variable}."""
        # Match {variable_name} while ignoring escaped {{ or }}
        pattern = r"(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)\}(?!\})"
        return set(re.findall(pattern, template_str))

    def render(self, **values: Any) -> str:
        """Render template with supplied keyword values.

        Args:
            **values: Variable values to inject into placeholders.

        Returns:
            The formatted prompt string.

        Raises:
            PromptTemplateError: If any required placeholder is missing.
        """
        missing = self.input_variables - set(values.keys())
        if missing:
            missing_list = sorted(list(missing))
            raise PromptTemplateError(
                f"Template '{self.name}' is missing required variable(s): {missing_list}. "
                f"Provided: {sorted(list(values.keys()))}"
            )
        try:
            return self.template.format(**values)
        except Exception as exc:
            raise PromptTemplateError(f"Failed to render template '{self.name}': {exc}") from exc

    def __call__(self, **values: Any) -> str:
        """Allow calling the template object directly as a function."""
        return self.render(**values)

    def __str__(self) -> str:
        return self.template

    def __repr__(self) -> str:
        return f"PromptTemplate(name={self.name!r}, variables={sorted(self.input_variables)})"


def render(template: str | PromptTemplate, **values: Any) -> str:
    """Render a prompt template string or PromptTemplate object with dynamic values.

    Args:
        template: Either a string template with placeholders or a PromptTemplate instance.
        **values: Named variables to substitute into placeholders.

    Returns:
        Rendered string with all placeholders replaced.

    Raises:
        PromptTemplateError: If a required placeholder is missing.
    """
    if isinstance(template, PromptTemplate):
        return template.render(**values)
    
    if not isinstance(template, str):
        raise PromptTemplateError("Template must be a string or PromptTemplate instance.")

    # Validate missing variables for string templates
    extracted_vars = PromptTemplate._extract_variables(template)
    missing = extracted_vars - set(values.keys())
    if missing:
        raise PromptTemplateError(
            f"Missing required template variable(s): {sorted(list(missing))}. "
            f"Provided: {sorted(list(values.keys()))}"
        )

    try:
        return template.format(**values)
    except Exception as exc:
        raise PromptTemplateError(f"Rendering failed: {exc}") from exc
