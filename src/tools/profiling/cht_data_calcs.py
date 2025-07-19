import numpy as np
from cv2 import getPerspectiveTransform, perspectiveTransform
from const import GENERIC_ERROR, GENERIC_OK

def convert_cht_to_pixels(cht_data: dict, image_width: int, image_height: int, dpi: int|None=None) -> int:
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
        GENERIC_OK on success, GENERIC_ERROR on failure

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

    """


    scale_factor = 1.0
    with_demo = bool(dpi)
    calc_name = "corner_demo"
    if not with_demo:
        cht_w = cht_data['corner_ref'][3][0] - cht_data['corner_ref'][0][0]
        cht_h = cht_data['corner_ref'][3][1] - cht_data['corner_ref'][0][1]
        scale_factor = min(image_width / cht_w,  image_height / cht_h)
        cht_data['corner'] = np.array(cht_data['corner_ref'], dtype=np.float32) * scale_factor
        calc_name = "corner"
    else:
        # Conversion factor: pixels = mm × dpi / 25.4
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
        cht_data["RGB"] = np.array(rgb_list, dtype=np.uint32)

        cht_data['corner'] = np.array(cht_data['corner_ref'], dtype=np.float32) * scale_factor

        cht_data["uv_wh"] = np.array(uv_wh_list, dtype=np.float32).reshape(-1, 1, 2)
        cht_data["uv"] = np.array(uv_list, dtype=np.float32).reshape(-1, 1, 2)


    # Transform UV coordinates to screen coordinates
    adopt_corner_target(cht_data[calc_name], image_width, image_height)
    ret, points, patch_wh =  compute_patch_wh_aligned(cht_data["uv"], cht_data["uv_wh"], cht_data[calc_name])
    if ret == GENERIC_OK:
        cht_data['points'] = points
        cht_data['patch_wh'] = patch_wh

    return  ret


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
    # if _is_grid_portrait_orientation(corners) != _is_image_portrait_orientation(image_width, image_height):
    #    corners[:] = _rotate_90_ccw(corners, image_width, image_height)

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


def _transform_uv_to_screen(uv, corner):
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

def compute_patch_wh_aligned(uv, uv_wh, corner, scale_percent=100):
    """
    Оптимизированное преобразование для формата (-1, 1, 2).
    """
    scale = scale_percent / 100.0
    # uv уже имеет форму (-1, 1, 2), uv_wh тоже
    uv_wh_scaled = uv_wh * scale
    n = len(uv)

    # Создаем все точки одним батчем
    zeros = np.zeros_like(uv_wh_scaled[:, :, 0:1])  # форма (-1, 1, 1)

    # Создаем смещения для правых и нижних точек
    right_offset = np.concatenate([uv_wh_scaled[:, :, 0:1], zeros], axis=2)  # (n, 1, 2)
    bottom_offset = np.concatenate([zeros, uv_wh_scaled[:, :, 1:2]], axis=2)  # (n, 1, 2)

    # Объединяем все точки: центры + правые + нижние
    all_points = np.concatenate([
        uv,  # центры
        uv + right_offset,  # правые точки
        uv + bottom_offset  # нижние точки
    ], axis=0)  # форма (3*n, 1, 2)

    # Одно преобразование для всех точек
    ret, screen_points = _transform_uv_to_screen(all_points, corner)
    if ret != GENERIC_OK:
        return GENERIC_ERROR, None, None

    # Разделяем результат
    centers = screen_points[:n].reshape(-1, 2)
    screen_right = screen_points[n:2 * n].reshape(-1, 2)
    screen_bottom = screen_points[2 * n:3 * n].reshape(-1, 2)

    # Векторизованное вычисление размеров
    width = np.linalg.norm(screen_right - centers, axis=1)
    height = np.linalg.norm(screen_bottom - centers, axis=1)

    patch_wh = np.column_stack([width, height])

    return GENERIC_OK, centers, patch_wh