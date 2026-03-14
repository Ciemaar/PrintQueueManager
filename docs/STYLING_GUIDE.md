# Styling Guide: Pico CSS

Print Queue Manager uses [Pico CSS](https://picocss.com/) for its frontend styling.

If you are coming from frameworks like Bootstrap, Tailwind, or Bulma, you will notice a significant lack of utility classes in the HTML templates. This is entirely intentional!

## The Semantic HTML Approach

Pico CSS is a "classless" CSS framework. Instead of adding a dozen classes to every `<div>` to style a form or a card, Pico simply targets **semantic HTML tags**.

For example, to create a beautiful container with padding and a shadow, you don't write:
`<div class="card shadow rounded p-4">`

You simply write:
`<article>`

If you want a responsive grid container, you just write:
`<main class="container">`

### Common Patterns in this Project

- **Containers:** `<main class="container">` automatically centers content and sets max widths based on breakpoints.
- **Cards:** Wrap elements in `<article>` to give them a card-like appearance.
- **Tables:** Use `<table role="grid">` (or wrap a normal table in `<figure>`) to get a beautifully styled, responsive table.
- **Headers:** Use `<hgroup>` to group an `<h1>` and a `<p>` subtitle together cleanly.
- **Buttons:** A standard `<button>` tag will look great out of the box. Add the `secondary` or `outline` classes for variations (e.g., `<button class="secondary outline">`).

## Themes

Pico CSS comes with built-in Light and Dark themes.

By default, we set `<html data-theme="light">` in `index.html` to force the light theme. If you remove that attribute, Pico will automatically switch between light and dark themes based on the user's OS preference (`prefers-color-scheme`).

## Customizing

If you need to make specific tweaks, you can override Pico's CSS Variables in the `<style>` block. For example, in `index.html` we utilize the Pico colors directly to create a badge:

```css
.source-badge {
    background-color: var(--pico-primary-background);
    color: var(--pico-primary-inverse);
    padding: 0.25rem 0.5rem;
    border-radius: 1rem;
}
```

By sticking to semantic HTML and relying on Pico, we keep the Jinja2 templates incredibly clean and readable.
