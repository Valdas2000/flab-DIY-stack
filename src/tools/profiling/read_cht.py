from const import GENERIC_OK, GENERIC_ERROR

def tr(text):
    """Translation wrapper for Qt5 internationalisation support."""
    return text


import numpy as np

def parse_cht_file(filename):
    status, result = read_cht_file(filename)
    if status != GENERIC_OK:
        return status, []
    rez, cht_data = prepare_cht_data(result['patches'], result['corner'])
    return rez, cht_data

def prepare_cht_data(patches, corner):
    """
    Calculate display data from parsed patches and corner data.

    Args:
        patches: dict with patch data {'A1': {'patch_point': [x, y], 'patch_size': [w, h], 'xyz': {...}}, ...}
        corner: list of 8 floats [x0, y0, x1, y1, x2, y2, x3, y3] for F frame corners

    Returns:
        data: Dictionary with patch and grid data
    """

    # Извлекаем углы рамки
    corner_points = corner

    patch_dict = {}

    for patch_name, patch_data in patches.items():
        # Расчет центра патча (patch_xy) - смещение на половину размера
        patch_point = patch_data['patch_point']
        patch_size = patch_data['patch_size']

        center_x = patch_point[0] + patch_size[0] / 2
        center_y = patch_point[1] + patch_size[1] / 2
        patch_xy = np.array([center_x, center_y], dtype=np.float32)

        # Calculate UV for the patch center point
        uv = _calculate_uv_coordinates(patch_xy, corner_points)
        uv_wh = _calculate_uv_coordinates(patch_size, corner_points)
        # Преобразование XYZ в RGB
        xyz_data = patch_data['xyz']
        rgb_packed = _xyz_to_rgb(xyz_data)

        # Формирование данных патча
        patch_dict[patch_name] = {
            'xyz': xyz_data,
            'rgb': rgb_packed,
            'uv': uv,
            'uv_wh': uv_wh,
            'patch_xy': patch_xy,
            'patch_wh': (patch_size[0], patch_size[1]),
            'analysis_result': None,
            'array_idx': 0,  # пока заглушка
        }

    return GENERIC_OK, {
        'patch_dict': patch_dict,
        'corner_ref': corner_points,
        'range_names': _find_corner_patches(patches),
        'patch_scale': 100,

        'corner_demo': np.array([], dtype=np.float32),      # reper pints for the demo image
        'corner': np.array([], dtype=np.float32),           # reper points
        'points': np.array([], dtype=np.float32),          # calculated patch centres
        'patches_wh': np.array([], dtype=np.float32),       # calculated total patch
        'uv_wh': np.array([], dtype=np.float32),            # uv for patch wh
        'uv': np.array([], dtype=np.float32),               # uv for centre point
        'RGB': np.array([], dtype=np.uint8)                 # rgb colours for patches
    }


def read_cht_file(filename):
    """
    Parse CHT file and extract patches and corner information.

    Args:
        filename (str): Path to the CHT file to parse

    Returns:
        tuple[str, dict]: A tuple of (status, data):
            - status: GENERIC_OK or GENERIC_ERROR
            - data: Dictionary with 'patches' and 'corner' keys
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()

        # Parse BOXES section
        boxes_data = _parse_boxes_section(content)
        if not boxes_data:
            print(tr("Error: Failed to parse BOXES section"))
            return (GENERIC_ERROR, {})

        # Parse EXPECTED section
        expected_colours = _parse_expected_section(content)
        if not expected_colours:
            print(tr("Error: Failed to parse EXPECTED section"))
            return (GENERIC_ERROR, {})

        # Extract corner coordinates from F line
        corner = None
        patches = {}

        for box_def in boxes_data:
            if box_def['type'] == 'F':
                corner = _extract_corner_coordinates(box_def)
            elif box_def['type'] in ['X', 'Y']:
                # Generate patches from X/Y definitions
                generated_patches = _generate_patches_from_box(box_def)

                # Validate that all patches have expected colours
                for patch_name, patch_data in generated_patches.items():
                    if patch_name not in expected_colours:
                        print(tr("Error: Missing expected colour for patch: %s") % patch_name)
                        expected_colours[patch_name] = {'colour_space': 'XYZ', 'xyz':{'X': -1, 'Y': -1, 'Z': -1}}
                        # return (GENERIC_ERROR, {})

                    # Add XYZ colour data
                    patch_data['xyz'] = expected_colours[patch_name]['xyz']
                    patches[patch_name] = patch_data

        # Validate corner data
        if corner is None:
            print(tr("Error: Missing fiducial marks (F line) in BOXES section"))
            return (GENERIC_ERROR, {})

        if len(patches) == 0:
            print(tr("Error: No patches found in BOXES section"))
            return (GENERIC_ERROR, {})

        result = {
            'patches': patches,
            'corner': corner
        }

        return (GENERIC_OK, result)

    except Exception as e:
        print(tr("Error parsing CHT file: %s") % str(e))
        return (GENERIC_ERROR, {})


def _calculate_uv_coordinates(point, corner_points):
    """Calculate UV coordinates using linear scaling within rectangle bounds."""

    # Найдем bounding box углов
    xs = [p[0] for p in corner_points]
    ys = [p[1] for p in corner_points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Нормализуем координаты центра патча
    u = (point[0] - min_x) / (max_x - min_x) if max_x != min_x else 0.0
    v = (point[1] - min_y) / (max_y - min_y) if max_y != min_y else 0.0

    return np.array([u, v], dtype=np.float32)

def _xyz_to_rgb(xyz):
    # Извлечение значений и нормализация
    X = xyz['X'] / 100.0
    Y = xyz['Y'] / 100.0
    Z = xyz['Z'] / 100.0

    # XYZ → линейный RGB
    r =  3.2406 * X - 1.5372 * Y - 0.4986 * Z
    g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z
    b =  0.0557 * X - 0.2040 * Y + 1.0570 * Z

    # Гамма-коррекция sRGB
    def gamma_correct(c):
        return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1/2.4)) - 0.055

    r = gamma_correct(r)
    g = gamma_correct(g)
    b = gamma_correct(b)

    # Обрезка и преобразование в 8-битный цвет
    r = int(round(max(0.0, min(1.0, r)) * 255))
    g = int(round(max(0.0, min(1.0, g)) * 255))
    b = int(round(max(0.0, min(1.0, b)) * 255))

    # Упаковка в QRgb (0xFFRRGGBB)
    return (255 << 24) | (r << 16) | (g << 8) | b

def _find_corner_patches(patches):
    """
    Find 4 corner patches from patches dictionary.

    Args:
        patches: dict with patch data {'A1': {'patch_point': [x, y], 'patch_size': [w, h], ...}, ...}

    Returns:
        list: [top_left_name, top_right_name, bottom_left_name, bottom_right_name]
    """
    if not patches:
        return []

    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')

    patch_points = {}

    for patch_name, patch_data in patches.items():
        x, y = patch_data['patch_point']
        patch_points[patch_name] = (x, y)

        # Обновляем границы
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)

    corner_patches = []
    corners = [
        (min_x, min_y),  # top_left
        (max_x, min_y),  # top_right
        (min_x, max_y),  # bottom_left
        (max_x, max_y)  # bottom_right
    ]

    for corner_x, corner_y in corners:
        closest_patch = None
        min_distance = float('inf')

        for patch_name, (x, y) in patch_points.items():
            distance = ((x - corner_x) ** 2 + (y - corner_y) ** 2) ** 0.5

            if distance < min_distance:
                min_distance = distance
                closest_patch = patch_name

        corner_patches.append(closest_patch)

    return corner_patches

def _parse_boxes_section(content):
    lines = content.split('\n')
    boxes_data = []

    for i, line in enumerate(lines):
        if line.startswith('BOXES'):
            # Найдена строка BOXES
            parts = line.split()
            if len(parts) >= 2:
                try:
                    n = int(parts[1])  # Количество патчей (для информации)

                    # Читаем строки до тех пор, пока они содержат валидные данные
                    j = 1
                    while i + j < len(lines):
                        box_line = lines[i + j].strip()

                        # Пропускаем пустые строки
                        if not box_line:
                            j += 1
                            continue

                        box_parts = box_line.split()
                        if len(box_parts) == 0:
                            j += 1
                            continue

                        box_type = box_parts[0]

                        # Проверяем, что строка начинается с валидного типа
                        if box_type not in ['D', 'F', 'X', 'Y']:
                            # Встретили строку, которая не относится к BOXES - выходим
                            break

                        # Обрабатываем валидные типы
                        if box_type == 'F':
                            # F _ _ x0 y0 x1 y1 x2 y2 x3 y3
                            try:
                                coords = [float(x) for x in box_parts[3:11]]
                                boxes_data.append({
                                    'type': 'F',
                                    'coordinates': coords
                                })
                            except (ValueError, IndexError):
                                pass

                        elif box_type == 'X':
                            # X: X lxs lxe lys lye w h xo yo xi yi
                            try:
                                box_def = {
                                    'type': 'X',
                                    'x_start': box_parts[1],  # lxs
                                    'x_end': box_parts[2],  # lxe
                                    'y_start': box_parts[3],  # lys
                                    'y_end': box_parts[4],  # lye
                                    'width': float(box_parts[5]),
                                    'height': float(box_parts[6]),
                                    'x_origin': float(box_parts[7]),
                                    'y_origin': float(box_parts[8]),
                                    'x_increment': float(box_parts[9]),
                                    'y_increment': float(box_parts[10])
                                }
                                boxes_data.append(box_def)
                            except (ValueError, IndexError):
                                pass

                        elif box_type == 'Y':
                            # Y: Y lys lye lxs lxe w h xo yo xi yi
                            try:
                                box_def = {
                                    'type': 'Y',
                                    'x_start': box_parts[3],  # lxs в позиции 3
                                    'x_end': box_parts[4],  # lxe в позиции 4
                                    'y_start': box_parts[1],  # lys в позиции 1
                                    'y_end': box_parts[2],  # lye в позиции 2
                                    'width': float(box_parts[5]),
                                    'height': float(box_parts[6]),
                                    'x_origin': float(box_parts[7]),
                                    'y_origin': float(box_parts[8]),
                                    'x_increment': float(box_parts[9]),
                                    'y_increment': float(box_parts[10])
                                }
                                boxes_data.append(box_def)
                            except (ValueError, IndexError):
                                pass

                        # D строки игнорируем, но продолжаем чтение
                        j += 1

                    break
                except ValueError:
                    continue

    return boxes_data

def _parse_expected_section(content):
    """Parse EXPECTED section and return colour data."""
    lines = content.split('\n')
    colours = {}

    for i, line in enumerate(lines):
        if line.startswith('EXPECTED'):
            # Найдена строка EXPECTED
            parts = line.split()
            if len(parts) >= 3:
                try:
                    colour_space = parts[1]  # XYZ или LAB
                    n = int(parts[2])  # Количество строк

                    # Читаем следующие N строк
                    for j in range(1, n + 1):
                        if i + j < len(lines):
                            colour_line = lines[i + j].strip()
                            if colour_line:
                                colour_parts = colour_line.split()
                                if len(colour_parts) >= 4:
                                    label = colour_parts[0]
                                    try:
                                        x, y, z = float(colour_parts[1]), float(colour_parts[2]), float(colour_parts[3])
                                        colours[label] = {
                                            'xyz': {'X': x, 'Y': y, 'Z': z},
                                            'colour_space': colour_space
                                        }
                                    except ValueError:
                                        continue
                    break
                except ValueError:
                    continue

    return colours


def _extract_corner_coordinates(box_def):
    """Extract corner coordinates from F-type box definition."""
    coords = box_def['coordinates']
    # F _ _ x0 y0 x1 y1 x2 y2 x3 y3
    # Order: top-left, top-right, bottom-right, bottom-left
    # [[0, 0], [1, 0], [0, 1], [1, 1]]
    return [
        [coords[0], coords[1]],  # x0, y0 - top-left
        [coords[2], coords[3]],  # x1, y1 - top-right
        [coords[6], coords[7]],  # x3, y3 - bottom-left
        [coords[4], coords[5]],  # x2, y2 - bottom-right
    ]


def _generate_patches_from_box(box_def):
    if box_def['type'] == 'Y':
        return _generate_patches_from_box_y(box_def)
    elif box_def['type'] == 'X':
        return _generate_patches_from_box_x(box_def)
    else:
        return {}


def _generate_patches_from_box_y(box_def):
    """Generate patches from X box definition - горизонтальное направление."""
    patches = {}

    # Generate label sequences
    x_labels = _generate_label_sequence(box_def['x_start'], box_def['x_end'])
    y_labels = _generate_label_sequence(box_def['y_start'], box_def['y_end'])

    # Handle null labels
    if box_def['x_start'] == '_' or box_def['x_end'] == '_':
        x_labels = ['_']
    if box_def['y_start'] == '_' or box_def['y_end'] == '_':
        y_labels = ['_']

    # X TYPE: Сначала проходим все Y-метки для одной X-метки, потом следующую X-метку
    # Порядок генерации: A1, A2, A3, A4, A5, A6, B1, B2, B3, B4, B5, B6, ...
    # НО координаты: A1, A2, A3... должны расти по X (горизонтально)!
    for x_idx, x_label in enumerate(x_labels):
        for y_idx, y_label in enumerate(y_labels):
            # X тип: y_increment используется для движения по X (горизонтально)!
            # x_increment используется для движения по Y (вертикально)!
            patch_x = box_def['x_origin'] + (y_idx * box_def['y_increment'])  # Y-индекс для X координаты!
            patch_y = box_def['y_origin'] + (x_idx * box_def['x_increment'])  # X-индекс для Y координаты!

            # Create patch name (always XY format)
            if x_label == '_':
                patch_name = y_label if y_label != '_' else 'PATCH'
            elif y_label == '_':
                patch_name = x_label
            else:
                patch_name = f"{x_label}{y_label}"

            patch_data = {
                'patch_point': [patch_x, patch_y],
                'patch_size': [box_def['width'], box_def['height']]
            }

            patches[patch_name] = patch_data

    return patches


def _generate_patches_from_box_x(box_def):
    """Generate patches from Y box definition - вертикальное направление."""
    patches = {}

    # Generate label sequences
    x_labels = _generate_label_sequence(box_def['x_start'], box_def['x_end'])
    y_labels = _generate_label_sequence(box_def['y_start'], box_def['y_end'])

    # Handle null labels
    if box_def['x_start'] == '_' or box_def['x_end'] == '_':
        x_labels = ['_']
    if box_def['y_start'] == '_' or box_def['y_end'] == '_':
        y_labels = ['_']

    # Y TYPE: Инкременты могут быть интерпретированы по-другому
    # Нужно поменять местами использование инкрементов
    for x_idx, x_label in enumerate(x_labels):
        for y_idx, y_label in enumerate(y_labels):
            # Y тип: возможно инкременты нужно использовать наоборот
            patch_x = box_def['x_origin'] + (x_idx * box_def['y_increment'])  # Поменяли!
            patch_y = box_def['y_origin'] + (y_idx * box_def['x_increment'])  # Поменяли!

            # Create patch name (always XY format)
            if x_label == '_':
                patch_name = y_label if y_label != '_' else 'PATCH'
            elif y_label == '_':
                patch_name = x_label
            else:
                patch_name = f"{x_label}{y_label}"

            patch_data = {
                'patch_point': [patch_x, patch_y],
                'patch_size': [box_def['width'], box_def['height']]
            }

            patches[patch_name] = patch_data

    return patches

def _generate_label_sequence(start_label, end_label):
    """Generate sequence of labels from start to end."""
    if start_label == '_' or end_label == '_':
        return ['_']

    labels = []

    # Handle numeric labels with leading zeros
    if start_label.isdigit() and end_label.isdigit():
        start_num = int(start_label)
        end_num = int(end_label)
        width = len(start_label)  # Preserve leading zeros
        for i in range(start_num, end_num + 1):
            labels.append(str(i).zfill(width))

    # Handle single alphabetic labels
    elif (start_label.isalpha() and end_label.isalpha() and
          len(start_label) == 1 and len(end_label) == 1):
        start_ord = ord(start_label.upper())
        end_ord = ord(end_label.upper())
        for i in range(start_ord, end_ord + 1):
            labels.append(chr(i))

    # Handle alphanumeric labels (e.g., GS00-GS23)
    elif len(start_label) > 1 and len(end_label) > 1:
        # Find common prefix
        prefix_len = 0
        for i in range(min(len(start_label), len(end_label))):
            if start_label[i] == end_label[i]:
                prefix_len += 1
            else:
                break

        if prefix_len > 0:
            prefix = start_label[:prefix_len]
            start_suffix = start_label[prefix_len:]
            end_suffix = end_label[prefix_len:]

            if start_suffix.isdigit() and end_suffix.isdigit():
                start_num = int(start_suffix)
                end_num = int(end_suffix)
                width = len(start_suffix)
                for i in range(start_num, end_num + 1):
                    labels.append(f"{prefix}{str(i).zfill(width)}")
            else:
                # Single label fallback
                labels.append(start_label)
        else:
            labels.append(start_label)

    else:
        # Single label fallback
        labels.append(start_label)

    return labels


# Test function
def test_parse_cht_file():
    """Test function for CHT file parsing."""

    test_filename = 'C:/Argyll_V3.3.0/ref/it8.cht'
    # Test parsing
    status, result = parse_cht_file(test_filename)
    from create_target_preview import create_color_target_tiff
    from cht_data_calcs import convert_cht_to_pixels
    create_color_target_tiff(result, 'CMP_Digital_Target-7.tif', "CMP_Digital_Target-7")
    # rez = convert_cht_to_pixels(result, 3000, 2000, 72)


    # Clean up
    import os


if __name__ == '__main__':
    test_parse_cht_file()