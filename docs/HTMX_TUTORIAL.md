# Learning HTMX for Print Queue Manager

Welcome! If you are a Python developer familiar with web frameworks like Flask, Django, or FastAPI, but new to **HTMX**, this guide will quickly get you up to speed.

In traditional modern web development, you often build an API that returns JSON, and then write a separate React, Vue, or vanilla JavaScript frontend to fetch that JSON and update the DOM.

**HTMX flips this paradigm back to basics:** your FastAPI routes will return *HTML*, not JSON. HTMX simply looks for special attributes in your HTML, makes background HTTP requests when users interact with the page, and swaps the returning HTML directly into the DOM.

## Core Concepts

You only need to understand four main HTML attributes to master HTMX in this project:

1. **`hx-[method]` (e.g., `hx-post`, `hx-get`, `hx-delete`)**: Tells HTMX what kind of HTTP request to make and to which URL.
2. **`hx-trigger`**: Tells HTMX *when* to make the request (e.g., on `click`, `change`, `blur`). If omitted, it defaults to the natural event of the element (clicks for buttons, changes for forms).
3. **`hx-target`**: Tells HTMX *where* to put the HTML response (using a CSS selector like `#element-id`). If omitted, it swaps the HTML into the element that triggered the request.
4. **`hx-swap`**: Tells HTMX *how* to swap the HTML (e.g., `innerHTML`, `outerHTML`, `beforeend`).

---

## Example 1: The "Delete" Button

Let's look at the Delete button in `src/app/templates/job_row.html`:

```html
<button class="btn btn-sm btn-outline-danger"
        hx-post="/jobs/{{ job.id }}/delete"
        hx-target="#job-{{ job.id }}"
        hx-swap="outerHTML"
        hx-confirm="Are you sure you want to delete this job?">
    Delete
</button>
```

**How it works:**
- When the user clicks the button, HTMX first shows a browser confirmation dialog (`hx-confirm`).
- If confirmed, it makes an HTTP `POST` request to `/jobs/123/delete`.
- The backend processes the deletion and returns an empty string `""` as an `HTMLResponse`.
- HTMX targets the table row (`#job-123`) and replaces the entire row (`outerHTML`) with the empty string. The row vanishes from the table instantly without a page reload or a line of JavaScript!

---

## Example 2: The Status Dropdown

Instead of submitting a whole form and reloading the page, we want the database to update the moment the user selects a new status from the dropdown.

```html
<form hx-post="/jobs/{{ job.id }}/status" hx-target="#job-{{ job.id }}" hx-swap="outerHTML">
    <select name="status" class="form-select form-select-sm" onchange="this.form.requestSubmit()">
        <option value="TO BE PRINTED" ...>TO BE PRINTED</option>
        <option value="PRINTED" ...>PRINTED</option>
    </select>
</form>
```

**How it works:**
- The small JS `onchange="this.form.requestSubmit()"` forces the form to submit whenever the `<select>` changes.
- HTMX intercepts the submission, serializes the `name="status"` value, and makes a `POST` request to `/jobs/123/status`.
- The FastAPI backend updates the database, re-renders the `job_row.html` template snippet with the *new* state, and returns it.
- HTMX takes that freshly rendered row and replaces the old row (`hx-swap="outerHTML"`).

---

## Example 3: Auto-Saving Text Notes

We want users to type material or timing notes and have them automatically save when they click away from the text box.

```html
<form hx-post="/jobs/{{ job.id }}/notes" hx-swap="outerHTML">
    <input type="text" name="material_notes" value="..." hx-trigger="blur">
</form>
```

**How it works:**
- The `hx-trigger="blur"` attribute overrides the default form submission. It tells HTMX: "Wait until the user leaves (blurs) this input field."
- When they leave, it posts the entire form (including the updated text) to the backend.
- The backend saves it. We don't even need to swap a new row here if we don't want to, so returning a simple success message or empty string works, depending on the `hx-swap` configuration.

## Backend Rule of Thumb

When writing FastAPI endpoints for HTMX:
1. If the action visually changes an element (like changing a status color), return the rendered Jinja2 template snippet (e.g., `job_row.html`) of the updated element.
2. If the action deletes an element, return an empty string `""` with `hx-swap="outerHTML"`.
3. You rarely need to return JSON or redirect the user!
