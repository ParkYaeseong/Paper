# Paper Help Guide Design

## Goal

Add an in-app bilingual usage guide so users can understand the Paper workflow after upload without leaving the app.

## Context

The current Paper UI exposes the stage buttons clearly, but the meaning and order of those stages is not obvious to first-time users. This causes the same questions repeatedly: what to upload, whether reference papers are required, what to click after upload, and when ingest must be rerun.

The guide should be available anywhere in the signed-in app, not just inside a populated project workspace. That rules out a workspace-only panel as the primary help surface.

## Recommended Approach

Add a global `Help / 사용법` button in the authenticated header. Clicking it opens a modal with an `English | 한국어` tab switcher and a compact usage guide.

This keeps the main workspace focused on writing while still making guidance available from any signed-in state, including:

- no project selected
- empty project
- active project workspace

## Content Structure

The modal should present four sections in both languages.

### Quick Start

The exact operating sequence:

1. Upload Selected Files
2. Run Ingest
3. Run Plan
4. Run Draft
5. Run Retrieve
6. Run Ground
7. Review evidence and draft text
8. Run Export

### What To Upload

Clarify that upload is for internal project material, such as:

- README and usage docs
- CSV or JSON result tables
- notes and summaries
- prior draft text
- figure or table source material

Also clarify that reference papers are optional because `Run Retrieve` searches external literature later.

### What Happens Next

Explain the role of each stage briefly and note that adding or deleting files after ingest requires running ingest again to refresh the project profile.

### Common Mistakes

Highlight the most common misuses:

- uploading only literature PDFs and expecting a draft immediately
- skipping ingest and running plan or draft first
- expecting grounded citations before retrieve and ground have run
- forgetting to rerun ingest after changing uploaded files

## UI Design

The guide should be a centered modal with:

- close button
- backdrop click support
- `Escape` key close support
- language tabs at the top
- scrollable body for smaller screens

The header trigger should read `Help / 사용법` so it is understandable regardless of the current tab language.

## Data Model

No backend changes are needed. The guide content should live in the frontend as static structured data.

Recommended structure:

- one content object keyed by language
- each language containing section titles and bullet points

This keeps the first version simple and makes later extraction into markdown or CMS content straightforward.

## Testing

Frontend tests should cover:

- header button is visible to authenticated users
- clicking the button opens the guide modal
- switching language tabs updates visible content
- closing the modal hides it

## Rollout

This is a frontend-only change. Deployment only requires rebuilding and restarting the Paper frontend container after tests and build pass.
