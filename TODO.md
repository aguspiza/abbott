# TODO

## Fetch Jenkins log automatically from URL

The submit form currently has two fields: **Build URL** and **Jenkins log**.

The URL is used today only to extract the job name for display. The log is
always required because Abbott has no way to reach Jenkins without credentials.

**Future plan:** when Jenkins credentials are configured (URL + API token in
`abbott.toml` or `.env`), Abbott should fetch the console log directly from the
Build URL and make the paste field optional. The form should degrade gracefully:
if credentials are absent, keep requiring the pasted log.

This means both fields stay in the form — the URL becomes the primary input
once Jenkins access is wired up.
