# Feishu HTML5 block contract

Use a complete, UTF-8, single-file HTML document. Its `<head>` must include this contract before the file is embedded or updated:

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="use-iframe" content="true">
  <meta name="html-box-height-mode" content="auto">
  <meta name="description" content="A concise description of the block's reader-facing purpose">
  <title>Diagram title</title>
</head>
<body>
  ...
</body>
</html>
```

`description` is the accessible, reader-facing summary exported as the block's alt text; write it for someone who cannot inspect the rendering.

## Height and layout

Set `html-box-height-mode` to exactly one of these values:

- `auto` for content that should expand naturally in a document. Use normal document flow. Do not set a fixed height or `overflow: hidden` on the root container; put any intentionally scrollable fixed operation area inside the visual.
- `viewport` for a single-screen surface that deliberately uses `100vh` and internal scrolling, paging, or zooming, such as a dashboard, game, or canvas editor.

Content added or expanded after page load does not cause the embedding client to refresh the block height. Design `auto` mode so its initial document-flow height is sufficient; do not invent a writer flag to change that behaviour.

A document commonly offers about 820px of reading width, but it can be narrower. Give the root visual `width: 100%`, `max-width: 100%`, and `box-sizing: border-box`; test the content rather than assuming a desktop-wide canvas.

## Size, resources, and secrets

The entire HTML document must be at most 500 KiB. Do not spend that budget on inline large images, Base64 data, fonts, large JSON/CSV payloads, or extensive mock data.

External scripts, styles, fonts, images, data, and network calls may not be available in the embedded environment. They are an uncertainty to validate on the actual Feishu client, not an assumed capability. Prefer essential content that renders without them and disclose any retained dependency. Never place API keys, tokens, passwords, session material, signed private URLs, or other secrets in the HTML, its comments, or embedded data.

## XML write and readback

Save the HTML as a local file, then write the block in Docx XML with a workspace-relative `@./` path:

```xml
<html5-block path="@./widget.html"/>
```

When updating an existing block that has a `data-ref`, provide the writer's reference map for that existing reference as required by the document-writing capability. Do not substitute unsupported path syntaxes for `@./`.

On a document fetch, XML such as the following is only a placeholder:

```xml
<html5-block data-ref="html5_1"></html5-block>
```

Read the actual HTML from `document.reference_map["html5-block"]["html5_1"].data`. If that entry instead supplies a `path`, read the corresponding file under the fetch resources directory (for example, `@./doc-fetch-resources/...html`). Compare the recovered content with the intended artifact before calling the write valid.
