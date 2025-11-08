"""Create dark theme icon variants for the Eltako ESR62PF-IP integration."""

from PIL import Image, ImageDraw

def create_dark_icon(size: int, output_path: str) -> None:
    """Create a dark theme icon optimized for dark backgrounds.

    Args:
        size: Size of the icon (width and height in pixels)
        output_path: Path where the icon should be saved
    """
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Use a lighter blue that works well on dark backgrounds
    # The original is #0066CC, we'll use a lighter shade for dark mode
    light_blue = (102, 153, 255, 255)  # #6699FF - lighter, more visible on dark

    # Calculate dimensions (same proportions as original)
    center = size // 2
    radius = int(size * 0.45)  # Circle radius

    # Draw circle background with light blue
    draw.ellipse(
        [center - radius, center - radius, center + radius, center + radius],
        fill=light_blue
    )

    # Draw the white symbol (two connected module shapes)
    symbol_width = int(size * 0.6)
    symbol_height = int(size * 0.35)
    symbol_x = (size - symbol_width) // 2
    symbol_y = (size - symbol_height) // 2

    white = (255, 255, 255, 255)

    # Left module (rounded top)
    left_module_width = int(symbol_width * 0.4)
    left_module_height = symbol_height

    # Right module (rounded top)
    right_module_width = int(symbol_width * 0.4)
    right_module_height = symbol_height

    # Connection beam in the middle
    beam_width = int(symbol_width * 0.2)
    beam_height = int(symbol_height * 0.3)

    # Draw left module with rounded top
    left_x = symbol_x
    left_y = symbol_y
    # Bottom rectangle
    draw.rectangle(
        [left_x, left_y + left_module_height // 3,
         left_x + left_module_width, left_y + left_module_height],
        fill=white
    )
    # Top rounded part
    draw.ellipse(
        [left_x, left_y,
         left_x + left_module_width, left_y + left_module_height // 2],
        fill=white
    )

    # Draw right module with rounded top
    right_x = symbol_x + symbol_width - right_module_width
    right_y = symbol_y
    # Bottom rectangle
    draw.rectangle(
        [right_x, right_y + right_module_height // 3,
         right_x + right_module_width, right_y + right_module_height],
        fill=white
    )
    # Top rounded part
    draw.ellipse(
        [right_x, right_y,
         right_x + right_module_width, right_y + right_module_height // 2],
        fill=white
    )

    # Draw connection beam (slightly angled)
    beam_x = symbol_x + left_module_width
    beam_y = symbol_y + (symbol_height - beam_height) // 2

    # Create a polygon for the angled beam
    points = [
        (beam_x, beam_y + beam_height // 4),
        (beam_x + beam_width, beam_y),
        (beam_x + beam_width, beam_y + beam_height),
        (beam_x, beam_y + 3 * beam_height // 4)
    ]
    draw.polygon(points, fill=white)

    # Save with optimization
    img.save(output_path, 'PNG', optimize=True)
    print(f"Created {output_path} ({size}x{size})")


if __name__ == '__main__':
    import os

    # Create icons in the integration directory
    integration_dir = 'custom_components/eltako_esr62pf'

    # Create both sizes
    create_dark_icon(256, os.path.join(integration_dir, 'dark_icon.png'))
    create_dark_icon(512, os.path.join(integration_dir, 'dark_icon@2x.png'))

    print("\nDark theme icons created successfully!")
    print("The icons use a lighter blue (#6699FF) that is more visible on dark backgrounds.")
