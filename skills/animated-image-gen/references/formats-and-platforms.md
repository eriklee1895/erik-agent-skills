# WebP and GIF delivery

The skill delivers animated WebP and GIF. Complete RGBA PNG frames remain the master source for local revisions and alternate exports.

## Select an encoding

WebP supports 24-bit RGB, 8-bit alpha and lossy or lossless animation. Photographic samples can benefit from lossy encoding. Precise diagrams and text often suit lossless encoding. Compare file size and visible quality for the actual material. [Google WebP FAQ](https://developers.google.com/speed/webp/faq)

GIF uses a shared palette in this helper. Its transparency is binary, so inspect fine edges and semi-transparent effects after export. The helper records the actual decoded frames, durations, total plays, transparent pixels and file size.

The measured four-source comparison is in [format results](../evals/format-results.json). Lossless WebP matched visible source pixels and alpha. A photo-scene q80 example fell from 1103691 to 146930 bytes. A fixed 1280×720 diagram was 93527 bytes as GIF, 91130 as lossless WebP and 173390 as q80 WebP. These values describe those files at those settings.

## Check the destination

Modern browsers support animated WebP broadly. For a blog, check the actual resource after upload, resizing, image-CDN processing and publication. [MDN image formats](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Image_types)

Notion's official help lists WEBP as a supported file type. Preservation of animation, duration and repeats requires target-page inspection. A user report describes truncated animated-WebP duration. The initial auto policy therefore uses GIF for a Notion destination, while an explicit WebP choice remains available.[Notion media support](https://www.notion.com/help/images-files-and-media) · [Firsthand problem report](https://www.reddit.com/r/Notion/comments/1vaqmhe/does_notion_not_support_webp/)

Client and server image-processing paths can have different animation behavior, including sub-size generation. Verify the published resource used by the specific site.[WordPress media processing](https://developer.wordpress.org/block-editor/explanations/architecture/client-side-media-architecture/)
