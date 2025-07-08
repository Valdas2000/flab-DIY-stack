import numpy as np
import re
import copy

def parse_cht_file(file_path):
    """
    The main function to parse the file

    Function for parsing CHT file.

    Args:
        file_path: Path to CHT file

    Returns:
        Dictionary with data from CHT file, containing:
        - main_grid: main grid with patch centers
        #- exclusion_grid: exclusion grid
        - patch_dict: dictionary of patches with XYZ, coordinates and analysis results
        - patch_size: patch size
        - reference_grid: grid reference points (from F-lines)
    """
    # Dictionaries for storing data from CHT file
    sections = {}
    current_section = None
    section_content = []

    # List of known sections (headers)
    known_sections = ['XLIST', 'YLIST', 'BOXES', 'X', 'BOX_SHRINK', 'REF_ROTATION', 'EXPECTED', 'D', 'F']

    # Reading CHT file
    with open(file_path, 'r') as file:
        for line_num, line in enumerate(file, 1):
            original_line = line
            line = line.strip()
            if not line:
                continue

            # Check if line is section header
            # (doesn't start with space/tab and first word contains only uppercase letters)
            if not original_line.startswith(' ') and not original_line.startswith('\t'):
                parts = line.split()
                if parts and parts[0].isupper() and parts[0].isalpha():
                    # This looks like section header
                    # Save previous section if it exists
                    if current_section:
                        sections[current_section] = section_content

                    # Set new section
                    current_section = parts[0]
                    section_content = []

                elif current_section:
                    # This is not header, but content of current section
                    section_content.append(line)

            elif current_section:
                # This is content of current section (with indent)
                section_content.append(line)

    # Add last section
    if current_section:
        sections[current_section] = section_content

    # Processing various CHT file sections
    xlist = parse_xlist(sections.get('XLIST', []))
    ylist = parse_ylist(sections.get('YLIST', []))
    box_shrink = parse_box_shrink(sections.get('BOX_SHRINK', []))
    xyz_dict = parse_expected_xyz(sections.get('EXPECTED', []))
    boxes_data = parse_boxes(sections.get('BOXES', []))

    # Creating main grid and exclusion grid
    main_grid, exclusion_grid = create_grids(xlist, ylist, boxes_data)

    # Determining patch size
    patch_size = calculate_patch_size(boxes_data)

    # Creating patch dictionary
    patch_dict = create_patch_dictionary(xyz_dict, main_grid, boxes_data)

    # Creating reference grid from F-lines
    reference_grid = extract_reference_grid(boxes_data['F'])

    range_name = get_x_range_string(patch_dict, main_grid)

    return {
        'main_grid': main_grid,
        # 'exclusion_grid': exclusion_grid,
        'patch_dict': patch_dict,
        'patch_size': patch_size,
        'reference_grid': reference_grid,
        'range_name': range_name
    }

def extract_reference_grid(f_entries):
    """
    Extract grid reference points from F-lines.
    Determines extreme points based on all corners from F-lines.

    Args:
        f_entries: List of F-lines from BOXES section

    Returns:
        Dictionary with grid corner coordinates in format
        {'top_left': (x, y), 'top_right': (x, y), 'bottom_left': (x, y), 'bottom_right': (x, y)}
    """
    if not f_entries:
        return None

    # Collect all corner coordinates
    all_x = []
    all_y = []

    for entry in f_entries:
        if 'corners' in entry:
            corners = entry['corners']
            # Add all X-coordinates
            all_x.extend([corners[0], corners[2], corners[4], corners[6]])
            # Add all Y-coordinates
            all_y.extend([corners[1], corners[3], corners[5], corners[7]])

    if not all_x or not all_y:
        return None

    # Find extreme points
    min_x = min(all_x)
    max_x = max(all_x)
    min_y = min(all_y)
    max_y = max(all_y)

    # Create dictionary with extreme points
    reference_grid = {
        'top_left': (min_x, min_y),
        'top_right': (max_x, min_y),
        'bottom_left': (min_x, max_y),
        'bottom_right': (max_x, max_y)
    }

    return reference_grid

def parse_xlist(xlist_content):
    """
    Parse XLIST section.

    Each line in XLIST contains three values: position (x0), visibility (v0) and normalized value (s0).
    Function extracts only positions.

    Args:
        xlist_content: XLIST section content

    Returns:
        List of X-axis coordinates
    """
    xlist = []
    for line in xlist_content:
        parts = line.split()
        if parts:
            try:
                # Take only first value (position)
                x = float(parts[0])
                xlist.append(x)
            except (ValueError, IndexError):
                continue
    return xlist

def parse_ylist(ylist_content):
    """
    Parse YLIST section.

    Each line in YLIST contains three values: position (y0), visibility (v0) and normalized value (s0).
    Function extracts only positions.

    Args:
        ylist_content: YLIST section content

    Returns:
        List of Y-axis coordinates
    """
    ylist = []
    for line in ylist_content:
        parts = line.split()
        if parts:
            try:
                # Take only first value (position)
                y = float(parts[0])
                ylist.append(y)
            except (ValueError, IndexError):
                continue
    return ylist

def parse_box_shrink(box_shrink_content):
    """
    Parse BOX_SHRINK section.

    Args:
        box_shrink_content: BOX_SHRINK section content

    Returns:
        BOX_SHRINK value or None if section is missing
    """
    if box_shrink_content:
        try:
            return float(box_shrink_content[0])
        except (ValueError, IndexError):
            pass
    return None

def parse_expected_xyz(expected_content):
    """
    Parse EXPECTED XYZ section.

    Args:
        expected_content: EXPECTED XYZ section content

    Returns:
        Dictionary with XYZ values for each patch
    """
    xyz_dict = {}
    pattern = r'(\w+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)'

    for line in expected_content:
        match = re.match(pattern, line)
        if match:
            patch_id, x, y, z = match.groups()
            xyz_dict[patch_id] = {
                'X': float(x),
                'Y': float(y),
                'Z': float(z)
            }

    return xyz_dict

def parse_boxes(boxes_content):
    """
    Parse BOXES section.

    Processes lines of various formats:
    - F _ _ x0 y0 x1 y1 x2 y2 x3 y3 - coordinates of 4 patch corners
    - D MARK0 MARK0 _ _ w h cx cy 0 0 - markers for binding
    - X A1 A1 _ _ w h cx cy 0 0 - patches with dimensions and coordinates

    Args:
        boxes_content: BOXES section content

    Returns:
        Dictionary with patch data (F, D and X lines)
    """
    boxes_data = {
        'F': [],  # Lines with patch geometry
        'D': [],  # Lines with description and markers
        'X': []  # Lines with patches
    }

    for line in boxes_content:
        parts = line.split()
        if not parts:
            continue

        line_type = parts[0]
        if line_type == 'F':
            # Parse F line with corner coordinates
            # F _ _ x0 y0 x1 y1 x2 y2 x3 y3
            if len(parts) >= 11:  # Correct length check
                try:
                    # If coordinates start from index 3 and there are 8 of them
                    corners = [float(val) for val in parts[3:11]]

                    # Check that we got exactly 8 coordinates
                    if len(corners) == 8:
                        boxes_data['F'].append({
                            'corners': corners,  # [x0, y0, x1, y1, x2, y2, x3, y3]
                            # Safer width and height calculation, considering corners can be in any order
                            'width': max(abs(corners[2] - corners[0]), abs(corners[6] - corners[4])),
                            'height': max(abs(corners[3] - corners[1]), abs(corners[7] - corners[5]))
                        })
                except ValueError:
                    continue

        elif line_type == 'D':
            # Parse D line with marker
            # D MARK0 MARK0 _ _ w h cx cy 0 0
            if len(parts) >= 10:
                try:
                    boxes_data['D'].append({
                        'name': parts[1],
                        'width': float(parts[5]),
                        'height': float(parts[6]),
                        'center_x': float(parts[7]),
                        'center_y': float(parts[8])
                    })
                except ValueError:
                    continue
        elif line_type == 'X':
            # Parse X line with patch
            # X A1 A1 _ _ w h cx cy 0 0
            if len(parts) >= 10:  # Check for all required fields
                try:
                    boxes_data['X'].append({
                        'id': parts[1],
                        'duplicate_id': parts[2],  # Second identifier (usually matches first)
                        'width': float(parts[5]),
                        'height': float(parts[6]),
                        'center_x': float(parts[7]),
                        'center_y': float(parts[8])
                    })
                except ValueError:
                    continue

    return boxes_data

def calculate_patch_size(boxes_data):
    """
    Determine patch size as smallest width and height values from X lines.

    Args:
        boxes_data: Patch data from BOXES section

    Returns:
        Patch size
    """
    if not boxes_data['X']:
        return 20  # Default value

    # Find minimum width and height among all X patches
    min_width = min(x['width'] for x in boxes_data['X'] if 'width' in x)
    min_height = min(x['height'] for x in boxes_data['X'] if 'height' in x)

    # Return smallest value
    return min_width, min_height

def create_grids(xlist, ylist, boxes_data):
    """
    Create main grid and exclusion grid.
    """

    def is_close(a, b, tolerance=1e-6):
        return abs(a - b) < tolerance

    # Center coordinates from X lines
    center_x_coords = [x['center_x'] for x in boxes_data['X']]
    center_y_coords = [x['center_y'] for x in boxes_data['X']]

    # Create main grid - only coordinates that are close to those found in X lines
    main_grid_x = []
    exclusion_grid_x = []
    for x in xlist:
        if any(is_close(x, cx) for cx in center_x_coords):
            main_grid_x.append(x)
        else:
            exclusion_grid_x.append(x)

    main_grid_y = []
    exclusion_grid_y = []
    for y in ylist:
        if any(is_close(y, cy) for cy in center_y_coords):
            main_grid_y.append(y)
        else:
            exclusion_grid_y.append(y)

    return {
        'x': sorted(main_grid_x),
        'y': sorted(main_grid_y)
    }, {
        'x': sorted(exclusion_grid_x),
        'y': sorted(exclusion_grid_y)
    }

def create_patch_dictionary(xyz_dict, main_grid, boxes_data):
    """
    Create patch dictionary with XYZ, coordinates and analysis results.

    Args:
        xyz_dict: Dictionary with XYZ values for each patch
        main_grid: Main grid with patch centers
        boxes_data: Patch data from BOXES section

    Returns:
        Patch dictionary
    """
    patch_dict = {}

    # Match patch centers with grid cells
    for x_entry in boxes_data['X']:
        patch_id = x_entry['id']
        center_x = x_entry['center_x']
        center_y = x_entry['center_y']

        # Find nearest indices in grid
        x_idx = find_nearest_index(main_grid['x'], center_x)
        y_idx = find_nearest_index(main_grid['y'], center_y)

        # Create patch entry
        patch_dict[patch_id] = {
            'grid_idx': (x_idx, y_idx),  # Indices in main_grid instead of coordinates
            'xyz': xyz_dict.get(patch_id, {'X': 0, 'Y': 0, 'Z': 0}),
            'analysis_result': None, # Placeholder for analyze_patch results
            'array_idx': 0 # placeholder for position in linear list
        }

    return patch_dict


def get_x_range_string(patch_dict, main_grid):
    """Get X range string by finding patches at first and last column indices."""
    if not patch_dict:
        return ""

    import re

    # Find any patch with first column (index 0) and last column (len(x)-1)
    first_col_patch = next((name for name, data in patch_dict.items()
                            if data['grid_idx'][0] == 0), None)
    last_col_patch = next((name for name, data in patch_dict.items()
                           if data['grid_idx'][0] == len(main_grid['x']) - 1), None)

    if not first_col_patch or not last_col_patch:
        return ""

    # Extract letter parts
    first_letter = re.match(r'^([A-Z]+)', first_col_patch).group(1)
    last_letter = re.match(r'^([A-Z]+)', last_col_patch).group(1)

    return f"{first_letter}-{last_letter}" if first_letter != last_letter else first_letter


def find_nearest_index(array, value):
    """
    Find index of nearest value in array.

    Args:
        array: Sorted array of values
        value: Value to search for

    Returns:
        Index of nearest value
    """
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx

def get_patch_center(patch_id, patch_dict, main_grid):
    """
    Get patch center coordinates.

    Args:
        patch_id: Patch identifier
        patch_dict: Patch dictionary
        main_grid: Main grid with patch centers

    Returns:
        (x, y) - patch center coordinates
    """
    if patch_id not in patch_dict:
        return None

    x_idx, y_idx = patch_dict[patch_id]['grid_idx']
    center_x = main_grid['x'][x_idx]
    center_y = main_grid['y'][y_idx]

    return (center_x, center_y)

def convert_cht_to_pixels(cht_data, image_width, image_height, dpi):
    """
    Convert all coordinates from CHT file to pixel coordinates of image.

    Parameters:
    - cht_data: data from CHT file (contains main_grid, exclusion_grid, reference_grid and other elements)
    - image_width: image width in pixels
    - image_height: image height in pixels
    - dpi: image resolution (dots per inch)

    Returns:
    - cht_data: original structure with recalculated coordinates in pixels
    """
    # Conversion factor: pixels = mm × dpi / 25.4
    scale_factor = dpi / 25.4

    if 1:
        x_offset = cht_data['patch_size'][0]/2.
        y_offset = cht_data['patch_size'][1]/2.
        for i in range(len(cht_data['main_grid']['x'])):
            cht_data['main_grid']['x'][i] += x_offset

        for i in range(len(cht_data['main_grid']['y'])):
            cht_data['main_grid']['y'][i] += y_offset

        ref_grid = cht_data['reference_grid']

        # Update each corner
        ref_grid['top_left'] = (ref_grid['top_left'][0] + x_offset, ref_grid['top_left'][1] + y_offset)
        ref_grid['top_right'] = (ref_grid['top_right'][0] + x_offset, ref_grid['top_right'][1] + y_offset)
        ref_grid['bottom_left'] = (ref_grid['bottom_left'][0] + x_offset, ref_grid['bottom_left'][1] + y_offset)
        ref_grid['bottom_right'] = (ref_grid['bottom_right'][0] + x_offset, ref_grid['bottom_right'][1] + y_offset)

    # Determine extreme points of main grid
    min_x = min(cht_data['main_grid']['x'])
    max_x = max(cht_data['main_grid']['x'])
    min_y = min(cht_data['main_grid']['y'])
    max_y = max(cht_data['main_grid']['y'])

    # Convert to pixels
    min_x_px = min_x * scale_factor
    max_x_px = max_x * scale_factor
    min_y_px = min_y * scale_factor
    max_y_px = max_y * scale_factor

    # Check if grid exceeds image boundaries
    is_out_of_bounds = max_x_px > image_width or max_y_px > image_height
    resize_scale = 1

    if is_out_of_bounds:
        # Calculate scaling factor to fit into image
        padding = 10
        scale_x = (image_width - 2 * padding) / max_x_px
        scale_y = (image_height - 2 * padding) / max_y_px
        resize_scale = min(scale_x, scale_y)

        # Update reference_grid with padding
        cht_data['reference_grid']['top_left'] = (padding, padding)
        cht_data['reference_grid']['top_right'] = (image_width - padding, padding)
        cht_data['reference_grid']['bottom_left'] = (padding, image_height - padding)
        cht_data['reference_grid']['bottom_right'] = (image_width - padding, image_height - padding)

        # Calculate proportional scale for all coordinates
        original_width = max_x_px - min_x_px
        original_height = max_y_px - min_y_px
        new_width = image_width - 2 * padding
        new_height = image_height - 2 * padding

        # Recalculate coordinates of both grids with new scale
        for grid_name in ['main_grid', 'exclusion_grid']:
            if grid_name in cht_data:
                # Recalculate X coordinates
                old_x = [x * scale_factor for x in cht_data[grid_name]['x']]
                cht_data[grid_name]['x'] = [(x - min_x_px) * new_width / original_width + padding for x in old_x]

                # Recalculate Y coordinates
                old_y = [y * scale_factor for y in cht_data[grid_name]['y']]
                cht_data[grid_name]['y'] = [(y - min_y_px) * new_height / original_height + padding for y in old_y]
    else:
        # Direct recalculation, just multiply by scale_factor
        cht_data['reference_grid']['top_left'] = (min_x_px, min_y_px)
        cht_data['reference_grid']['top_right'] = (max_x_px, min_y_px)
        cht_data['reference_grid']['bottom_left'] = (min_x_px, max_y_px)
        cht_data['reference_grid']['bottom_right'] = (max_x_px, max_y_px)

        # Recalculate coordinates of both grids directly
        for grid_name in ['main_grid', 'exclusion_grid']:
            if grid_name in cht_data:
                cht_data[grid_name]['x'] = [x * scale_factor for x in cht_data[grid_name]['x']]
                cht_data[grid_name]['y'] = [y * scale_factor for y in cht_data[grid_name]['y']]

    # If patch_size field exists, scale it too
    if 'patch_size' in cht_data:
        if is_out_of_bounds:
            # Scale with resize_scale
            cht_data['patch_size'] = ( cht_data['patch_size'][0] * scale_factor * resize_scale,
                                       cht_data['patch_size'][1] * scale_factor * resize_scale)
        else:
            # Direct scaling
            cht_data['patch_size'] = (cht_data['patch_size'][0] * scale_factor,
                                      cht_data['patch_size'][1] * scale_factor)

    reverse_map = {}
    for name, data in cht_data['patch_dict'].items():
        i, j = data['grid_idx']
        x = cht_data['main_grid']['x'][i]
        y = cht_data['main_grid']['y'][j]
        reverse_map[(x, y)] = name

    sorted_keys = sorted(reverse_map.keys(), key=lambda xy: (xy[1], xy[0]))

    grid_linear = []
    parametric_uv = []

    x_min, x_max = cht_data['main_grid']['x'][0], cht_data['main_grid']['x'][-1]
    y_min, y_max = cht_data['main_grid']['y'][0], cht_data['main_grid']['y'][-1]

    for idx, (x, y) in enumerate(sorted_keys):
        name = reverse_map[(x, y)]

        # Save linear coordinate
        grid_linear.append((x, y))

        # Normalized UV
        u = (x - x_min) / (x_max - x_min) if x_max > x_min else 0
        v = (y - y_min) / (y_max - y_min) if y_max > y_min else 0
        parametric_uv.append((u, v))

        # Write index and uv to patch_dict
        cht_data['patch_dict'][name]['array_idx'] = idx

    cht_data['grid_linear'] = copy.deepcopy(grid_linear)
    cht_data['grid_linear_ref'] = copy.deepcopy(grid_linear)
    cht_data['reference_grid_ref'] = copy.deepcopy(cht_data['reference_grid'])

    cht_data['parametric_uv'] = parametric_uv
    cht_data['patch_scale'] = 100 # recognition area size
    del cht_data['main_grid']

    for patch_name, patch_data in cht_data['patch_dict'].items():
        patch_data.pop('grid_idx', None)  # Remove if exists, otherwise do nothing

    return cht_data

#    cht_data = {
#        'main_grid': {
#            'x': List[float],     # sorted grid coordinates by X
#            'y': List[float],     # sorted grid coordinates by Y
#        },
#        'exclusion_grid': {
#            'x': List[float],     # coordinates excluded from main grid by X
#            'y': List[float],     # coordinates excluded from main grid by Y
#        },
#        'reference_grid': {
#            'top_left': Tuple[float, float],
#            'top_right': Tuple[float, float],
#            'bottom_left': Tuple[float, float],
#            'bottom_right': Tuple[float, float],
#        },
#        'reference_grid_ref': {
#            'top_left': Tuple[float, float],
#            'top_right': Tuple[float, float],
#            'bottom_left': Tuple[float, float],
#            'bottom_right': Tuple[float, float],
#        },
#        'patch_size': Tuple[float, float],  # (width, height) of one patch, in cht coordinates
#        'patch_dict': {
#            'A1': {
#                'xyz': List[float],         # [X, Y, Z] from EXPECTED section
#                'grid_idx': Tuple[int, int],# patch index in grid (i, j) — by x and y
#                'array_idx': int,           # index in grid_linear and parametric_uv
#                'analysis_result': Any,
#            },
#            ...
#        },
#        'grid_linear': List[Tuple[float, float]],   # [(x0, y0), (x1, y1), ...] — center of each patch
#        'grid_linear_ref': List[Tuple[float, float]],   # [(x0, y0), (x1, y1), ...] — center of each patch
#        'parametric_uv': List[Tuple[float, float]], # [(u0, v0), (u1, v1), ...] — normalized coordinates
#        'patch_scale': Int - scaling of recognition area
#        'range_name': range_name
#    }