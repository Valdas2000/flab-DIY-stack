import numpy as np
from cv2 import getPerspectiveTransform, perspectiveTransform
from const import GENERIC_ERROR, GENERIC_OK

def convert_cht_to_pixels(cht_data: dict, image_width: int, image_height: int, dpi: int, with_demo = False) -> int:
    """
    Transform CHT grid coordinates to pixel coordinates with geometric integrity preservation.

    with_demo= True converts CHT patch dictionary to linear numpy arrays with synchronized indexing
    for efficient patch access. Implements conservative data principle - always
    recalculates working coordinates from reference data using perspective transformation.

    Args:
        cht_data (dict): CHT data containing:
            - 'patch_dict': dict[str, dict] - Dictionary with patch data
            - 'corner_ref': dict[str, tuple[float, float]] - Reference corner points
        image_width (int): Target image width in pixels
        image_height (int): Target image height in pixels
        dpi (int): Dots per inch for coordinate conversion from millimetres used only if with_demo= True

    Returns:
        tuple[int, dict]: A tuple of (status, enhanced_data):
            - status (int): Operation execution status (GENERIC_OK or GENERIC_ERROR)
            - enhanced_data (dict): Enhanced CHT data with populated arrays:
                - 'patches': np.ndarray[np.float32] - Patch centre coordinates in pixels (N, 2)
                - 'uv': np.ndarray[np.float32] - Normalised UV coordinates (N, 2)
                - 'patch_wh': np.ndarray[np.float32] - Patch dimensions (N, 2)
                - 'RGB': np.ndarray[np.uint8] - Packed RGB values (N,)
                - 'corner': np.ndarray[np.float32] - Corner coordinates in pixels (4, 2)
                - 'patch_dict': dict[str, dict] - Updated with 'array_idx' field
                - All original fields preserved

    Processing Logic:
        1. Extract data: Converts patch_dict to linear numpy arrays
        2. Index assignment: Updates each patch with array_idx for O(1) access
        3. Coordinate transformation: Applies DPI scaling (pixels = mm × dpi / 25.4)
        4. Boundary validation: Checks if corners fit within image bounds
        5. Fallback positioning: If corners exceed bounds, applies safe padding
        6. Perspective transformation: Maps UV coordinates to screen coordinates
        7. Conservative data: Reference data remains immutable throughout

    Note:
        - Conversion factor: pixels = millimetres × dpi / 25.4
        - Boundary overflow triggers fallback corner positioning with 10-pixel padding
        - Perspective transformation handles lens distortion and viewing angle
        - array_idx enables direct patch access without coordinate searching
        - Designed for scenarios where Argyll ColorChecker recognition fails
          due to lost patch separators during photography
        - Error handling returns GENERIC_ERROR if perspective transformation fails

    Example:
        cht_data = parse_cht_file("target.cht")[1]
        status, result = convert_cht_to_pixels(cht_data, 1920, 1080, 300)
        if status == GENERIC_OK:
            print(f"Patches array shape: {result['patches'].shape}")
            print(f"First patch position: {result['patches'][0]}")
            print(f"RGB values shape: {result['RGB'].shape}")
    """


    # Conversion factor: pixels = mm × dpi / 25.4
    scale_factor = 1.0
    calc_name = "corner_demo"
    if not with_demo:
        cht_w = cht_data['corner_ref'][3][0] - cht_data['corner_ref'][0][0]
        cht_h = cht_data['corner_ref'][3][1] - cht_data['corner_ref'][0][1]
        scale_factor = min(cht_w / image_width, cht_h / image_height)
        cht_data['corner'] = np.array(cht_data['corner_ref'], dtype=np.float32) * scale_factor
        adopt_corner_target(cht_data["corner"] , image_width, image_height)
        calc_name = "corner"
    else:
        scale_factor = dpi / 25.4

        uv_list = []
        uv_wh_list = []
        rgb_list = []
        idx = 0

        for key, val in cht_data["patch_dict"].items():
            uv_list.append(val['uv'])
            uv_wh_list.append(val['uv_wh'])
            rgb_list.append(val['rgb'])
            val['array_idx'] = idx
            idx += 1

        # Convert lists into numpy arrays
        cht_data["corner_demo"] = np.array(cht_data['corner_ref'], dtype=np.float32) * scale_factor
        cht_data['corner'] = np.array(cht_data['corner_ref'], dtype=np.float32) * scale_factor

        cht_data["uv_wh"] = np.array(uv_wh_list, dtype=np.float32).reshape(-1, 1, 2)
        cht_data["uv"] = np.array(uv_list, dtype=np.float32).reshape(-1, 1, 2)

        cht_data["RGB"] = np.array(rgb_list, dtype=np.uint32)

    # Transform UV coordinates to screen coordinates
    adopt_corner_target(cht_data[calc_name], image_width, image_height)
    ret, coords = transform_uv_to_screen(cht_data["uv"], cht_data[calc_name])
    if ret == GENERIC_OK:
        cht_data['points'] = coords
    ret, coords = transform_uv_to_screen(cht_data["uv_wh"], cht_data[calc_name])
    if ret == GENERIC_OK:
        cht_data['patch_wh'] = coords
        cht_data['half_patch'] = coords / 2

    return  ret

def transform_uv_to_screen(uv, corner):
    """
    Transforms UV coordinates to screen coordinates using perspective transformation.

    This function performs a perspective transformation from normalised UV coordinates
    (range [0,1] x [0,1]) to actual screen coordinates, utilising a quadrilateral
    as the target area.

    Args:
        uv (numpy.ndarray): Array of UV coordinates in format [[u1, v1], [u2, v2], ...].
                           Coordinates must be within the range [0,1].
        corner (numpy.ndarray): Quadrilateral in screen coordinates in format
                               [[x1, y1], [x2, y2], [x3, y3], [x4, y4]].
                               Defines the target area for transformation.

    Returns:
        tuple: (status, result)
            - status (int): GENERIC_OK on success, GENERIC_ERROR on failure
            - result (numpy.ndarray): Array of transformed screen coordinates
                                     in format [[x1, y1], [x2, y2], ...] or
                                     empty array on error

    Note:
        - UV coordinates (0,0) correspond to the first corner of the quadrilateral
        - UV coordinates (1,1) correspond to the third corner of the quadrilateral
        - The quadrilateral must be valid and possess non-zero area
        - The function utilises OpenCV for perspective transformation

    Example:
        uv_points = np.array([[0.5, 0.5], [0.25, 0.75]])
        screen_quad = np.array([[0, 0], [100, 0], [100, 100], [0, 100]])
        status, screen_points = transform_uv_to_screen(uv_points, screen_quad)
        if status == GENERIC_OK:
        ...     print(f"Screen centre: {screen_points[0]}")  # [50, 50]
    """

    uv_quad = np.array([[0, 0], [1, 0], [0, 1], [1, 1]], dtype=np.float32)
    if not _is_valid_quad(corner) or not _quad_area(corner):
        return GENERIC_ERROR, np.array([])

    H = getPerspectiveTransform(uv_quad, corner)
    screen_pts = perspectiveTransform(uv, H).reshape(-1, 2)

    return GENERIC_OK, screen_pts

def adopt_corner_target(corners: np.ndarray, image_width: int, image_height: int,
                        rotation: int = 0) -> (int, np.ndarray):
    """
    Adapt grid coordinates to target dimensions with rotation logic.

    Args:
        corners: Corner points
        image_width: Target image width
        image_height: Target image height
        rotation: -1 (counter-clockwise), 1 (clockwise), 0 (auto-rotation)

    Returns:
        GENERIC_OK on success, updated corner points
    """

    # If grid doesn't fit initially → force auto-rotation
    if not _is_inside_np(corners, [0, 0, image_width, image_height]):
        rotation = GENERIC_OK

    # Manual counter-clockwise rotation (grid initially fits)
    if rotation == -1:
        corners[:] = _rotate_90_ccw(corners, image_width, image_height)
        # If doesn't fit after 90° → rotate another 90° (total 180°)
        if not _is_inside_np(corners, [0, 0, image_width, image_height]):
            corners = _rotate_90_ccw(corners, image_width, image_height)
        return GENERIC_OK

    # Manual clockwise rotation (grid initially fits)
    if rotation == 1:
        corners[:]= _rotate_90_cw(corners, image_width, image_height)
        # If doesn't fit after 90° → rotate another 90° (total 180°)
        if not _is_inside_np(corners, [0, 0, image_width, image_height]):
            corners[:] = _rotate_90_cw(corners, image_width, image_height)
        return GENERIC_OK

    # Auto-rotation: align orientations first, then scale if needed
    # Rotate grid to match image orientation (portrait/landscape)
    if _is_grid_portrait_orientation(corners) != _is_image_portrait_orientation(image_width, image_height):
        corners[:] = _rotate_90_ccw(corners, image_width, image_height)

    # If still doesn't fit → apply rule-10 scaling (10px margins)
    if not _is_inside_np(corners, [0, 0, image_width, image_height]):
        corners[:]= np.array(
            [[10, 10], [image_width - 10, 10], [10, image_height - 10], [image_width - 10, image_height - 10]],
            dtype=np.float32)

    return GENERIC_OK

def _is_image_portrait_orientation(width: int, height: int) -> bool:
    """Check if image is in portrait orientation (height > width)"""
    return height > width

def _is_grid_portrait_orientation(corner_coords: np.ndarray) -> bool:
    """Check if grid is in portrait orientation (height > width)"""
    x_coords = corner_coords[:, 0]
    y_coords = corner_coords[:, 1]
    grid_width = np.max(x_coords) - np.min(x_coords)
    grid_height = np.max(y_coords) - np.min(y_coords)
    return grid_height > grid_width

def _rotate_90_cw(coords: np.ndarray, width: int, height: int) -> np.ndarray:
    """Rotate coordinates 90° clockwise"""
    rotated = coords.copy()
    rotated[:, 0] = height - coords[:, 1]
    rotated[:, 1] = coords[:, 0]
    return rotated

def _rotate_90_ccw(coords: np.ndarray, width: int, height: int) -> np.ndarray:
    """Rotate coordinates 90° counter-clockwise"""
    rotated = coords.copy()
    rotated[:, 0] = coords[:, 1]
    rotated[:, 1] = width - coords[:, 0]
    return rotated

def _is_inside_np(inner: np.ndarray, outer_bbox):
    """
    Check if inner inside outer

    inner: np.array формы (4, 2)
    outer_bbox: [xmin, ymin, xmax, ymax]
    """
    xmin, ymin, xmax, ymax = outer_bbox
    # Используем векторизованные операции без промежуточных переменных
    return (
        np.all(inner[:, 0] >= xmin) and
        np.all(inner[:, 0] <= xmax) and
        np.all(inner[:, 1] >= ymin) and
        np.all(inner[:, 1] <= ymax)
    )

def _is_valid_quad(corner, threshold=5.0):
    pts = np.array(corner, dtype=np.float32)
    d = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=-1)
    too_close = (d < threshold) & (d > 0)
    return not np.any(too_close)

def _quad_area(corner, threshold = 1024.):
    # Используем два вектора и внешнее произведение
    a, b, c, d = map(np.array, corner)
    ab = b - a
    ad = d - a
    return np.abs(np.cross(ab, ad)) > threshold
