#!/usr/bin/env python3
"""
Skill Initializer - Creates a new skill from template

Usage:
    init_skill.py <skill-name> --path <path>

Examples:
    init_skill.py my-new-skill --path skills/public
    init_skill.py my-api-helper --path skills/private
    init_skill.py custom-skill --path /custom/location
"""

import sys
from pathlib import Path


SKILL_TEMPLATE = """---
name: {skill_name}
description: |
  [TODO: Complete and informative explanation of what the skill does and when to use it.
  Use third-person: "This skill should be used when Claude needs to..."
  Include specific triggers: file types, tasks, or scenarios that trigger it.
  Example: "Comprehensive PDF processing. Use this skill when Claude needs to
  work with .pdf files for: extracting text, merging documents, filling forms."]

# === 调用控制配置 (根据需要选择) ===
# 决策流程: https://code.claude.com/docs/en/skills#control-who-invokes-a-skill
#
# disable-model-invocation: true    # 取消注释以仅允许用户调用 (如 /commit, /deploy)
# user-invocable: false             # 取消注释以仅允许 Claude 自动调用 (如背景知识)
#
# 调用模式对比:
# | 模式         | 配置                          | 用户调用 | Claude 自动调用 |
# |--------------|-------------------------------|----------|-----------------|
# | 默认模式     | (无配置)                      | ✓        | ✓               |
# | 用户独占     | disable-model-invocation: true| ✓        | ✗               |
# | Claude 独占  | user-invocable: false         | ✗        | ✓               |

# === 其他可选配置 ===
# 详细配置说明: https://code.claude.com/docs/en/skills#frontmatter-reference
# 或查看: ~/.claude/skills/skill-creator/references/frontmatter.md
#
# argument-hint: "[arg1] [arg2]"     # 参数提示 (如: "[issue-number]")
# allowed-tools: ["Bash", "Read"]    # 允许的工具 (无需用户许可)
# model: "sonnet"                     # 指定模型 (sonnet/opus/haiku)
# context: fork                       # 在子 Agent 中运行
# agent: "Explore"                    # 配合 context: fork 使用
---

# {skill_title}

## Overview

[TODO: 1-2 sentences explaining what this skill enables]

## Structuring This Skill

[TODO: Choose the structure that best fits this skill's purpose. Common patterns:

**1. Workflow-Based** (best for sequential processes)
- Works well when there are clear step-by-step procedures
- Example: DOCX skill with "Workflow Decision Tree" → "Reading" → "Creating" → "Editing"
- Structure: ## Overview → ## Workflow Decision Tree → ## Step 1 → ## Step 2...

**2. Task-Based** (best for tool collections)
- Works well when the skill offers different operations/capabilities
- Example: PDF skill with "Quick Start" → "Merge PDFs" → "Split PDFs" → "Extract Text"
- Structure: ## Overview → ## Quick Start → ## Task Category 1 → ## Task Category 2...

**3. Reference/Guidelines** (best for standards or specifications)
- Works well for brand guidelines, coding standards, or requirements
- Example: Brand styling with "Brand Guidelines" → "Colors" → "Typography" → "Features"
- Structure: ## Overview → ## Guidelines → ## Specifications → ## Usage...

**4. Capabilities-Based** (best for integrated systems)
- Works well when the skill provides multiple interrelated features
- Example: Product Management with "Core Capabilities" → numbered capability list
- Structure: ## Overview → ## Core Capabilities → ### 1. Feature → ### 2. Feature...

Patterns can be mixed and matched as needed. Most skills combine patterns (e.g., start with task-based, add workflow for complex operations).

Delete this entire "Structuring This Skill" section when done - it's just guidance.]

## [TODO: Replace with the first main section based on chosen structure]

[TODO: Add content here. See examples in existing skills:
- Code samples for technical skills
- Decision trees for complex workflows
- Concrete examples with realistic user requests
- References to scripts/templates/references as needed]

## Resources

This skill includes example resource directories that demonstrate how to organize different types of bundled resources:

### scripts/
Executable code (Python/Bash/etc.) that can be run directly to perform specific operations.

**Examples from other skills:**
- PDF skill: `fill_fillable_fields.py`, `extract_form_field_info.py` - utilities for PDF manipulation
- DOCX skill: `document.py`, `utilities.py` - Python modules for document processing

**Appropriate for:** Python scripts, shell scripts, or any executable code that performs automation, data processing, or specific operations.

**Note:** Scripts may be executed without loading into context, but can still be read by Claude for patching or environment adjustments.

### references/
Documentation and reference material intended to be loaded into context to inform Claude's process and thinking.

**Examples from other skills:**
- Product management: `communication.md`, `context_building.md` - detailed workflow guides
- BigQuery: API reference documentation and query examples
- Finance: Schema documentation, company policies

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Claude should reference while working.

### examples/
Example outputs showing expected formats or patterns.

**Examples from other skills:**
- Code skills: Sample outputs showing expected format
- Report skills: Example report templates
- Test skills: Sample test patterns

**Appropriate for:** Sample outputs, format templates, usage examples.

### template.md
Template file for Claude to fill in with generated content.

**Examples from other skills:**
- Report generation: Structured report template
- Documentation: API documentation template
- PR descriptions: Pull request template

**Appropriate for:** Any structured document generation.

---

**Official structure from** https://code.claude.com/docs/en/skills

**Any unneeded directories can be deleted.** Not every skill requires all resource types.
"""

EXAMPLE_SCRIPT = '''#!/usr/bin/env python3
"""
Example helper script for {skill_name}

This is a placeholder script that can be executed directly.
Replace with actual implementation or delete if not needed.

Example real scripts from other skills:
- pdf/scripts/fill_fillable_fields.py - Fills PDF form fields
- pdf/scripts/convert_pdf_to_images.py - Converts PDF pages to images
"""

def main():
    print("This is an example script for {skill_name}")
    # TODO: Add actual script logic here
    # This could be data processing, file conversion, API calls, etc.

if __name__ == "__main__":
    main()
'''

EXAMPLE_REFERENCE = """# Reference Documentation for {skill_title}

This is a placeholder for detailed reference documentation.
Replace with actual reference content or delete if not needed.

Example real reference docs from other skills:
- product-management/references/communication.md - Comprehensive guide for status updates
- product-management/references/context_building.md - Deep-dive on gathering context
- bigquery/references/ - API references and query examples

## When Reference Docs Are Useful

Reference docs are ideal for:
- Comprehensive API documentation
- Detailed workflow guides
- Complex multi-step processes
- Information too lengthy for main SKILL.md
- Content that's only needed for specific use cases

## Structure Suggestions

### API Reference Example
- Overview
- Authentication
- Endpoints with examples
- Error codes
- Rate limits

### Workflow Guide Example
- Prerequisites
- Step-by-step instructions
- Common patterns
- Troubleshooting
- Best practices
"""

EXAMPLE_TEMPLATE = """# Template for {skill_title}

This is a placeholder template file for Claude to fill in.
Replace with actual template content or delete if not needed.

Template files define the structure for generated output.
Claude will fill in the placeholders with actual content.

## Example Template Structure

# [Title]

## Overview
[Brief description of the content]

## Details
[Main content goes here]

## Notes
[Any additional notes or considerations]
"""

EXAMPLE_EXAMPLE = """# Example Output for {skill_title}

This is a placeholder example file showing expected output format.
Replace with actual example content or delete if not needed.

Example files demonstrate the expected format or pattern
that Claude should follow when generating output.

## When Example Files Are Useful

Example files are ideal for:
- Showing expected output format
- Demonstrating code patterns
- Illustrating document structure
- Providing reference implementations

## Example Content

[Your example content would go here]
"""


def title_case_skill_name(skill_name):
    """Convert hyphenated skill name to Title Case for display."""
    return ' '.join(word.capitalize() for word in skill_name.split('-'))


def init_skill(skill_name, path):
    """
    Initialize a new skill directory with template SKILL.md.

    Args:
        skill_name: Name of the skill
        path: Path where the skill directory should be created

    Returns:
        Path to created skill directory, or None if error
    """
    # Determine skill directory path
    skill_dir = Path(path).resolve() / skill_name

    # Check if directory already exists
    if skill_dir.exists():
        print(f"❌ Error: Skill directory already exists: {skill_dir}")
        return None

    # Create skill directory
    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        print(f"✅ Created skill directory: {skill_dir}")
    except Exception as e:
        print(f"❌ Error creating directory: {e}")
        return None

    # Create SKILL.md from template
    skill_title = title_case_skill_name(skill_name)
    skill_content = SKILL_TEMPLATE.format(
        skill_name=skill_name,
        skill_title=skill_title
    )

    skill_md_path = skill_dir / 'SKILL.md'
    try:
        skill_md_path.write_text(skill_content)
        print("✅ Created SKILL.md")
    except Exception as e:
        print(f"❌ Error creating SKILL.md: {e}")
        return None

    # Create resource directories with example files
    try:
        # Create scripts/ directory with example script
        scripts_dir = skill_dir / 'scripts'
        scripts_dir.mkdir(exist_ok=True)
        example_script = scripts_dir / 'example.py'
        example_script.write_text(EXAMPLE_SCRIPT.format(skill_name=skill_name))
        example_script.chmod(0o755)
        print("✅ Created scripts/example.py")

        # Create references/ directory with example reference doc
        references_dir = skill_dir / 'references'
        references_dir.mkdir(exist_ok=True)
        example_reference = references_dir / 'api_reference.md'
        example_reference.write_text(EXAMPLE_REFERENCE.format(skill_title=skill_title))
        print("✅ Created references/api_reference.md")

        # Create examples/ directory with example file
        examples_dir = skill_dir / 'examples'
        examples_dir.mkdir(exist_ok=True)
        example_file = examples_dir / 'sample.md'
        example_file.write_text(EXAMPLE_EXAMPLE.format(skill_title=skill_title))
        print("✅ Created examples/sample.md")

        # Create template.md file
        template_file = skill_dir / 'template.md'
        template_file.write_text(EXAMPLE_TEMPLATE.format(skill_title=skill_title))
        print("✅ Created template.md")
    except Exception as e:
        print(f"❌ Error creating resource directories: {e}")
        return None

    # Print next steps
    print(f"\n✅ Skill '{skill_name}' initialized successfully at {skill_dir}")
    print("\nNext steps:")
    print("1. Edit SKILL.md to complete the TODO items and update the description")
    print("2. Customize or delete the example files in scripts/, references/, examples/, and template.md")
    print("3. Run the validator when ready to check the skill structure")

    return skill_dir


def main():
    if len(sys.argv) < 4 or sys.argv[2] != '--path':
        print("Usage: init_skill.py <skill-name> --path <path>")
        print("\nSkill name requirements:")
        print("  - Hyphen-case identifier (e.g., 'data-analyzer')")
        print("  - Lowercase letters, digits, and hyphens only")
        print("  - Max 40 characters")
        print("  - Must match directory name exactly")
        print("\nExamples:")
        print("  init_skill.py my-new-skill --path skills/public")
        print("  init_skill.py my-api-helper --path skills/private")
        print("  init_skill.py custom-skill --path /custom/location")
        sys.exit(1)

    skill_name = sys.argv[1]
    path = sys.argv[3]

    print(f"🚀 Initializing skill: {skill_name}")
    print(f"   Location: {path}")
    print()

    result = init_skill(skill_name, path)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
