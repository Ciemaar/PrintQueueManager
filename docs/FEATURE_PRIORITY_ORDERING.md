# Feature Request: Print Priority Ordering

## Background

The initial project requirements included the ability to "organize, categorize, and prioritize" 3D prints. While the system currently supports categorizing via `PrintStatus` (e.g., `TO BE PRINTED`, `PRINT IN PROGRESS`), and categorizing via custom notes, there is no explicit system to rank or prioritize the order in which items should be printed.

## Proposed Solution

Introduce a robust priority system to the Print Queue Manager.

### Option 1: Drag-and-Drop Reordering (HTMX + SortableJS)

Implement a fully interactive queue where users can click and drag rows up or down in the UI.

- Update the `PrintJob` database model to include a `sort_order` integer column.
- Use [SortableJS](https://sortablejs.github.io/Sortable/) hooked into HTMX's `hx-trigger="end"` to fire an API request that updates the new index of the row.
- `src/app/main.py` would handle a bulk update of `sort_order` for the affected rows.

### Option 2: Explicit Priority Tags

Add a formal `Priority` column (Enum: `Low`, `Medium`, `High`, `Urgent`).

- Users select the priority from a dropdown menu, similar to the existing status dropdown.
- The default UI sort logic (`order_by(PrintJob.created_at.desc())`) would be updated to order by `PrintJob.priority` first, and then `created_at` second.
- Visual indicators (like a red badge for `Urgent`) could be added using PicoCSS.

## Next Steps

Determine which UX (Drag & Drop vs Explicit Tags) aligns best with the user workflow, then implement the frontend changes, database migration, and routing required to support it.
