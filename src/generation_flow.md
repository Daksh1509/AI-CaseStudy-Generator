# AI Case Study Generation Flow

This describes how the system will turn raw company documents into a structured, source-backed case study.

## Step 1 – Document loading

- Use `load_company_documents(company_name)` to read all files for a company.
- Each document has: company_name, source_id, source_type, source_name, file_path, text.

## Step 2 – Preprocessing and cleaning

- Remove boilerplate: navigation menus, sidebars, repeated headers/footers.
- Normalize whitespace, fix broken line breaks, and join paragraphs where needed.
- Keep source_id and source_type attached to each text block.

## Step 3 – Chunking

- Split cleaned text into manageable chunks (for example 500–1,000 characters with overlap).
- Each chunk keeps: company_name, source_id, source_type, chunk_id, chunk_text, source_name.

## Step 4 – Summarization

- For each chunk, generate a short summary focused on key facts and themes.
- Combine chunk summaries per source or topic when needed.

## Step 5 – Insight extraction

- From summaries and chunks, extract:
  - company background
  - key challenges
  - strategies/interventions
  - operations/implementation details
  - results/impact
  - risks and learning outcomes

## Step 6 – Structured case generation

- Use prompts to generate full sections:
  - Background
  - Challenge
  - Intervention/Strategy
  - Execution/Operations
  - Results and Impact
  - Learning Outcomes and Risks
- Ensure each section is written clearly and uses only information from the company’s documents.

## Step 7 – Evidence mapping

- For each section, select 2–3 supporting snippets from the most relevant chunks.
- Show the snippet text along with source_id, source_type, and source_name.

## Step 8 – Output formatting

- Combine sections + evidence into a structured case study output.
- Provide this output in the Streamlit app and allow export as text/markdown for editing.