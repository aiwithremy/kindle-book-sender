---
name: kindle-book-sender
description: Find a lawfully available ebook and send it to a user's Kindle. Use when a user names a book and wants it found, downloaded, converted, or emailed to a Kindle; when preparing a legal EPUB or PDF for Send to Kindle; or when troubleshooting a Kindle delivery email.
---

# Kindle Book Sender

Find and deliver only books the user may lawfully receive. Prefer a clean EPUB; use a PDF with Amazon's `convert` email subject only when an EPUB is unavailable or unsuitable.

## Inputs and permissions

Ask for these before downloading a file or sending an email:

1. The book title, author if ambiguous, and preferred language/edition.
2. The Kindle Send-to-Kindle address.
3. The email address Amazon has approved as a sender.

If the user does not know either address, explain how to find them in Amazon: **Manage Your Content and Devices -> Preferences -> Personal Document Settings**. The Send-to-Kindle address is under **Send-to-Kindle E-Mail Settings**; the approved senders are under **Approved Personal Document E-mail List**. Ask the user to paste both values rather than guessing.

Treat sending an email as an external write. Confirm the recipient, source file, subject, and sender account immediately before sending unless the user has already clearly authorized those exact details.

## Legal-source gate

Search for an authorized copy first. Accept public-domain, openly licensed, publisher-authorized free downloads, or a file the user owns and supplies. Prefer primary sources such as Project Gutenberg, Standard Ebooks, an author/publisher site, or the library/retailer itself.

Do not scrape, download, convert, or email a pirated copy, a DRM-protected library/retailer file, or a file whose authorization is unclear. For a copyrighted book without a legal free download, offer the library, Kindle store, publisher, or other official route instead. A library loan is not permission to export its ebook file.

## Kindle quality gate

Before emailing **any EPUB**—including a publisher download, a conversion, or a collection built from web pages—run:

```bash
python3 scripts/verify_ebook.py /absolute/path/book.epub
```

Treat a failed check as a hard stop; repair the EPUB and rerun validation before delivery.

- **Cover:** Require an embedded PNG or JPEG cover image. An SVG-only cover is not acceptable because Kindle can show a generic thumbnail instead. If the book has no acceptable cover, create and embed a simple 1600×2560 PNG title card with:

  ```bash
  python3 scripts/add_epub_cover.py /absolute/path/book.epub --output /absolute/path/book-with-cover.epub --title "Book title" --author "Author"
  ```

  Then validate the new file before delivery.
- **Reading layout:** Require full-width, reflowable prose. Remove imported web-page shells, spacer tables, `width` attributes, and fixed-pixel CSS from article containers before conversion. In particular, never retain narrow legacy layout tables such as `width="435"` around body text.
- **Visual release check:** Inspect the cover and a representative early, middle, and final chapter in Kindle Previewer when available. Confirm the cover title is legible, the prose occupies the normal reading width, headings start each chapter, and there is no clipping, horizontal scrolling, or narrow vertical text column. Do not send an EPUB merely because the ZIP opens.

1. Search for an authorized **EPUB**. Prefer a standard, reflowable edition when images add unnecessary size.
2. Download it to a temporary directory. Keep attachments below 18 MB before email encoding. Verify the file:

   ```bash
   python3 scripts/verify_ebook.py /absolute/path/book.epub
   ```

3. If the EPUB has no acceptable cover, add the required PNG title card and set it as the EPUB cover, then validate again.
4. If validation passes, email the EPUB as an attachment. Use the book title as the subject; do **not** use `convert` for EPUB.
5. If no suitable EPUB exists but there is a lawful **PDF**, validate the PDF and email it with the subject exactly:

   ```text
   convert
   ```

   Amazon's email conversion service converts a PDF to a Kindle-friendly document. This works best for simple, text-led PDFs; preserve the source PDF as the fallback because complex layouts can convert poorly.
6. If the PDF conversion route is unsuitable or fails, manually convert only a lawful, non-DRM PDF. Use Calibre's `ebook-convert`, then validate the EPUB and visually inspect a representative conversion before delivery:

   ```bash
   ebook-convert /absolute/path/book.pdf /absolute/path/book.epub
   python3 scripts/verify_ebook.py /absolute/path/book.epub
   ebook-convert /absolute/path/book.epub /tmp/kindle-preview.pdf
   pdftoppm -f 1 -l 3 -png /tmp/kindle-preview.pdf /tmp/kindle-preview
   ```

   Inspect the rendered pages for missing text, bad chapter breaks, clipping, or garbled characters. Do not claim a manual conversion is good without this check.
   If `ebook-convert` is unavailable, do not install a converter or invent an EPUB; offer the PDF-with-`convert` route instead.
7. Send through an account whose primary address exactly matches the approved sender. Verify the send result shows it was sent, but say Kindle delivery may take a few minutes; do not claim the Kindle received it unless there is evidence.

## Email delivery

Read [references/composio-delivery.md](references/composio-delivery.md) before sending through Composio. Use its direct local-file attachment route when available. It avoids fragile intermediary upload steps.

Never expose private Kindle addresses, approved sender addresses, tokens, or raw mail IDs in normal status updates.

## Completion report

Report the title, source, format, sender, and whether the email was successfully sent. State which route was used: EPUB, PDF with `convert`, or manually converted EPUB. If blocked, name the exact missing authorization or source issue and the smallest next action.
