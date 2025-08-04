import numpy as np
from scipy.spatial.distance import euclidean

illuminants = {
    'D65': [95.047, 100.000, 108.883],
    'D50': [96.422, 100.000, 82.521],
    'CUS': [89.18831, 92.43061, 75.24555]
}

def normalize_patch_data(rgb_data, stdev_data, xyz_data, target_max=100.0, white_xyz=(100.0, 100.0, 100.0), eps=1e-3):
    rgb = np.array(rgb_data, dtype=float)
    stdev = np.array(stdev_data, dtype=float)
    xyz = np.array(xyz_data, dtype=float)

    # Находим "белые" патчи — те, у кого XYZ близко к 100,100,100
    white_mask = np.all(np.abs(xyz - white_xyz) < eps, axis=1)
    if not np.any(white_mask):
        raise ValueError("Не найдено ни одного белого патча с XYZ = 100,100,100")

    # Получаем RGB этих патчей
    white_rgbs = rgb[white_mask]

    # Выбираем наибольший max(R,G,B) среди них
    max_channel = np.max(white_rgbs, axis=1)  # по каждому патчу
    reference_rgb_max = np.max(max_channel)

    # Вычисляем масштаб
    scale = target_max / reference_rgb_max

    # Применяем масштаб к RGB и stddev
    rgb_scaled = (rgb * scale).round(2)
    stdev_scaled = np.clip(stdev * scale, 0.1, 10.0).round(1)

    return rgb_scaled, stdev_scaled

def _normalize_patch_data(rgb_data, stdev_data, white_idx, target_max=100):
    """
    Компактная нормализация всех данных патчей для ArgyllCMS
    """
    # Конвертируем в numpy массивы
    white_rgb = np.array(rgb_data[white_idx])
    rgb, stdev = np.array(rgb_data, dtype=float), np.array(stdev_data, dtype=float)

    # Единый масштаб по максимальному RGB
    scale = target_max / np.max(white_rgb)

    # Нормализуем все сразу
    return (rgb * scale).round(2), np.clip(stdev * scale, 0.1, 10.0).round(1)


# Пример использования для пикселей изображения:
# pixels = [(r1,g1,b1), (r2,g2,b2), ...]  # ваши RGB значения 0-65535
# normalized = normalize_rgb_preserve_color(pixels, 100)

def chromatic_adaptation_brdf(xyz, src_white, dst_white):
    """Bradford адаптация XYZ из src_wp → dst_wp
    xyz_d50 = chromatic_adaptation_brdf(xyz_d65, src_white, dst_white)
    """
    # Bradford адаптационная матрица
    src_wp = np.array(src_white)  / 100.0
    dst_wp = np.array(dst_white) / 100.0

    M = np.array([
        [ 0.8951,  0.2664, -0.1614],
        [-0.7502,  1.7135,  0.0367],
        [ 0.0389, -0.0685,  1.0296]
    ])
    M_inv = np.linalg.inv(M)

    # В LMS-пространство
    src_lms = M @ src_wp
    dst_lms = M @ dst_wp
    D = np.diag(dst_lms / src_lms)  # масштабирование

    # Итоговая матрица адаптации
    adapt_matrix = M_inv @ D @ M

    # Применяем адаптацию
    return xyz @ adapt_matrix.T


def xyz_to_lab(xyz, illuminant='D65'):
    """Конвертация XYZ в LAB"""
    # Референсные белые точки

    xyz_n = np.array(illuminants[illuminant])
    xyz_norm = xyz / xyz_n

    # Функция f(t)
    def f(t):
        return np.where(t > (6 / 29) ** 3,
                        np.power(t, 1 / 3),
                        (1 / 3) * ((29 / 6) ** 2) * t + (4 / 29))

    fx, fy, fz = f(xyz_norm[0]), f(xyz_norm[1]), f(xyz_norm[2])

    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)

    return np.array([L, a, b])


def _calculate_color_difference(ref_lab, measured_xyz, wb_color_space='D65'):
    """Рассчет цветовых различий"""
    # Конвертируем XYZ в LAB
    measured_lab = xyz_to_lab(measured_xyz)

    # Delta E (CIE76 - простая евклидова дистанция)
    delta_e_76 = np.sqrt(
        (ref_lab[0] - measured_lab[0]) ** 2 +
        (ref_lab[1] - measured_lab[1]) ** 2 +
        (ref_lab[2] - measured_lab[2]) ** 2
    )

    # Delta E (CIE94 - взвешенная)
    delta_L = ref_lab[0] - measured_lab[0]
    delta_a = ref_lab[1] - measured_lab[1]
    delta_b = ref_lab[2] - measured_lab[2]

    C1 = np.sqrt(ref_lab[1] ** 2 + ref_lab[2] ** 2)
    C2 = np.sqrt(measured_lab[1] ** 2 + measured_lab[2] ** 2)
    delta_C = C1 - C2
    delta_H = np.sqrt(delta_a ** 2 + delta_b ** 2 - delta_C ** 2)

    SL = 1
    SC = 1 + 0.045 * C1
    SH = 1 + 0.015 * C1

    delta_e_94 = np.sqrt(
        (delta_L / SL) ** 2 +
        (delta_C / SC) ** 2 +
        (delta_H / SH) ** 2
    )

    # Gray drift
    # Gray points: L is the same, A=0, B=0
    gray_drift_delta_e = np.sqrt(
        (ref_lab[1] - 0) ** 2 +
        (ref_lab[2] - 0) ** 2
    )

    return {
        'delta_e_76': delta_e_76,
        'delta_e_94': delta_e_94,
        'delta_L': delta_L,
        'delta_a': delta_a,
        'delta_b': delta_b,
        'measured_lab': measured_lab,
        'gray_drift': gray_drift_delta_e
    }


def analyze_color_accuracy(data, wb_color_space='D65') :
    """Анализ точности цветопередачи и отклонения от серого"""
    patches = data['patches']  # got list of dicts there 'lab_reference_m' reference colors tuple 'xyz_target' measured_colors
    results = []

    for i, patch in enumerate(patches):
        patch_result = _calculate_color_difference(patch['lab_reference_m'], patch['xyz_target'], wb_color_space)
        patch['lab_reference_QA'] = patch_result
        results.append(patch_result)

    # Общая статистика точности цветопередачи
    delta_e_values = [r['delta_e_94'] for r in results]

    statistics = {
        'mean_delta_e': np.mean(delta_e_values),
        'max_delta_e': np.max(delta_e_values),
        'min_delta_e': np.min(delta_e_values),
        'std_delta_e': np.std(delta_e_values),
        'patches_over_1': sum(1 for de in delta_e_values if de > 1.0),
        'patches_over_3': sum(1 for de in delta_e_values if de > 3.0),
        'patches_over_6': sum(1 for de in delta_e_values if de > 6.0)
    }
    data['lab_reference_QA_summary'] = statistics

    # Статистика отклонения от серого и равномерности
    # Используем delta_a и delta_b из уже вычисленных результатов
    a_values = [r['delta_a'] for r in results]
    b_values = [r['delta_b'] for r in results]

    # Средний сдвиг (общее направление)
    mean_a = np.mean(a_values)
    mean_b = np.mean(b_values)

    # Величина общего сдвига
    overall_drift = np.sqrt(mean_a ** 2 + mean_b ** 2)

    # Равномерность - насколько каждый патч отклоняется от общего направления
    deviations = []
    for a, b in zip(a_values, b_values):
        # Отклонение от среднего направления
        dev_a = a - mean_a
        dev_b = b - mean_b
        deviation = np.sqrt(dev_a ** 2 + dev_b ** 2)
        deviations.append(deviation)

    gray_drift_statistics = {
        'overall_drift': overall_drift,
        'drift_direction_a': mean_a,
        'drift_direction_b': mean_b,
        'uniformity_rms': np.sqrt(np.mean(np.array(deviations) ** 2)),
        'uniformity_max': np.max(deviations),
        'uniformity_std': np.std(deviations),
        'patches_uniformity_over_1': sum(1 for dev in deviations if dev > 1.0),
        'patches_uniformity_over_3': sum(1 for dev in deviations if dev > 3.0),
        'patches_uniformity_over_6': sum(1 for dev in deviations if dev > 6.0)
    }
    data['gray_drift_summary'] = gray_drift_statistics
