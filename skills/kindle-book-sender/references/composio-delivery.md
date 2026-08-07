# Composio Kindle Delivery

## Before sending

- Confirm the Gmail connection is active and select the account whose primary address exactly matches the user's approved sender.
- Use the Kindle address only as the recipient. Do not add other recipients unless the user asks.
- Validate the attachment first with `scripts/verify_ebook.py`.
- Keep the attachment under 18 MB. Gmail's practical limit is about 25 MB after encoding.

## Preferred local-file route

When the Composio CLI and Gmail connection are available, the `--file` flag attaches a local file directly. It is preferable to first uploading a file through a remote workbench.

```bash
composio execute GMAIL_SEND_EMAIL \
  --account <approved-sender-account> \
  --file /absolute/path/book.epub \
  --dry-run \
  -d '{
    "recipient_email": "<kindle-address>",
    "subject": "<book title>",
    "body": "Lawfully obtained ebook for Kindle delivery."
  }'
```

Review the dry-run values. Then run the same command without `--dry-run`.

For a PDF conversion email, change the attachment extension and set the subject to exactly `convert`.

```bash
composio execute GMAIL_SEND_EMAIL \
  --account <approved-sender-account> \
  --file /absolute/path/book.pdf \
  -d '{
    "recipient_email": "<kindle-address>",
    "subject": "convert",
    "body": "Lawfully obtained PDF for Kindle conversion."
  }'
```

## Troubleshooting

- **Wrong sender:** Stop. Choose the correct connected Gmail account; do not send from a different account merely because it is connected.
- **Local file rejected:** Revalidate the file and try the standard/no-images EPUB. Do not rename a different file type to `.epub`.
- **Remote upload gets a pre-signed-URL authorization error:** Use the direct CLI `--file` route above rather than retrying the remote upload helper.
- **Attachment too large:** Find a lawful smaller/no-images edition, or ask the user to use Amazon's Send to Kindle web uploader. Do not split an EPUB or strip content without permission.
- **Email is marked sent but missing on Kindle:** Wait a few minutes, then have the user sync the Kindle and check their Kindle library. Verify that the sender remains on Amazon's approved list.
