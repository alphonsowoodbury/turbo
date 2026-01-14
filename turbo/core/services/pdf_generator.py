"""PDF generation service for resumes with template support."""

import re
from datetime import datetime
from pathlib import Path


class PDFGeneratorService:
    """Service for generating PDF resumes from markdown with templates."""

    def __init__(self):
        """Initialize PDF generator."""
        self.templates_dir = Path(__file__).parent.parent.parent / "templates" / "resumes"

    def markdown_to_html(self, markdown_content: str, template: str = "professional") -> str:
        """Convert markdown to styled HTML using template."""
        # Get template
        html_template = self._get_template(template)

        # Convert markdown to HTML (basic conversion)
        html_content = self._simple_markdown_to_html(markdown_content)

        # Insert into template
        final_html = html_template.replace("{{CONTENT}}", html_content)

        return final_html

    def _get_template(self, template_name: str) -> str:
        """Get HTML template for resume styling."""
        # Professional template with clean, ATS-friendly styling
        professional_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: Letter;
            margin: 0.75in;
        }

        body {
            font-family: 'Calibri', 'Arial', sans-serif;
            font-size: 11pt;
            line-height: 1.4;
            color: #000000;
            margin: 0;
            padding: 0;
        }

        h1 {
            font-size: 24pt;
            font-weight: bold;
            margin: 0 0 4pt 0;
            padding: 0;
            color: #000000;
        }

        h2 {
            font-size: 13pt;
            font-weight: bold;
            margin: 12pt 0 6pt 0;
            padding-bottom: 2pt;
            border-bottom: 1.5pt solid #000000;
            color: #000000;
        }

        h3 {
            font-size: 11pt;
            font-weight: bold;
            margin: 8pt 0 2pt 0;
            color: #000000;
        }

        p {
            margin: 0 0 6pt 0;
        }

        ul {
            margin: 4pt 0 8pt 0;
            padding-left: 20pt;
        }

        li {
            margin-bottom: 3pt;
        }

        strong {
            font-weight: bold;
        }

        em {
            font-style: italic;
        }

        a {
            color: #0066cc;
            text-decoration: none;
        }

        hr {
            border: none;
            border-top: 1pt solid #cccccc;
            margin: 10pt 0;
        }

        .contact-info {
            font-size: 10pt;
            margin-bottom: 8pt;
            text-align: center;
        }

        .section-subtitle {
            font-size: 10pt;
            font-style: italic;
            margin-bottom: 8pt;
        }

        .footer {
            font-size: 9pt;
            color: #666666;
            text-align: center;
            margin-top: 20pt;
        }

        .experience-item {
            margin-bottom: 10pt;
        }

        .job-title {
            font-weight: bold;
        }

        .company-name {
            font-weight: bold;
        }

        .date-range {
            font-style: italic;
            float: right;
        }
    </style>
</head>
<body>
{{CONTENT}}
</body>
</html>
"""

        modern_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: Letter;
            margin: 0.6in;
        }

        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 10.5pt;
            line-height: 1.35;
            color: #1a1a1a;
            margin: 0;
            padding: 0;
        }

        h1 {
            font-size: 26pt;
            font-weight: 600;
            margin: 0 0 4pt 0;
            padding: 0;
            color: #2c3e50;
            letter-spacing: -0.5pt;
        }

        h2 {
            font-size: 12pt;
            font-weight: 600;
            margin: 14pt 0 6pt 0;
            padding-bottom: 3pt;
            border-bottom: 2pt solid #3498db;
            color: #2c3e50;
            text-transform: uppercase;
            letter-spacing: 0.5pt;
        }

        h3 {
            font-size: 10.5pt;
            font-weight: 600;
            margin: 7pt 0 3pt 0;
            color: #2c3e50;
        }

        p {
            margin: 0 0 5pt 0;
        }

        ul {
            margin: 3pt 0 7pt 0;
            padding-left: 18pt;
        }

        li {
            margin-bottom: 2pt;
        }

        strong {
            font-weight: 600;
            color: #2c3e50;
        }

        a {
            color: #3498db;
            text-decoration: none;
        }

        hr {
            border: none;
            border-top: 1.5pt solid #ecf0f1;
            margin: 8pt 0;
        }

        .contact-info {
            font-size: 9.5pt;
            margin-bottom: 6pt;
            text-align: center;
            color: #555555;
        }

        .footer {
            font-size: 8.5pt;
            color: #999999;
            text-align: center;
            margin-top: 18pt;
        }
    </style>
</head>
<body>
{{CONTENT}}
</body>
</html>
"""

        templates = {
            "professional": professional_template,
            "modern": modern_template,
        }

        return templates.get(template_name, professional_template)

    def _simple_markdown_to_html(self, markdown: str) -> str:
        """Convert markdown to HTML (basic implementation)."""
        html = markdown

        # Headers
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)

        # Horizontal rules
        html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)

        # Bold and italic
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

        # Links
        html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)

        # Bullet lists
        lines = html.split('\n')
        in_list = False
        processed_lines = []

        for line in lines:
            if line.strip().startswith('- '):
                if not in_list:
                    processed_lines.append('<ul>')
                    in_list = True
                content = line.strip()[2:]
                processed_lines.append(f'<li>{content}</li>')
            else:
                if in_list:
                    processed_lines.append('</ul>')
                    in_list = False
                # Wrap non-header, non-list content in paragraphs
                if line.strip() and not line.strip().startswith('<'):
                    processed_lines.append(f'<p>{line}</p>')
                else:
                    processed_lines.append(line)

        if in_list:
            processed_lines.append('</ul>')

        html = '\n'.join(processed_lines)

        # Add contact info class
        html = html.replace('<p>USA |', '<p class="contact-info">USA |')
        html = html.replace('<p>*Resume generated', '<p class="footer">*Resume generated')

        return html

    def html_to_pdf(self, html_content: str, output_path: Path) -> Path:
        """Convert HTML to PDF using WeasyPrint."""
        try:
            from weasyprint import HTML, CSS
        except ImportError:
            raise ImportError(
                "WeasyPrint is required for PDF generation. "
                "Install with: pip install weasyprint"
            )

        # Generate PDF
        HTML(string=html_content).write_pdf(output_path)

        return output_path

    def markdown_to_pdf(
        self, markdown_content: str, output_path: Path, template: str = "professional"
    ) -> Path:
        """Convert markdown resume to PDF with styling."""
        # Convert to HTML
        html_content = self.markdown_to_html(markdown_content, template)

        # Convert to PDF
        return self.html_to_pdf(html_content, output_path)
