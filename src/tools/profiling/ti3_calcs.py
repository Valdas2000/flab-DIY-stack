import numpy as np
from scipy.spatial.distance import euclidean


def xyz_to_lab(xyz, illuminant='D65'):
    """Конвертация XYZ в LAB"""
    # Референсные белые точки
    illuminants = {
        'D65': [95.047, 100.000, 108.883],
        'D50': [96.422, 100.000, 82.521]
    }

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


def _calculate_color_difference(ref_lab, measured_xyz):
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

    return {
        'delta_e_76': delta_e_76,
        'delta_e_94': delta_e_94,
        'delta_L': delta_L,
        'delta_a': delta_a,
        'delta_b': delta_b,
        'measured_lab': measured_lab
    }


def analyze_color_accuracy(data):
    """Анализ точности цветопередачи"""
    patches = data['patches']       # got list of dicts there 'lab_scaner' reference colors tuple 'xyz_target' measured_colors
    results = []
    for i, patch in enumerate(patches):
        patch_result = _calculate_color_difference(patch['lab_scaner'], patch['xyz_target'])
        patch['lab_scaner_QA'] = patch_result
        results.append(patch_result)

    # Общая статистика
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
    data['lab_scaner_QA_summary'] = statistics

    return results, statistics