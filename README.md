# Kindle Book Sender

Give your AI agent a book title and this skill helps it find a **lawfully available** copy, prepare it for Kindle, and send it to your Kindle library.

It prefers EPUB files. When only a lawful PDF is available, it can use Amazon's `convert` email subject to turn the PDF into a Kindle-friendly document.

## Install in Codex

The easiest route is to paste this into Codex:

> Install the skill from https://github.com/aiwithremy/kindle-book-sender/tree/main/skills/kindle-book-sender

Or run this in a terminal with Codex installed:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo aiwithremy/kindle-book-sender \
  --path skills/kindle-book-sender
```

After installation, start a new Codex message and say:

> Use $kindle-book-sender to find and send The Count of Monte Cristo to my Kindle.

Prefer a manual install? [Download the ZIP](https://github.com/aiwithremy/kindle-book-sender/archive/refs/heads/main.zip), then place `skills/kindle-book-sender` inside your Codex skills folder.

## What it does

- Finds only public-domain, openly licensed, publisher-authorized, or user-provided files.
- Asks for your Send-to-Kindle email address and the email address Amazon has approved to send from.
- Verifies EPUB and PDF files before delivery.
- Prefers EPUB for adjustable text; uses `convert` for lawful PDF fallback.
- Checks a manual PDF-to-EPUB conversion before sending it.

## Before you use it

In Amazon, open **Manage Your Content and Devices -> Preferences -> Personal Document Settings**. There you can find your Send-to-Kindle email address and add an approved sender under **Approved Personal Document E-mail List**.

This skill does not find or distribute pirated books, remove DRM, or export library-loan files.

## Requirements

You need a Kindle account with Send to Kindle enabled and an AI-agent email connection that can send from an address approved by Amazon. Composio is supported when available, but it is not required.

## License

[MIT](LICENSE)
