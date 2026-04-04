# Tool Evaluation

## Playwright

### Pros
- Supports multiple browsers.
- Fully supports JavaScript execution and modern web pages.
- Highly reliable for waiting on elements to load (auto-waiting).
- Robust handling of complex user interactions like clicks, scrolling, forms.
- Provides screenshots and video recording for debugging.
- Bypasses basic bot-detection techniques if configured correctly.

### Cons
- High resource usage (CPU and Memory).
- Downloading browser binaries significantly increases Docker image sizes.
- Hard to deploy in restrictive environments due to dependencies (`install-deps`).

## Alternatives

### Requests + BeautifulSoup
- **Pros:** Fast, lightweight, very low resource usage, minimal dependencies.
- **Cons:** Cannot execute JavaScript. Will not work on SPAs or sites heavily reliant on client-side rendering. Can't bypass Cloudflare/JS-challenges easily.

### Selenium
- **Pros:** Long-standing industry standard, huge community.
- **Cons:** Slower, more setup required (WebDriver management), less reliable auto-waiting than Playwright.

### Puppeteer
- **Pros:** Native Chrome support, slightly smaller footprint than full Playwright if only using Chrome.
- **Cons:** Primarily Node.js (Pyppeteer exists but is less maintained than Playwright Python). Doesn't officially support Firefox/WebKit as cleanly as Playwright.

## Conclusion

Given the nature of the sites being scraped (MyMiniFactory, MakerWorld, Printables, etc.), which often require complex authentication or JS execution, **Playwright is the necessary tool**. The overhead of the browser binaries is justified by the requirement to execute client-side code and manage session cookies reliably. The alternatives either cannot render JS (BeautifulSoup) or offer a worse developer experience (Selenium).
