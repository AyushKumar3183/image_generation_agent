"""Rules for distinct variations when generating multiple images in one request."""

MULTI_IMAGE_VARIATION_RULES = """
MULTI-IMAGE VARIATION REQUIREMENTS (MANDATORY FOR BATCH GENERATION):

- Each image MUST be clearly different from every other image in the batch.
- Keep the EXACT SAME studio format for every image: front-facing, straight-on, full-length, centered.
- Do NOT change camera angle between images. No side view, no three-quarter angle, no profile.
- Vary ONLY within the same front-facing format: outfit color, fabric, embroidery pattern, border design,
  accessory styling, subtle hand pose, and fine garment details.
- Avoid near-duplicates, mirrored copies, or minimal tweaks between images.
""".strip()

MULTI_IMAGE_VARIATION_HINTS = [
    (
        "Image {image_index} of {total_images}: Front-facing full-length studio portrait. "
        "Create a distinct color palette and primary embroidery motif while keeping straight-on centered framing."
    ),
    (
        "Image {image_index} of {total_images}: Front-facing full-length studio portrait. "
        "Use a different border pattern, fabric texture, and accessory combination with the same straight-on format."
    ),
    (
        "Image {image_index} of {total_images}: Front-facing full-length studio portrait. "
        "Apply a unique decorative layout and styling accents while maintaining front-facing centered composition."
    ),
    (
        "Image {image_index} of {total_images}: Front-facing full-length studio portrait. "
        "Deliver a fresh outfit interpretation with distinct craftsmanship details and the same straight-on framing."
    ),
]


def format_multi_image_variation(*, image_index: int, total_images: int) -> str:
    """Return variation instructions for one image in a multi-image batch."""
    if total_images <= 1:
        return ""

    hint_index = min(image_index - 1, len(MULTI_IMAGE_VARIATION_HINTS) - 1)
    hint = MULTI_IMAGE_VARIATION_HINTS[hint_index].format(
        image_index=image_index,
        total_images=total_images,
    )
    return f"{MULTI_IMAGE_VARIATION_RULES}\n\nVARIATION DIRECTION:\n{hint}"
