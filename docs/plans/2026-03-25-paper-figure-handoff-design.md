# Paper Figure Handoff Design

## Goal

Replace the current PaperBanana-backed figure generation stage with a lighter figure handoff workflow that prepares PaperBanana-ready text for the user instead of generating image assets inside Paper.

## Context

The current figure stage is over-coupled:

- draft sections insert figure placeholders
- the `figures` stage turns those placeholders into PaperBanana image candidates
- quality treats missing selected figure assets as a critical export blocker
- the Figure Review UI is built around image previews and asset selection

This creates a fragile dependency on an external image-generation runtime even though the actual user workflow is better served by preparing the text that PaperBanana needs and letting the user generate images there manually.

## Approach Options

### Option 1: Keep automatic generation and only change the default pipeline mode

- Pros: smallest backend change
- Cons: still depends on image generation working inside Paper
- Cons: keeps quality/export coupled to generated assets
- Cons: does not match the intended user workflow

### Option 2: Replace image generation with a text-only handoff stage

- Pros: removes the fragile external generation dependency from Paper
- Pros: matches the desired workflow where the user finishes the figure in PaperBanana
- Pros: still gives users structured figure-specific guidance instead of raw placeholders
- Cons: requires API, quality, export, and Figure Review UI updates together

### Option 3: Keep generation optional and support both images and text handoff

- Pros: most flexible
- Cons: introduces mixed states and more UI complexity than needed right now
- Cons: forces the quality and export rules to handle two different figure completion models

## Recommendation

Use **Option 2**.

Paper should stop generating figure assets. The `figures` stage should instead parse the draft placeholders and create figure handoff specs with:

- `Method Section Content (Markdown recommended)`
- `Figure Caption (Markdown recommended)`
- optional source context and section linkage for review

The user then copies those fields into PaperBanana and chooses advanced settings there.

## Product Behavior

### Figure stage semantics

The `figures` stage remains in the pipeline, but its job changes from asset generation to handoff generation.

For each unique placeholder like `[FIGURE_1: ...]`, create a figure spec that contains:

- section key
- figure number and figure key
- caption draft
- method-section content derived from the surrounding section context
- source excerpt for reviewer context
- status such as `prepared`

No figure asset rows are created.

### Figure Review UI

Replace the image-grid review with text handoff cards.

Each card should show:

- figure number
- linked section key
- figure caption draft
- method section content
- source excerpt / context note
- copy buttons for caption and method content

The panel should clearly communicate that Paper generates reusable figure instructions, while PaperBanana is used separately for actual image generation and advanced settings like aspect ratio, candidate count, and critic rounds.

### User responsibility split

Paper prepares:

- the figure-specific method block
- the figure caption draft

PaperBanana remains responsible for:

- pipeline mode selection
- retrieval setting
- number of candidates
- aspect ratio
- refinement settings
- model choice

If automatic generation is ever reintroduced, `demo_planner_critic` is the right default, but this design removes the dependency from Paper entirely.

## Quality and Export Changes

### Quality

Unresolved figure placeholders should no longer be a critical blocker just because there is no generated asset.

Instead, the figure-related quality rule becomes:

- critical only when a placeholder exists but no prepared figure handoff spec exists for that figure key

This makes `Run All` and `Final Export` dependent on the presence of figure handoff text, not image files.

### Export

Exports should continue to replace figure placeholders with text-only insert guidance.

If there is no actual selected image, export should still produce a readable placeholder note using the prepared caption. No image path embedding is required for the new workflow.

## Data Model

`FigureSpec` should evolve from an image-generation record into a handoff record.

Keep:

- `caption_draft`
- `source_excerpt`
- `figure_key`
- `figure_number`
- `section_key`
- `status`

Add:

- `method_section_content`

Keep `FigureAsset` support in the schema only if it avoids unnecessary churn, but the stage and UI should stop relying on it.

## Testing

### Backend

- figure stage creates handoff specs from placeholders without creating assets
- quality passes when each placeholder has a prepared figure spec
- final export is not blocked by missing figure assets
- export still renders human-readable figure insert text

### Frontend

- Figure Review renders handoff text cards instead of candidate previews
- copy buttons write caption and method text to the clipboard
- empty-state copy reflects the new workflow

