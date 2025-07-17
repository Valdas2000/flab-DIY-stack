from PIL import Image, ImageDraw, ImageFont
from const import GENERIC_ERROR, GENERIC_OK, IMAGE_ROTATED_270

LABEL_PT = 16
WARNING_PT = 18
MARKER_PT = 22

def tr(text):
    """Auto-translation function placeholder"""
    # This would be replaced with actual translation logic
    return text

def em_height(size_pt, dpi):
    """
    Calculate em height for a given font size and DPI.
    """
    return int((size_pt * dpi[1] ) // 72 )

def create_color_target_tiff(cht_data, file_name, label, dpi=(72, 72)):
    """
    Create colour target TIFF file based on original cht values.

    Args:
        cht_data: dict with keys 'patch_dict', 'corner_ref', 'range_names'
        file_name: string - full path with filename and extension
        label: string - target name for bottom label
        dpi: tuple (dpi_x, dpi_y) - default (72, 72)
    """
    patch_dict = cht_data['patch_dict']
    corner_ref = cht_data['corner_ref']
    range_names = cht_data['range_names']

    # Scale factor for pixel conversion
    scale_factor = dpi[0] / 25.4  # from units to pixels

    # Calculate text space using proper typography
    text_space_points = _calculate_text_space_points()

    # Calculate bounding box from corner points
    bbox = _calculate_bounding_box(corner_ref)

    # Convert to pixels
    width_pixels = int(bbox['width'] * scale_factor)
    height_pixels = int(bbox['height'] * scale_factor + em_height(text_space_points, dpi))

    # Create image
    image = Image.new('RGB', (width_pixels, height_pixels), color='white')
    # image = Image.new('RGB', (3000, 1500), color='white')
    draw = ImageDraw.Draw(image)

    # Draw functional blocks with proper offsets
    _draw_target_patches(draw, patch_dict, scale_factor, dpi)
    _draw_patch_labels(draw, patch_dict, range_names, scale_factor, dpi)
    _draw_info_text(draw, label, width_pixels, height_pixels, dpi, text_space_points)

    # Save with correct DPI in header
    image.save(file_name,
               format='TIFF',
               dpi=dpi,
               compression='lzw')

    print(f"Demo target {width_pixels}x{height_pixels}  {dpi[0]}x{dpi[1]}dpi  saved: {file_name}")

def resize_tiff_to_96dpi(input_path, output_path=None, auto_rotate = False) -> int :
    """
    Resizes TIFF file DPI to 96 if current DPI is greater than 96

    Args:
        auto_rotate: rotate image (reserved for future use)
        input_path: path to the source TIFF file
        output_path: path for saving (if None, overwrites the original)
    """
    try:
        with Image.open(input_path) as img:
            # Get current DPI
            current_dpi = img.info.get('dpi', (72, 72))  # default 72 DPI

            # Take maximum value from horizontal and vertical DPI
            max_dpi = max(current_dpi[0], current_dpi[1])

            # If DPI is greater than 96, resize
            if max_dpi > 96:
                # Calculate scaling factor
                scale_factor = 96 / max_dpi

                # New dimensions
                new_width = int(img.width * scale_factor)
                new_height = int(img.height * scale_factor)

                # Resize with anti-aliasing
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Set new DPI
                resized_img.info['dpi'] = (96, 96)

                # Determine save path
                save_path = output_path if output_path else input_path


                # rotated_image = resized_img.transpose(Image.Transpose.ROTATE_270)  # No loss rotation
                # IMAGE_ROTATED_270

                resized_img.save(save_path, dpi=(96, 96))

            else:
                # If need to save to different location
                if output_path and output_path != input_path:
                    img.save(output_path)

        return GENERIC_OK
    except Exception as e:
        print(tr("Error processing {}: {}").format(input_path, e))
        return GENERIC_ERROR

def _calculate_text_space_points():
    """Calculate space needed for bottom text in points"""
    # 8pt text: 3 lines + interline spacing
    text_8pt_lines = 3
    text_8pt_size = WARNING_PT
    text_8pt_interline = WARNING_PT // 2

    # 10pt text: 2 lines + interline spacing
    text_10pt_lines = 3
    text_10pt_size = MARKER_PT
    text_10pt_interline = text_10pt_size // 2

    # Gap between blocks
    gap_between_blocks = 4

    # Total calculation
    space_8pt = text_8pt_lines * text_8pt_size + (text_8pt_lines - 1) * text_8pt_interline
    space_10pt = text_10pt_lines * text_10pt_size + (text_10pt_lines - 1) * text_10pt_interline

    return space_8pt + gap_between_blocks + space_10pt + WARNING_PT  # 10pt gap for the last line

def _calculate_bounding_box(points):
    """Calculate bounding box from list of [x, y] points"""
    all_x = [point[0] for point in points]
    all_y = [point[1] for point in points]

    return {
        'min_x': min(all_x),
        'max_x': max(all_x),
        'min_y': min(all_y),
        'max_y': max(all_y),
        'width': max(all_x) + min(all_x),   # width with white spaces
        'height': max(all_y) + min(all_y)   # height with white spaces
    }

def _draw_target_patches(draw, patch_dict, scale_factor, dpi):
    """
    Draw target patches on the image.

    Args:
        draw: PIL ImageDraw object
        patch_dict: Dictionary with patch data
        scale_factor: Scale factor for pixel conversion
    """
    for patch_name, patch_data in patch_dict.items():
        # Get center coordinates and dimensions
        center_x, center_y = patch_data['patch_xy']
        width, height = patch_data['patch_wh']

        # Convert to pixels with offset
        center_x_px = int((center_x) * scale_factor)
        center_y_px = int((center_y) * scale_factor)
        width_px = int(width * scale_factor)
        height_px = int(height * scale_factor)

        # Calculate rectangle coordinates (from center)
        x1 = center_x_px - width_px // 2
        y1 = center_y_px - height_px // 2
        x2 = center_x_px + width_px // 2
        y2 = center_y_px + height_px // 2

        cross = False
        # Extract color from packed RGB
        if patch_data['xyz']['X'] == -1:
            color = (255, 255, 255)  # white
            draw.rectangle([x1, y1, x2, y2], fill=color, outline=color)
            color = (255, 0, 0)  # white
            draw.line([x1, y1, x2, y2], fill=color, width=em_height(6,dpi))
            draw.line([x1, y2, x2, y1], fill=color, width=em_height(6,dpi))

        else:
            rgb_packed = patch_data['rgb']
            r = (rgb_packed >> 16) & 0xFF
            g = (rgb_packed >> 8) & 0xFF
            b = rgb_packed & 0xFF
            color = (r, g, b)
            draw.rectangle([x1, y1, x2, y2], fill=color, outline=color)

def _draw_patch_labels(draw, patch_dict, range_names, scale_factor, dpi):
    """
    Draw patch labels at corner positions.

    Args:
        draw: PIL ImageDraw object
        patch_dict:
        range_names: List of corner names
        scale_factor: Scale factor for pixel conversion
        dpi: DPI tuple (dpi_x, dpi_y)
    """
    # Load 8pt font
    font_8pt_size = None
    try:
        font_8pt_size = em_height(LABEL_PT, dpi)
        font_8pt = ImageFont.truetype("arial.ttf", font_8pt_size)
    except:
        font_8pt = ImageFont.load_default()

    # Draw labels for each corner
    for i, (corner_name) in enumerate(range_names):
        corner_x, corner_y = patch_dict[corner_name]['patch_xy']
        patch_w, patch_h = patch_dict[corner_name]['patch_wh']

        # Convert to pixels with offset
        x_px = int((corner_x - patch_w // 2) * scale_factor)
        y_px = int((corner_y - patch_h // 2) * scale_factor)

        # Position text based on corner (assuming order: top-left, top-right, bottom-right, bottom-left)
        if i < 2:  # top corners
            text_y = y_px - font_8pt_size - font_8pt_size // 2 # above corner
        else:  # bottom corners
            text_y = y_px + font_8pt_size + - font_8pt_size // 2 # below corner

        draw.text((x_px, text_y), corner_name, fill='black', font=font_8pt)

def _draw_info_text(draw, label, width_pixels, height_pixels, dpi, text_space_points):
    """
    Draw informational text at the bottom of the image.

    Args:
        draw: PIL ImageDraw object
        label: Target label string
        width_pixels: Image width in pixels
        height_pixels: Image height in pixels
        dpi: DPI tuple (dpi_x, dpi_y)
        text_space_points: Space allocated for text in points
    """
    # Load fonts
    try:
        font_8 = ImageFont.truetype("arial.ttf",  em_height(WARNING_PT, dpi))
        font_10 = ImageFont.truetype("arial.ttf", em_height(MARKER_PT, dpi))
        font_10_bold = ImageFont.truetype("arialbd.ttf", em_height(MARKER_PT, dpi))
    except:
        font_8 = ImageFont.load_default()
        font_10 = ImageFont.load_default()
        font_10_bold = ImageFont.load_default()

    font_8_size = em_height(WARNING_PT, dpi)
    font_10_size = em_height(WARNING_PT, dpi)

    # Text lines
    lines = [
       [font_10_bold, font_10_size, "PREVIEW ONLY. NOT FOR PRINT. NOT FOR COMMERCIAL USE"],
       [font_8,  font_8_size, "Generated via PatchReader - Educational/Research Tool"],
       [font_8,  font_8_size, "Part of flab-DIY-stack project github.com/Valdas2000/flab-DIY-stack"],
       [font_8,  font_8_size, "CC BY-NC 4.0 License"],
       [font_10, font_10_size, label]
    ]

    # Calculate text area start position
    text_space_pixels = em_height(text_space_points, dpi)
    start_y = height_pixels - text_space_pixels


    current_y = start_y

    # Draw 8pt text
    for font, line_heigh, line in lines:
        text_bbox = draw.textbbox((0, 0), line, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        x = (width_pixels - text_width) // 2  # center
        draw.text((x, current_y), line, fill="black", font=font)
        current_y += line_heigh * 1.5


# Usage
if __name__ == "__main__":
    # Example
    resize_tiff_to_96dpi('input.tiff', 'output.tiff')
