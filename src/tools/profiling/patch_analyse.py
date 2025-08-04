import traceback

import numpy as np
import cv2
#from PIL import Image
import tifffile
from numpy.ma.core import max_val
from scipy.ndimage import gaussian_filter
from const import GENERIC_OK, GENERIC_ERROR
import rawpy
import numpy as np
import colour
from colour import CCS_ILLUMINANTS, adaptation
from colour.models import RGB_COLOURSPACE_sRGB
from colour.models import RGB_to_XYZ, XYZ_to_Lab, Lab_to_XYZ, XYZ_to_RGB, RGB_Colourspace, RGB_COLOURSPACES
from colour.adaptation import chromatic_adaptation_VonKries

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

def analyze_patches(points: np.ndarray, wh: np.ndarray, outputs: dict, metadata: dict):
    """Анализ всех патчей на изображении"""

    try:
        max_val = 0
        is_RGB = False
        is_do_lab = True
        rez = {}
        pattern = None
        colour_spaсe = make_camera_colourspace( metadata['WB']['cam2xyz'])
        for subject, f in outputs.items():
            rez[subject] = []
            file = f
            #file = '_R5B4809_DCP_9322_F7.1_80_Canon_EOS_R5.tif'
            # print(tr("Subject: {0} file: {1}").format(subject, file))
            print(tr("Subject: {0} file: {1}").format(subject, file))
            # check file extension (type)
            if file.endswith(".tif") or file.endswith(".tiff"):
                image = tifffile.imread(file)

                if image.dtype == np.uint16 or np.max(image) > 255:
                    bit_depth = 16.
                else:
                    bit_depth = 8.

                is_RGB = (image.ndim == 3 and image.shape[2] == 3)
                max_val = 65535. if bit_depth == 16 else 255.

            else:
                raw = rawpy.imread(file)
                image = raw.raw_image_visible  # ← ссылка на C-буфер
                pattern = raw.raw_pattern
                is_RGB = False
                max_val = 1.
                raw.close()

            # Для каждого патча в словаре
            for idx, patch_wh in enumerate(wh):
                result = {}
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

                height, width = patch.shape[:2]
                min_pixels_per_channel = height * width
                edge_score = detect_edge_artifacts(patch)

                if is_do_lab:
                    lab = rgb_linear_to_lab_d50(patch, colour_spaсe, max_val)
                    lab_result = analyze_lab(lab, min_pixels_per_channel)
                    result = lab_summary_to_rgb(lab_result, max_val)
                    result['is_RGB'] = True
                    result['method'] = 'process_large_patch_lab'
                else: # never got here foe now
                    # placeholder for other analuses
                    analysis_result = analyze_patch(patch, p_info)

                analysis_result = result_analyze(result, edge_score, max_val, min_pixels_per_channel, reliable_threshold=0.02 , edge_threshold=0.1)
                rez[subject].append(analysis_result)

        return GENERIC_OK, rez
    except Exception as e:
        print(tr("Error: {0}").format(e))
        traceback.print_exc()
        return GENERIC_ERROR, []

def get_bayer_pixel_count(h, w, channel_idx):
    """Подсчет пикселей определенного канала в Bayer-паттерне"""
    if channel_idx == 1:  # Green
        return h * w // 2  # G составляет 50% в RGGB
    else:  # Red или Blue
        return h * w // 4  # R и B по 25% каждый

def analyze_lab(lab_patch, min_pixels_per_channel):
    lab_result = process_large_patch_lab(lab_patch)
    return lab_result

def result_analyze(result, edge_score, min_pixels_per_channel, max_val, reliable_threshold=0.02 , edge_threshold=0.1):

    # Вычисляем дельту и проверяем надежность
    delta = np.abs(result['mean_rgb'] - result['median_rgb'])
    is_reliable = False
    normalized_delta = np.mean(delta) / (np.mean(result['mean_rgb']) + 1e-6)

    size_factor = np.clip(np.log10(min_pixels_per_channel / 64), -1, 1)
    adapted_threshold = reliable_threshold * (1 - 0.3 * size_factor)
    adapted_threshold = min(adapted_threshold, 0.2)  # Разумный максимум
    is_reliable = (normalized_delta <= adapted_threshold) and (edge_score <= edge_threshold)


    # Формируем итоговый результат
    return {
        'mean_rgb': result['mean_rgb'],
        'median_rgb': result['median_rgb'],
        'std_rgb': result['std_rgb'],

        'is_RGB': result['is_RGB'],
        'mean_rgb_n': result['mean_rgb'] / max_val,
        'median_rgb_n': result['median_rgb'] / max_val,

        'delta': delta,
        'normalized_delta': normalized_delta,
        'reliable':is_reliable,
        'method': result['method'],
        'edge_score': edge_score  # New field
    }


def analyze_patch(patch, p_info, min_pixels_per_channel):
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
        result = process_small_patch(patch, p_info, max_val)
        method = "small_patch_sampling"
    elif min_pixels_per_channel <= 3600:
        # Средний патч: центральная зона 50% по ширине
        #result = process_medium_patch(patch, p_info, max_val)
        result = process_large_patch(patch, p_info, max_val)
        method = "medium_patch_central_zone"
    else:
        # Большой патч: маска по гауссу или кругу
        result = process_large_patch(patch, p_info, max_val)
        method = "large_patch_gaussian_mask"
    return result

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


def process_small_patch(patch, p_info, bit_depth = 1):
    """
    Обработка маленьких патчей (≤30×30):
    - Плотная регулярная выборка из центра
    - Trimmed mean для устойчивости

    Args:
          patch: RAW: (height, width) или RGB: (height, width, 3)
    Returns:
        dict: Словарь с mean_rgb и median_rgb
    """

    if not p_info:
        patch = scale_patch_down(patch, 10)


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

def process_medium_patch(patch, p_info, bit_depth = 1):
    """
    Обработка средних патчей (30×30 - 60×60):
    - Центральная зона 50% по ширине
    - Комбинация mean и median

    Args:
        patch: Numpy array с формой (height, width, 3)

    Returns:
        dict: Словарь с mean_rgb и median_rgb
    """
    if not p_info:
        patch = scale_patch_down(patch, 30)


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

def process_large_patch(patch, p_info = None, bit_depth = 1):
    """
    Обработка больших патчей (>60×60):
    - Маска по гауссу или кругу
    - Взвешенное среднее
    """

    if not p_info:
        print("")
        #patch = cv2.GaussianBlur(patch, (15, 15), 3.5)
        h, w = patch.shape[:2]
        patch = cv2.resize(patch, (w//4, h//4), interpolation=cv2.INTER_AREA)
        patch = cv2.GaussianBlur(patch, (0, 0), 1.5)
        patch = cv2.resize(patch, (w, h), interpolation=cv2.INTER_AREA)
        #patch= pca_filter_scaled(patch)
        #patch=np.clip(patch, 0, bit_depth).astype(np.uint16)

        # Применяем размытие по Гауссу
    blurred_patch = patch.astype(float)
    #blurred_patch = np.stack([
    #    gaussian_filter(patch[:, :, i].astype(float), sigma=0.2, mode='nearest')
    #    for i in range(3)
    #], axis=2)

    #blurred_patch = patch

    # Создаем маску по Гауссу
    #h, w = patch.shape[:2]
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
        # RGB: применяем маску к каждому каналу
        # Извлекаем только замаскированные пиксели
        valid_r = blurred_patch[:, :, 0][mask > 0]
        valid_g = blurred_patch[:, :, 1][mask > 0]
        valid_b = blurred_patch[:, :, 2][mask > 0]

        # Усеченная выборка - убираем тени и пересветы
        p25_r, p90_r = np.percentile(valid_r, [25, 90])
        p25_g, p90_g = np.percentile(valid_g, [25, 90])
        p25_b, p90_b = np.percentile(valid_b, [25, 90])

        clean_r = valid_r[(valid_r >= p25_r) & (valid_r <= p90_r)]
        clean_g = valid_g[(valid_g >= p25_g) & (valid_g <= p90_g)]
        clean_b = valid_b[(valid_b >= p25_b) & (valid_b <= p90_b)]

        # Теперь mean и std считаются от одного и того же "чистого" множества
        mean_r = np.mean(clean_r)
        mean_g = np.mean(clean_g)
        mean_b = np.mean(clean_b)

        std_r = np.std(clean_r, ddof=1)
        std_g = np.std(clean_g, ddof=1)
        std_b = np.std(clean_b, ddof=1)

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
        center_flat = center_patch.reshape(-1, 3)

        # Усеченная выборка для центральных пикселей
        center_r, center_g, center_b = center_flat[:, 0], center_flat[:, 1], center_flat[:, 2]

        p25_cr, p90_cr = np.percentile(center_r, [25, 90])
        p25_cg, p90_cg = np.percentile(center_g, [25, 90])
        p25_cb, p90_cb = np.percentile(center_b, [25, 90])

        clean_center_r = center_r[(center_r >= p25_cr) & (center_r <= p90_cr)]
        clean_center_g = center_g[(center_g >= p25_cg) & (center_g <= p90_cg)]
        clean_center_b = center_b[(center_b >= p25_cb) & (center_b <= p90_cb)]

        median_rgb = np.array([
            np.median(clean_center_r),
            np.median(clean_center_g),
            np.median(clean_center_b)
        ])

    print(f"Mean RGB: {mean_rgb}")
    print(f"Std RGB: {std_rgb}")
    print(f"Median RGB: {median_rgb}")

    return {
        'mean_rgb': mean_rgb,
        'median_rgb': median_rgb,
        'std_rgb': std_rgb
    }


def pca_filter_scaled(patch):
    # Даунскейл
    h0, w0 = patch.shape[:2]
    m = max(w0, h0)
    if m > 64:
        scale = 64 / m
        h_s = int(h0 * scale)
        w_s = int(w0 * scale)
        # Приведение к float32
        # Даунскейл
        small = cv2.resize(patch, (w_s, h_s) ,  interpolation=cv2.INTER_AREA)
        small = small.astype(np.float32)


        # PCA
        h, w, c = small.shape
        reshaped = small.reshape(-1, 3)
        mean = np.mean(reshaped, axis=0)
        centered = reshaped - mean

        U, S, Vt = np.linalg.svd(centered, full_matrices=False)
        pc1 = np.dot(centered, Vt[0])  # первая главная компонента
        patch = np.outer(pc1, Vt[0]) + mean
        patch = patch.reshape(h, w, 3)

        # Апскейл
        patch = cv2.GaussianBlur(patch, (0, 0), 1.5) #1.8
        patch = cv2.resize(patch, (w0, h0),  interpolation=cv2.INTER_CUBIC)

        # Обратное приведение (если надо)
    return patch


def process_large_patch_lab(patch):
    """
    Обработка Lab-патча с использованием взвешенного среднего,
    медианы и стандартного отклонения. Предполагается, что патч
    находится в Lab-пространстве (D50) и передан в виде float массива.
    """

    h, w = patch.shape[:2]

    # Создаём гауссову маску
    mask = gaussian_mask(h, w, sigma_scale=0.33)

    # Извлекаем только замаскированные пиксели
    valid_l = patch[:, :, 0][mask > 0]
    valid_a = patch[:, :, 1][mask > 0]
    valid_b = patch[:, :, 2][mask > 0]

    # Усечённые процентили — применим только к L (контраст)
    p25_l, p90_l = np.percentile(valid_l, [25, 90])
    clean_l = valid_l[(valid_l >= p25_l) & (valid_l <= p90_l)]

    mean_lab = np.array([
        np.mean(clean_l),
        np.mean(valid_a),
        np.mean(valid_b)
    ])

    std_lab = np.array([
        np.std(clean_l, ddof=1),
        np.std(valid_a, ddof=1),
        np.std(valid_b, ddof=1)
    ])

    # Центральная область
    center_radius = int(min(h, w) * 0.3)
    cy, cx = h // 2, w // 2
    y_start = max(0, cy - center_radius)
    y_end = min(h, cy + center_radius)
    x_start = max(0, cx - center_radius)
    x_end = min(w, cx + center_radius)

    center_patch = patch[y_start:y_end, x_start:x_end]
    center_flat = center_patch.reshape(-1, 3)

    # Медиана без усечений (по всем компонентам)
    median_lab = np.median(center_flat, axis=0)

    return {
        'mean_lab': mean_lab,
        'std_lab': std_lab,
        'median_lab': median_lab
    }

def lab_summary_to_rgb(summary_lab, max_val):
    return {
        k.replace('lab', 'rgb'): lab_d50_to_linear_rgb_d50(v, max_val=max_val)
        for k, v in summary_lab.items()
        for k, v in summary_lab.items()
    }


def make_camera_colourspace(cam2xyz: np.ndarray) :
    """
    Создаёт RGB_Colourspace из матрицы camera_to_XYZ.

    Аргументы:
        cam2xyz: np.ndarray 3×3 — матрица преобразования camera RGB → XYZ (в D65)

    Возвращает:
        RGB_Colourspace с нормализованной матрицей, обратной матрицей и D65 whitepoint.
    """
    # Нормализация по сумме Y (второй строки)
    cam2xyz = cam2xyz / cam2xyz[1].sum()
    white_rgb = np.array([1.0, 1.0, 1.0])
    camera_whitepoint = np.dot(cam2xyz, white_rgb)[:3]
    camera_whitepoint = camera_whitepoint / camera_whitepoint[1]

    if cam2xyz.shape == (4, 3):
        xyz_primaries= cam2xyz[:3].T
    else:
        xyz_primaries = cam2xyz.T  # Транспонируем для получения [R_xyz, G_xyz, B_xyz]

    return {
       'name': 'CameraRGB_ForwardOnly',
       'whitepoint': camera_whitepoint,
       'matrix_RGB_to_XYZ': xyz_primaries,
       'matrix_XYZ_to_RGB': None
    }

def rgb_linear_to_lab_d50(rgb_patch, colourspace, max_val):
    """
    Преобразует линейный RGB-патч из произвольного цветового пространства камеры
    в Lab D50 с использованием адаптации Von Kries.

    Parameters:
        rgb_patch : array_like
            Массив из 3 значений (R, G, B) в диапазоне 0–65535 (линейное RGB).
        colourspace : RGB_Colourspace
            Цветовое пространство камеры (с линейной матрицей RGB→XYZ и белой точкой).

    Returns:
        Lab-представление патча, адаптированное к D50.
    """
    # 1. Приводим к диапазону [0, 1]
    rgb = np.clip(np.array(rgb_patch) / max_val, 0.0, 1.0)

    # 2. RGB → XYZ в цвет. пространстве камеры
    xyz_camera_wp = np.einsum('ij,hwj->hwi', colourspace['matrix_RGB_to_XYZ'], rgb)

    # 3. D65 → D50 адаптация
    xyz_d50 = chromatic_adaptation_VonKries(
        xyz_camera_wp,
        colourspace['whitepoint'],
        [0.9642, 1.0000, 0.8251]  # стандартный D50 whitepoint
    )

    # 4. XYZ (D50) → Lab (D50)
    lab = XYZ_to_Lab(xyz_d50, [0.9642, 1.0000, 0.8251])
    return lab


def lab_d50_to_linear_rgb_d50(lab_patch, max_val):
    """
    Преобразует Lab (D50) в линейное RGB D50.
    Остается в D50 - не возвращается в камеру!

    Parameters:
        lab_patch : array_like
            Lab-представление патча (D50 whitepoint).
        max_val : float
            Максимальное значение для выхода (обычно 65535 для 16-bit).

    Returns:
        Массив (R, G, B) в линейном RGB D50, масштабированный к max_val.
    """
    # 1. Lab (D50) → XYZ (D50)
    xyz_d50 = Lab_to_XYZ(lab_patch, [0.9642, 1.0000, 0.8251])

    # 2. XYZ (D50) → Linear RGB (D50)
    # Используем sRGB матрицу, но БЕЗ гамма-коррекции
    rgb_linear_d50 = XYZ_to_RGB(
        XYZ=xyz_d50,
        colourspace=RGB_COLOURSPACES['ProPhoto RGB'],
        illuminant=[0.9642, 1.0000, 0.8251],  # D50 whitepoint
        chromatic_adaptation_transform=None  # Не нужна адаптация, так как источник и цель - D50
    )


    # 3. Масштабируем к нужному диапазону
    rgb_scaled = np.clip(rgb_linear_d50 * max_val, 0, max_val).round().astype(int)
    return rgb_scaled


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


