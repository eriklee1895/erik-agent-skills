# Visible-marker editing with Seedream 5.5

Prefer natural-language targeting or prompt `<bbox>` / `<point>` tags when the intended region is clear. A visible marker can help identify ambiguous regions, but it changes the reference itself and may leave residue. It does not impose a hard pixel mask.

The editing contract also understands freehand arrows, circles and scribbles drawn yourself on the reference, not just the CLI's rectangles — describe each mark's meaning in the prompt and always end with an explicit “remove all marker lines/sketches” instruction. Marker leakage is the most common beginner failure: without the cleanup sentence, colored strokes tend to survive into the output. The CLI's auto-appended cleanup wording covers its own rectangles; self-drawn marks need the sentence in your own prompt.

```bash
uv run scripts/seedream_image_gen.py edit --reference-image poster.png \
  --marker-rect '5%,6%,90%,20%' \
  --prompt '只把红框内标题改成“新绿计划”。保持原位置、字体大小、对齐、全部小字、物体和背景不变，移除彩色标记，不重新排版。'
```

- `--marker-rect` is **x,y,width,height**, in pixels or percentages, rather than left/top/right/bottom. Rectangles are relative to the source image.
- Repeat `--marker-rect` and `--marker-color` for multiple targets. Assign each color a clear edit in the prompt.
- Markers annotate the first local reference. Additional references retain their upload order. Download remote inputs first if they need local annotation.
- The CLI saves an annotated reference and appends a cleanup instruction in the detected prompt language. `--no-marker-cleanup-prompt` leaves cleanup wording under explicit prompt control.
- `--marker-alpha` controls rectangle fill; inspect line/fill residue rather than assuming an opacity guarantees better edits. `--background transparent` preserves alpha during annotation.
- Inspect intended edits, original layout, protected areas and marker removal separately. If the result fails, return to the accepted unmarked image before another intentional attempt.

For fixed-layout artwork, explicitly retain position, scale, font size and whitespace. See [the measured 5.5 recipes](seedream55-workflows.md) and [benchmark](../evals/seedream55-benchmark.md) for the short-prompt failure and improved geometry constraints. Historical 5.0 marker ratings are retained under `../evals/history/` as provenance, not transferred to 5.5.
