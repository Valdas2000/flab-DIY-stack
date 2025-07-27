import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from const import GENERIC_OK, GENERIC_ERROR
import rawpy

def tr(text):
    """Translation wrapper for Qt5 internationalisation support."""
    return text

def apply_wb(rgb, wb_vector=None):
    if wb_vector is None:
        return rgb
    wb_norm = wb_vector / wb_vector[1]  # нормируем на G
    return rgb / wb_norm

#DCP_CCCC_RAW: без WB
#DCP_CCCC_NORMWB: с нормировкой по CWB
#DCP_CCCC_JPEG_MATCH: с визуальной адаптацией по JPEG WB

#with rawpy.imread(file) as raw:
#    raw_image = raw.raw_image_visible.astype(np.float32)


def bayer_masks_for_patch(top_left_x, top_left_y, h, w, pattern):
    """
    Генерирует маски R, G, B для патча (h×w), расположенного в (x, y),
    с учётом глобального Bayer-паттерна.

    Returns:
        r_mask, g_mask, b_mask: булевы маски R/G/B размером h×w
    """

    r_mask = np.zeros((h, w), dtype=bool)
    g_mask = np.zeros((h, w), dtype=bool)
    b_mask = np.zeros((h, w), dtype=bool)

    masks = (r_mask, g_mask, b_mask)

    for i in range(h):
        for j in range(w):
            dy = (top_left_y + i) % 2
            dx = (top_left_x + j) % 2
            color = pattern[dy, dx]
            masks[color][i, j] = True

    return r_mask, g_mask, b_mask

def analyze_patches(points: np.ndarray, wh: np.ndarray, outputs: dict):
    """Анализ всех патчей на изображении"""

    try:
        rez = {}
        pattern = None
        for subject, file in outputs.items():
            rez[subject] = []
            print(tr("Subject: {0} file: {1}").format(subject, file))
            # check file extension (type)
            if file.endswith(".tif") or file.endswith(".tiff"):
                image = np.array(Image.open(file))
                is_RGB = True
            else:
                raw = rawpy.imread(file)
                image = raw.raw_image_visible  # ← ссылка на C-буфер
                pattern = raw.raw_pattern
                is_RGB = False
                raw.close()

            # Для каждого патча в словаре
            for idx, patch_wh in enumerate(wh):
                # Получаем индексы в сетке
                grid_x, grid_y = points[idx]
                grid_wx, grid_wy = patch_wh
                x1 = int(grid_x - grid_wx / 2)
                y1 = int(grid_y - grid_wy / 2)
                x2 = int(grid_x + grid_wx /2)
                y2 = int(grid_y + grid_wy /2)

                p_info = None
                if not is_RGB and pattern is not None:
                    p_info= (x1, y1,pattern)

                # Вырезаем патч из изображения
                patch = image[y1:y2, x1:x2]

                # Анализируем патч
                if patch.size > 0:  # Проверяем, что патч не пустой
                    analysis_result = analyze_patch(patch, p_info)
                    rez[subject].append(analysis_result)

        return GENERIC_OK, rez
    except Exception as e:
        print(tr("Error: {0}").format(e))
        return GENERIC_ERROR, []

def get_bayer_pixel_count(h, w, channel_idx):
    """Подсчет пикселей определенного канала в Bayer-паттерне"""
    if channel_idx == 1:  # Green
        return h * w // 2  # G составляет 50% в RGGB
    else:  # Red или Blue
        return h * w // 4  # R и B по 25% каждый

def analyze_patch(patch, p_info,  reliable_threshold=0.02 , edge_threshold=0.25):
    """
    Анализирует патч изображения и возвращает его средние значения RGB.

    Args:
        patch: Numpy array с формой (height, width, 3) - RGB изображение
        reliable_threshold: Пороговое значение разницы между mean и median (по умолчанию 0.02 или 2%)

    Returns:
        dict: Словарь с результатами анализа, включая:
            - mean_rgb: Средние значения RGB
            - median_rgb: Медианные значения RGB
            - delta: Разница между mean и median
            - reliable: Флаг надежности патча
            - method: Использованный метод анализа
    """
    # Проверяем размер патча для определения метода обработки
    height, width = patch.shape[:2]
    min_pixels_per_channel = height * width

    if p_info:
        # Для RAW учитываем количество пикселей каждого канала
        bayer_mask_rgb = bayer_masks_for_patch(p_info[0], p_info[1], height, width, p_info[2])
        min_pixels_per_channel = min([
            np.sum(bayer_mask_rgb[0]),  # R
            np.sum(bayer_mask_rgb[1]),  # G
            np.sum(bayer_mask_rgb[2])   # B
        ])

    # Check if patch might have edge artifacts
    edge_score = detect_edge_artifacts(patch)

    # Выбираем метод в зависимости от размера патча
    if min_pixels_per_channel <= 400:
        return {
            'mean_rgb': np.array([0, 0, 0]),
            'median_rgb': np.array([0, 0, 0]),
            'std_rgb': np.array([255, 255, 255]),
            'delta': 100,
            'normalized_delta': 100,
            'reliable': False,
            'method': "Not_Applicable",
            'edge_score': -1  # New field
        }
    elif min_pixels_per_channel <= 900:
        # Маленький патч: плотная регулярная выборка из центра
        result = process_small_patch(patch, p_info)
        method = "small_patch_sampling"
    elif min_pixels_per_channel <= 3600:
        # Средний патч: центральная зона 50% по ширине
        result = process_medium_patch(patch, p_info)
        method = "medium_patch_central_zone"
    else:
        # Большой патч: маска по гауссу или кругу
        result = process_large_patch(patch, p_info)
        method = "large_patch_gaussian_mask"

    # Вычисляем дельту и проверяем надежность
    delta = np.abs(result['mean_rgb'] - result['median_rgb'])
    is_reliable = False
    normalized_delta = np.mean(delta) / (np.mean(result['mean_rgb']) + 1e-6)

    if min_pixels_per_channel > 32:  # Менее 4x4 пикселей на канал
        adapted_threshold = reliable_threshold * (100 / min_pixels_per_channel) ** 0.5
        adapted_threshold = min(adapted_threshold, 0.1)  # Максимальный порог 10%
        is_reliable = (normalized_delta <= adapted_threshold) and (edge_score <= edge_threshold)

    # Формируем итоговый результат
    return {
        'mean_rgb': result['mean_rgb'],
        'median_rgb': result['median_rgb'],
        'std_rgb': result['std_rgb'],
        'delta': delta,
        'normalized_delta': normalized_delta,
        'reliable':is_reliable,
        'method': method,
        'edge_score': edge_score  # New field
    }

def detect_edge_artifacts(patch):
    """Detect potential edge artifacts in patch"""
    # Convert to grayscale for edge detection
    if len(patch.shape) == 3:
        gray_patch = np.mean(patch, axis=2)
    else:
        gray_patch = patch

    # Check gradient near patch borders
    h, w = gray_patch.shape
    border_width = max(2, min(h, w) // 10)

    # Compare border vs center intensity
    center = gray_patch[border_width:-border_width, border_width:-border_width]

    # Extract border pixels
    border_pixels = np.concatenate([
        gray_patch[:border_width, :].flatten(),  # top
        gray_patch[-border_width:, :].flatten(),  # bottom
        gray_patch[:, :border_width].flatten(),  # left
        gray_patch[:, -border_width:].flatten()  # right
    ])

    center_mean = np.mean(center)
    border_mean = np.mean(border_pixels)

    return abs(center_mean - border_mean) / (center_mean + 1e-6)


def std_analyze(patch, bmask_rgb):
    """
    Вычисление trimmed mean, median и std для патча.
    Для RAW применяется маска Bayer, для RGB — по всем пикселям.

    Args:
        patch: Numpy array (RAW: 2D, RGB: 3D)
        bmask_rgb: tuple из масок (bool arrays) для R, G, B
        is_RGB: True если TIFF/RGB, False если RAW

    Returns:
        mean_rgb, median_rgb, std_rgb: np.array с 3 значениями
    """
    if bmask_rgb:
        # RAW: применяем маски Bayer
        mean_rgb = np.array([
            trimmed_mean(patch[bmask_rgb[0]]),
            trimmed_mean(patch[bmask_rgb[1]]),
            trimmed_mean(patch[bmask_rgb[2]])
        ])
        median_rgb = np.array([
            np.median(patch[bmask_rgb[0]]),
            np.median(patch[bmask_rgb[1]]),
            np.median(patch[bmask_rgb[2]])
        ])
        std_rgb = np.array([
            np.std(patch[bmask_rgb[0]]),
            np.std(patch[bmask_rgb[1]]),
            np.std(patch[bmask_rgb[2]])
        ])
    else:
        # TIFF: считаем по всем пикселям каждого канала
        mean_rgb = np.array([
            trimmed_mean(patch[:, :, 0]),
            trimmed_mean(patch[:, :, 1]),
            trimmed_mean(patch[:, :, 2])
        ])
        median_rgb = np.array([
            np.median(patch[:, :, 0]),
            np.median(patch[:, :, 1]),
            np.median(patch[:, :, 2])
        ])
        std_rgb = np.array([
            np.std(patch[:, :, 0]),
            np.std(patch[:, :, 1]),
            np.std(patch[:, :, 2])
        ])


    return mean_rgb, median_rgb, std_rgb


def process_small_patch(patch, p_info):
    """
    Обработка маленьких патчей (≤30×30):
    - Плотная регулярная выборка из центра
    - Trimmed mean для устойчивости

    Args:
          patch: RAW: (height, width) или RGB: (height, width, 3)
    Returns:
        dict: Словарь с mean_rgb и median_rgb
    """
    # Применяем размытие по Гауссу для устранения шума
    blurred_patch = gaussian_filter(patch.astype(np.float32), sigma=1.2, mode='reflect')

    # Вычисляем центр патча
    h, w = patch.shape[:2]
    cy, cx = h // 2, w // 2

    # Определяем размер центральной выборки (примерно 60% патча)
    sample_size = max(5, min(21, int(min(h, w) * 0.6)))
    half_size = sample_size // 2

    # Извлекаем центральную часть
    y_start = max(0, cy - half_size)
    y_end = min(h, cy + half_size + 1)
    x_start = max(0, cx - half_size)
    x_end = min(w, cx + half_size + 1)

    center_patch = blurred_patch[y_start:y_end, x_start:x_end]
    bayer_mask_rgb = None
    if p_info:
        bayer_mask_rgb = bayer_masks_for_patch(p_info[0] + x_start, p_info[1] + y_start, y_end - y_start, x_end - x_start, p_info[2])

    # Теперь правильно передаем обрезанные маски!
    rez = std_analyze(center_patch, bayer_mask_rgb)

    return {
        'mean_rgb': rez[0],
        'median_rgb': rez[1],
        'std_rgb': rez[2]
    }


def process_medium_patch(patch, p_info):
    """
    Обработка средних патчей (30×30 - 60×60):
    - Центральная зона 50% по ширине
    - Комбинация mean и median

    Args:
        patch: Numpy array с формой (height, width, 3)

    Returns:
        dict: Словарь с mean_rgb и median_rgb
    """
    # Применяем размытие по Гауссу
    blurred_patch = gaussian_filter(patch.astype(float), sigma=1.2, mode='reflect')

    # Вычисляем центр патча
    h, w = patch.shape[:2]
    cy, cx = h // 2, w // 2

    # Берем центральную зону 50% от размера
    half_h = max(1, (h // 2) // 2)
    half_w = max(1, (w // 2) // 2)

    # Извлекаем центральную часть
    y_start = max(0, cy - half_h)
    y_end = min(h, cy + half_h + 1)
    x_start = max(0, cx - half_w)
    x_end = min(w, cx + half_w + 1)

    center_patch = blurred_patch[y_start:y_end, x_start:x_end]
    bayer_mask_rgb = None
    if p_info:
        bayer_mask_rgb = bayer_masks_for_patch(p_info[0] + x_start, p_info[1] + y_start, y_end - y_start, x_end - x_start, p_info[2])

    # Вычисляем обычное среднее и медиану
    rez = std_analyze(center_patch, bayer_mask_rgb)

    # Комбинируем mean и median для большей устойчивости
    combined_rgb = (rez[0] + rez[1]) / 2

    return {
        'mean_rgb': combined_rgb,
        'median_rgb': rez[1],
        'std_rgb': rez[2]
    }

def weighted_std(values, weights):
    average = np.average(values, weights=weights)
    variance = np.average((values - average) ** 2, weights=weights)
    return np.sqrt(variance)

def process_large_patch(patch, p_info):
    """
    Обработка больших патчей (>60×60):
    - Маска по гауссу или кругу
    - Взвешенное среднее
    """
    # Применяем размытие по Гауссу
    blurred_patch = gaussian_filter(patch.astype(float), sigma=1.5, mode='reflect')

    # Создаем маску по Гауссу
    h, w = patch.shape[:2]
    mask = gaussian_mask(h, w, sigma_scale=0.33)

    if p_info:
        # Для RAW учитываем количество пикселей каждого канала
        bayer_mask_rgb = bayer_masks_for_patch(p_info[0], p_info[1], h, w, p_info[2])

        # Для RAW применяем маски к 2D данным
        r_values = blurred_patch[bayer_mask_rgb[0]]
        g_values = blurred_patch[bayer_mask_rgb[1]]
        b_values = blurred_patch[bayer_mask_rgb[2]]

        r_weights = mask[bayer_mask_rgb[0]]
        g_weights = mask[bayer_mask_rgb[1]]
        b_weights = mask[bayer_mask_rgb[2]]

        mean_r = np.average(r_values, weights=r_weights)
        mean_g = np.average(g_values, weights=g_weights)
        mean_b = np.average(b_values, weights=b_weights)

        std_r = weighted_std(r_values, r_weights)
        std_g = weighted_std(g_values, g_weights)
        std_b = weighted_std(b_values, b_weights)

    else:
        # RGB: применяем маску к каждому каналу
        masked_r = blurred_patch[:, :, 0] * mask
        masked_g = blurred_patch[:, :, 1] * mask
        masked_b = blurred_patch[:, :, 2] * mask

        sum_mask = np.sum(mask)
        mean_r = np.sum(masked_r) / sum_mask
        mean_g = np.sum(masked_g) / sum_mask
        mean_b = np.sum(masked_b) / sum_mask

        std_r = np.std(masked_r)
        std_g = np.std(masked_g)
        std_b = np.std(masked_b)

    mean_rgb = np.array([mean_r, mean_g, mean_b])
    std_rgb = np.array([std_r, std_g, std_b])

    # Медиана из центральной области
    center_radius = int(min(h, w) * 0.3)
    cy, cx = h // 2, w // 2

    # Безопасные границы
    y_start = max(0, cy - center_radius)
    y_end = min(h, cy + center_radius)
    x_start = max(0, cx - center_radius)
    x_end = min(w, cx + center_radius)

    if p_info:  # RAW
        # Корректируем координаты для Bayer маски
        center_bayer = bayer_masks_for_patch(
            p_info[0] + x_start,
            p_info[1] + y_start,
            y_end - y_start,
            x_end - x_start,
            p_info[2]
        )
        center_patch = blurred_patch[y_start:y_end, x_start:x_end]
        median_rgb = np.array([
            np.median(center_patch[center_bayer[0]]),
            np.median(center_patch[center_bayer[1]]),
            np.median(center_patch[center_bayer[2]])
        ])
    else:  # RGB
        center_patch = blurred_patch[y_start:y_end, x_start:x_end]
        median_rgb = np.median(center_patch.reshape(-1, 3), axis=0)

    return {
        'mean_rgb': mean_rgb,
        'median_rgb': median_rgb,
        'std_rgb': std_rgb
    }

def trimmed_mean(channel, trim=0.1):
    """
    Вычисляет trimmed mean - среднее после удаления экстремальных значений.

    Args:
        channel: Numpy array с одним каналом изображения
        trim: Доля отбрасываемых значений с каждой стороны (по умолчанию 0.1 или 10%)

    Returns:
        float: Trimmed mean значение
    """
    sorted_vals = np.sort(channel.flatten())
    n = len(sorted_vals)
    trim_size = int(n * trim)
    return np.mean(sorted_vals[trim_size:-trim_size] if trim_size > 0 else sorted_vals)

def gaussian_mask(h, w, sigma_scale=0.33):
    """
    Создает 2D маску по Гауссу.

    Args:
        h, w: Высота и ширина маски
        sigma_scale: Масштаб сигмы относительно ширины (по умолчанию 0.33)

    Returns:
        Numpy array: 2D маска с весами по Гауссу
    """
    # Создаем координатную сетку
    y, x = np.ogrid[:h, :w]

    # Вычисляем центр
    cy, cx = h / 2, w / 2

    # Вычисляем сигму на основе размера патча
    sigma = min(h, w) * sigma_scale

    # Создаем маску по Гауссу
    mask = np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * sigma ** 2))

    # Нормализуем маску
    mask = mask / np.max(mask)

    return mask


