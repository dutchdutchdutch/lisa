# PLACEHOLDERS

## 1. Background
Summary of background.md

## 2. Skill Definitions & Capabilities
define what the skill actually does when called.

Persona & Objective: Who is the skill acting as (e.g., Status Auditor) and what is its primary goal?

Prompt Architecture: Brief description of the system instructions (stored in your .md or .json files).

Available Tools/Commands: List the .sh scripts or API hooks the skill can trigger.

## 3. Data Schema & Configuration
 "source of truth" for data structures.

Input Requirements: What data does the skill need (e.g., a project_manifest.yaml)?

Output Format: Define the structure of the JSON/Markdown the skill produces (e.g., a "Cycle Time Report").

Environment Variables: List any necessary keys or paths required for the .sh tools to run.

## 4. Workflow Logic (The "Loop")
Map the squence of events

Trigger: How is the skill invoked? (Manual, Hook, or Cron).

Step-by-Step Execution: (e.g., 1. Parse JSON -> 2. Run Audit Prompt -> 3. Output MD Report).

Error Handling: What happens when the AI returns a "hallucination" or invalid JSON?

## 5. Evaluation & Quality Benchmarks (EDD)

Success Criteria: What defines a "Good" response from this Claude skill?

Test Cases (Evals): Reference the specific JSON/YAML files used to benchmark the skill's performance.

Validation Rules: (e.g., "Must include a 'Schedule Drift' percentage").

# 6. Installation & Deployment

The "Blackbox" setup.

Prerequisites: Required CLI tools (e.g., Claude Code, n8n, or Python for local scripts).

Setup Script: Documentation for your .sh installation tools.

Usage Examples: A quick "copy-paste" command to see the skill in action.
