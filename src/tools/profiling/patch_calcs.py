import numpy as np
from const import GENERIC_OK, GENERIC_ERROR, QUALITY_COLOURS_16BIT_NON_RELATABLE, QUALITY_COLOURS_16BIT_WORST_CASE

def tr(text):
    """Translation wrapper for Qt5 internationalisation support."""
    return text

_workflows = {
    # POSITIVE WORKFLOWS
    "DCP": {
        'accuracy_weight': 0.5, 'stability_weight': 0.3, 'reliability_weight': 0.2,
        'accuracy_tolerance': 0.01, 'stability_tolerance': 25.0,
        'thresholds': [0.6, 0.7, 0.8, 0.9],
        'delta_e': ["< 1.5 ΔE", "< 2.0 ΔE", "< 3.0 ΔE", "< 4.0 ΔE"],
        'grades': ["A+ PROFESSIONAL", "A HIGH QUALITY", "B+ GOOD", "B ACCEPTABLE"]
    },
    "ICC": {
        'accuracy_weight': 0.6, 'stability_weight': 0.25, 'reliability_weight': 0.15,
        'accuracy_tolerance': 0.008, 'stability_tolerance': 20.0,
        'thresholds': [0.65, 0.75, 0.85, 0.95],
        'delta_e': ["< 1.0 ΔE", "< 1.5 ΔE", "< 2.5 ΔE", "< 3.5 ΔE"],
        'grades': ["A+ PROFESSIONAL", "A HIGH QUALITY", "B+ GOOD", "B ACCEPTABLE"]
    },
    "LUT": {
        'accuracy_weight': 0.4, 'stability_weight': 0.4, 'reliability_weight': 0.2,
        'accuracy_tolerance': 0.012, 'stability_tolerance': 20.0,
        'thresholds': [0.55, 0.65, 0.75, 0.85],
        'delta_e': ["< 2.0 ΔE", "< 3.0 ΔE", "< 4.5 ΔE", "< 6.0 ΔE"],
        'grades': ["A+ EXCELLENT", "A VERY GOOD", "B+ GOOD", "B ACCEPTABLE"]
    },

    "Cineon": {
        'accuracy_weight': 0.4, 'stability_weight': 0.4, 'reliability_weight': 0.2,
        'accuracy_tolerance': 0.012, 'stability_tolerance': 20.0,
        'thresholds': [0.55, 0.65, 0.75, 0.85],
        'delta_e': ["< 2.0 ΔE", "< 3.0 ΔE", "< 4.5 ΔE", "< 6.0 ΔE"],
        'grades': ["A+ EXCELLENT", "A VERY GOOD", "B+ GOOD", "B ACCEPTABLE"]
    },

    # NEGATIVE WORKFLOWS
    "ICC_NEGATIVE": {
        'accuracy_weight': 0.45, 'stability_weight': 0.35, 'reliability_weight': 0.2,
        'accuracy_tolerance': 0.015, 'stability_tolerance': 18.0,
        'thresholds': [0.58, 0.68, 0.78, 0.88],
        'delta_e': ["< 2.5 ΔE", "< 4.0 ΔE", "< 6.0 ΔE", "< 8.0 ΔE"],
        'grades': ["A+ EXCELLENT", "A VERY GOOD", "B+ GOOD", "B NEEDS WORK"]
    },
    "LUT_COLOR_NEG": {
        'accuracy_weight': 0.35, 'stability_weight': 0.45, 'reliability_weight': 0.2,
        'accuracy_tolerance': 0.018, 'stability_tolerance': 15.0,
        'thresholds': [0.52, 0.62, 0.72, 0.82],
        'delta_e': ["< 3.5 ΔE", "< 5.0 ΔE", "< 7.0 ΔE", "< 9.0 ΔE"],
        'grades': ["A+ EXCELLENT", "A VERY GOOD", "B+ GOOD", "B BASIC QUALITY"]
    },
    "LUT_BW_NEG": {
        'accuracy_weight': 0.3, 'stability_weight': 0.5, 'reliability_weight': 0.2,
        'accuracy_tolerance': 0.020, 'stability_tolerance': 12.0,  # Stricter noise tolerance
        'thresholds': [0.50, 0.60, 0.70, 0.80],
        'delta_e': ["Excellent tonal range", "Very good tones", "Good tones", "Basic quality"],
        'grades': ["A+ ARCHIVAL", "A PROFESSIONAL", "B+ GOOD", "B AMATEUR"]
    }
}

_patch_workflows = {
        # ===== POSITIVE (DIGITAL) WORKFLOWS =====
        "DCP": {
            'delta_weight': 0.4,  # Colour accuracy (normalized_delta)
            'noise_weight': 0.3,  # Uniformity (std_rgb) - strict
            'edge_weight': 0.2,  # Structure (edge_score)
            'reliable_weight': 0.1,  # Reliability (reliable)

            'delta_tolerance': 0.004,
            'noise_tolerance': 8.0,  # Strict threshold for digital
            'edge_tolerance': 0.1,
            'thresholds': [0.6, 0.7, 0.8, 0.9]
        },

        "ICC": {
            'delta_weight': 0.5, 'noise_weight': 0.25, 'edge_weight': 0.15, 'reliable_weight': 0.1,
            'delta_tolerance': 0.003, 'noise_tolerance': 6.0, 'edge_tolerance': 0.08,
            'thresholds': [0.65, 0.75, 0.85, 0.95]
        },

        "LUT": {
            'delta_weight': 0.35, 'noise_weight': 0.35, 'edge_weight': 0.2, 'reliable_weight': 0.1,
            'delta_tolerance': 0.005, 'noise_tolerance': 10.0, 'edge_tolerance': 0.12,
            'thresholds': [0.55, 0.65, 0.75, 0.85]
        },

        "Cineon": {
            'delta_weight': 0.35, 'noise_weight': 0.35, 'edge_weight': 0.2, 'reliable_weight': 0.1,
            'delta_tolerance': 0.005, 'noise_tolerance': 10.0, 'edge_tolerance': 0.12,
            'thresholds': [0.55, 0.65, 0.75, 0.85]
        },

    # ===== NEGATIVE (FILM) WORKFLOWS =====
        "ICC_NEGATIVE": {
            'delta_weight': 0.4, 'noise_weight': 0.2, 'edge_weight': 0.3, 'reliable_weight': 0.1,
            'delta_tolerance': 0.006, 'noise_tolerance': 18.0, 'edge_tolerance': 0.15,  # Softer for film
            'thresholds': [0.58, 0.68, 0.78, 0.58]
        },

        "LUT_COLOUR_NEG": {  # Colour negative
            'delta_weight': 0.35, 'noise_weight': 0.2, 'edge_weight': 0.35, 'reliable_weight': 0.1,
            'delta_tolerance': 0.007, 'noise_tolerance': 20.0, 'edge_tolerance': 0.18,
            'thresholds': [0.52, 0.62, 0.72, 0.82]
        },

        "LUT_BW_NEG": {  # Black and white negative - softest thresholds for grain
            'delta_weight': 0.4, 'noise_weight': 0.15, 'edge_weight': 0.35, 'reliable_weight': 0.1,
            'delta_tolerance': 0.008, 'noise_tolerance': 25.0, 'edge_tolerance': 0.20,  # Very soft for grain
            'thresholds': [0.50, 0.60, 0.70, 0.80]
        }
    }

def nrgb_to_qrgb(rgb_tuple):
    """
    Convert normalised RGB tuple to QRgb format
    Args:
        rgb_tuple: tuple/list of normalised RGB values (0.0-1.0)
    Returns:
        int: QRgb value (0xFFRRGGBB)
    """
    # Convert to 8-bit and pack into QRgb
    r, g, b = (np.clip(rgb_tuple, 0, 1) * 255).astype(int)
    return (255 << 24) | (r << 16) | (g << 8) | b



def expected_artifact_quality(patch_data, is_negative=False, artifact_type="DCP"):
    """
    Universal quality prediction for all color management artifacts
    [остальной docstring без изменений]
    """
    try:
        # Define workflow categories
        negative_workflows = ["ICC_NEGATIVE", "LUT_COLOR_NEG", "LUT_BW_NEG"]
        positive_workflows = ["DCP", "ICC", "LUT", "LUT_BW"]

        # Auto-conversion BEFORE validation
        if is_negative and artifact_type in positive_workflows:
            conversion_map = {
                "ICC": "ICC_NEGATIVE",
                "LUT": "LUT_COLOR_NEG",
                "LUT_BW": "LUT_BW_NEG",
                "DCP": "ICC_NEGATIVE"  # DCP -> ICC_NEGATIVE fallback
            }
            artifact_type = conversion_map.get(artifact_type, "ICC_NEGATIVE")
            print(f"Auto-converted to negative workflow: {artifact_type}")

        # Validation AFTER auto-conversion
        if is_negative and artifact_type not in negative_workflows:
            raise ValueError(f"Invalid negative workflow: {artifact_type}. Use: {negative_workflows}")
        if not is_negative and artifact_type not in positive_workflows:
            raise ValueError(f"Invalid positive workflow: {artifact_type}. Use: {positive_workflows}")


        analysis = _analyze_patch_measurement_quality(patch_data)  #
        quality = _predict_workflow_quality(analysis, artifact_type)

        # Format text strings
        m_analysis_text = _format_measurement_analysis(analysis)
        q_results_text = _format_quality_results(quality, artifact_type)

        result = {
            "data": quality,
            "m_analysis": m_analysis_text,
            "q_results": q_results_text
        }

        return GENERIC_OK, result

    except Exception as e:
        print(f"Error: {e}")
        return GENERIC_ERROR, {}


def _analyze_patch_measurement_quality(patch_data):
    """
    Analyze patch measurement quality from patch_data

    Args:
        patch_data (list): List of patch measurements with RGB values
    Returns:
        dict: Analysis results with quality metrics
    """


    # Extract RGB values from patch data
    rgb_values = []
    reliable_count = 0

    for patch in patch_data:
        if 'mean_rgb' in patch and patch['mean_rgb'] is not None:
            rgb = patch['mean_rgb']
            if isinstance(rgb, np.ndarray) and rgb.size == 3:
                rgb_values.append(rgb)
                if not (all(c == 0 for c in rgb) or all(c == 255 for c in rgb)):
                    reliable_count += 1

    if not rgb_values:
        return {
            'patch_count': len(patch_data),
            'reliable_patches': 0,
            'reliability_rate': 0.0,
            'mean_accuracy': 1.0,
            'stability_rgb': [100.0, 100.0, 100.0],
            'rgb_range': [0.0, 0.0],
            'dynamic_range': 1.0
        }

    rgb_array = np.array(rgb_values, dtype=np.float64)

    # Calculate statistics
    patch_count = len(patch_data)
    reliability_rate = reliable_count / patch_count if patch_count > 0 else 0.0

    # Mean accuracy (normalized deviation from expected values)
    # Simple approximation: lower std deviation = higher accuracy
    mean_rgb_std = np.mean(np.std(rgb_array, axis=0))
    mean_accuracy = mean_rgb_std / 65535  # Normalize to 0-1 range

    # Stability per channel (RGB standard deviation)
    stability_rgb = np.std(rgb_array, axis=0).tolist()

    # Dynamic range
    rgb_min = np.min(rgb_array)
    rgb_max = np.max(rgb_array)
    rgb_range = [float(rgb_min), float(rgb_max)]
    min_divisor = rgb_min if rgb_min > 1.0 else 1.0
    dynamic_range = rgb_max / min_divisor     # Avoid division by zero

    return {
        'patch_count': patch_count,
        'reliable_patches': reliable_count,
        'reliability_rate': reliability_rate,
        'mean_accuracy': mean_accuracy,
        'stability_rgb': stability_rgb,
        'rgb_range': rgb_range,
        'dynamic_range': dynamic_range
    }


def _predict_workflow_quality(analysis, workflow_type):
    """
    Workflow-specific quality prediction with tailored thresholds
    """
    # Define workflow-specific parameters

    params = _workflows[workflow_type]

    # Calculate normalized scores
    accuracy_norm = min(1.0, max(0.0, (params['accuracy_tolerance'] - analysis['mean_accuracy']) / (
                params['accuracy_tolerance'] * 0.9)))
    stability_norm = min(1.0, max(0.0, (params['stability_tolerance'] - max(analysis['stability_rgb'])) / (
                params['stability_tolerance'] * 0.8)))
    reliability_norm = analysis['reliability_rate']

    # Weighted overall score
    overall_score = (
            accuracy_norm * params['accuracy_weight'] +
            stability_norm * params['stability_weight'] +
            reliability_norm * params['reliability_weight']
    )

    # Determine quality grade
    grade_index = 3  # Default to lowest grade
    for i, threshold in enumerate(params['thresholds']):
        if overall_score <= threshold:
            grade_index = i
            break

    # Generate workflow-specific recommendations
    use_cases, recommendations = _get_workflow_recommendations(workflow_type, grade_index, overall_score)

    return {
        'score': overall_score,
        'grade': params['grades'][grade_index],
        'delta_e_expected': params['delta_e'][grade_index],
        'use_case': use_cases[grade_index] if grade_index < len(use_cases) else "Limited use",
        'recommendation': recommendations[grade_index] if grade_index < len(recommendations) else "Needs improvement",
        'workflow_type': workflow_type,
        'detailed_scores': {
            'accuracy': accuracy_norm,
            'stability': stability_norm,
            'reliability': reliability_norm
        },
        'workflow_notes': _get_workflow_specific_notes(workflow_type)
    }


def _get_workflow_recommendations(workflow_type, grade_index, score):
    """
    Get workflow-specific use cases and recommendations
    """
    recommendations_map = {
        "DCP": {
            'use_cases': [
                "Commercial RAW processing, Capture One workflow",
                "Professional photography, Adobe Camera Raw",
                "Amateur photography, general RAW editing",
                "Basic RAW processing, social media"
            ],
            'recommendations': [
                "Excellent DCP profile, use for all camera work",
                "Very good profile for professional workflows",
                "Suitable for most photography applications",
                "Usable but consider lighting improvements"
            ]
        },
        "ICC": {
            'use_cases': [
                "Commercial printing, critical color matching",
                "Professional photography, fine art printing",
                "General photography, web publishing",
                "Basic photo editing, amateur use"
            ],
            'recommendations': [
                "Perfect ICC profile for professional work",
                "Excellent for color-critical applications",
                "Good for general photography workflows",
                "Consider measurement improvements"
            ]
        },
        "LUT": {
            'use_cases': [
                "Professional color grading, cinema workflow",
                "Commercial photography, advertising",
                "Content creation, social media",
                "Basic color correction"
            ],
            'recommendations': [
                "Perfect LUT for professional color grading",
                "Excellent for commercial applications",
                "Good for creative workflows",
                "Basic quality, suitable for simple tasks"
            ]
        },
        "ICC_NEGATIVE": {
            'use_cases': [
                "Professional film scanning, archival work",
                "Commercial film digitization",
                "Personal film conversion projects",
                "Basic film scanning"
            ],
            'recommendations': [
                "Excellent for C1 negative workflow",
                "Very good for professional film work",
                "Suitable for most film conversion needs",
                "Consider improving scan conditions"
            ]
        },
        "LUT_COLOR_NEG": {
            'use_cases': [
                "Professional film restoration, cinema",
                "Commercial film digitization, broadcast",
                "Personal film projects, social sharing",
                "Basic film conversion"
            ],
            'recommendations': [
                "Perfect for Cineon/Luminar/LR negative workflow",
                "Excellent for professional film digitization",
                "Good for amateur film conversion projects",
                "Basic quality, check lighting setup"
            ]
        },
        "LUT_BW_NEG": {
            'use_cases': [
                "Archival B&W film digitization",
                "Professional B&W photography workflow",
                "Personal B&W film projects",
                "Basic B&W negative conversion"
            ],
            'recommendations': [
                "Excellent tonal reproduction, archival quality",
                "Professional B&W workflow ready",
                "Good for personal B&W film projects",
                "Basic quality, consider noise reduction"
            ]
        }
    }

    workflow_data = recommendations_map.get(workflow_type, {
        'use_cases': ["General use"] * 4,
        'recommendations': ["Check workflow configuration"] * 4
    })

    return workflow_data['use_cases'], workflow_data['recommendations']


def _get_workflow_specific_notes(workflow_type):
    """
    Provide workflow-specific technical notes
    """
    notes_map = {
        "DCP": {
            'software_compatibility': "Adobe Camera Raw, Lightroom, Capture One",
            'file_format': ".dcp profile file",
            'installation': "Camera Profiles folder",
            'critical_factors': ["Consistent lighting", "Proper exposure", "Color temperature accuracy"]
        },
        "ICC": {
            'software_compatibility': "Photoshop, Capture One, most photo editors",
            'file_format': ".icc/.icm profile file",
            'installation': "System color profiles folder",
            'critical_factors': ["Monitor calibration", "Viewing conditions", "Profile embedding"]
        },
        "LUT": {
            'software_compatibility': "DaVinci Resolve, Premiere Pro, FCPX, Luminar",
            'file_format': ".cube/.3dl LUT file",
            'installation': "Application LUT folders",
            'critical_factors': ["Consistent grading setup", "Monitor calibration", "Viewing environment"]
        },
        "ICC_NEGATIVE": {
            'software_compatibility': "Capture One (Film mode), Photoshop",
            'file_format': ".icc profile + inversion workflow",
            'installation': "C1 Film profiles or system profiles",
            'critical_factors': ["Light table color temperature", "Negative flatness", "Dust-free scanning"]
        },
        "LUT_COLOR_NEG": {
            'software_compatibility': "Cineon tools, Luminar Neo, Lightroom",
            'file_format': ".cube LUT with inversion",
            'installation': "Application-specific LUT folders",
            'critical_factors': ["Known light source temperature", "Orange mask consistency", "Grain vs noise"]
        },
        "LUT_BW_NEG": {
            'software_compatibility': "B&W processing software, general editors",
            'file_format': ".cube LUT for tonal mapping",
            'installation': "LUT folders or manual application",
            'critical_factors': ["Consistent negative density", "Film grain preservation", "Tonal range coverage"]
        }
    }

    return notes_map.get(workflow_type, {})


def _format_measurement_analysis(analysis):
    """Format measurement quality analysis as text string"""
    lines = []
    lines.append(f"{tr('Patches analyzed')}: {analysis['patch_count']}")
    lines.append(
        f"{tr('Reliable measurements')}: {analysis['reliable_patches']} ({analysis['reliability_rate'] * 100:.1f}%)")
    lines.append(f"{tr('Average measurement error')}: {analysis['mean_accuracy']:.6f}")
    lines.append(
        f"{tr('Measurement stability (RGB std)')}: ({analysis['stability_rgb'][0]:.2f}, {analysis['stability_rgb'][1]:.2f}, {analysis['stability_rgb'][2]:.2f})")
    lines.append(
        f"{tr('Dynamic range')}: {analysis['rgb_range'][0]:.1f} - {analysis['rgb_range'][1]:.1f} ({analysis['dynamic_range']:.1f}:1)")

    return '\n'.join(lines)


def _format_quality_results(quality, artifact_type):
    """Format quality prediction results as text string"""

    lines = []
    lines.append(f"{tr('EXPECTED')} {artifact_type} {tr('QUALITY')}:")
    lines.append(f"   {tr('Overall grade')}: {quality['grade']}")
    lines.append(f"   {tr('Expected accuracy')}: {quality['delta_e_expected']}")
    lines.append(f"   {tr('Best use case')}: {quality['use_case']}")
    lines.append(f"   {tr('Recommendation')}: {quality['recommendation']}")

    if 'workflow_notes' in quality and quality['workflow_notes']:
        notes = quality['workflow_notes']
        lines.append("")
        lines.append(f"{tr('WORKFLOW TECHNICAL NOTES')}:")
        lines.append(f"   {tr('Software')}: {notes.get('software_compatibility', 'N/A')}")
        lines.append(f"   {tr('File format')}: {notes.get('file_format', 'N/A')}")

        critical_factors = notes.get('critical_factors', [])
        if critical_factors:
            lines.append(f"   {tr('Critical factors')}: {', '.join(critical_factors)}")

    return '\n'.join(lines)


def evaluate_patches_quality(patches, workflow="DCP") -> tuple[int,list[tuple[int,int,int]]]:
    """
    Quality of patches considering workflow
    4 components: accuracy + noise + structure + reliability
    """

    rez = []
    for patch in patches:
        params = _patch_workflows.get(workflow, _patch_workflows[workflow])

        # Normalisation of all 4 metrics
        delta_norm = max(0.0, 1.0 - (patch['normalized_delta'] / params['delta_tolerance']))
        noise_norm = max(0.0, 1.0 - (np.mean(patch['std_rgb']) / params['noise_tolerance']))
        edge_norm = max(0.0, 1.0 - (patch['edge_score'] / params['edge_tolerance']))
        reliable_norm = 1.0 if patch['reliable'] else 0.0

        # Overall weighted score
        overall_score = (
                delta_norm * params['delta_weight'] +
                noise_norm * params['noise_weight'] +
                edge_norm * params['edge_weight'] +
                reliable_norm * params['reliable_weight']
        )

        # Colour index (0=green, 4=red)

        colour_index = QUALITY_COLOURS_16BIT_WORST_CASE
        for i, threshold in enumerate(params['thresholds']):
            if not patch['reliable']:
                colour_index = QUALITY_COLOURS_16BIT_NON_RELATABLE
            if overall_score <= threshold:
                colour_index = i
                break
        # colour_index, overall_score
        rez.append([colour_index, nrgb_to_qrgb(patch['mean_rgb_n']), nrgb_to_qrgb(patch['median_rgb_n'])])

    return GENERIC_OK, rez


def evaluate_patch_components(patch: dict, workflow: str = "DCP") -> tuple[int,dict]:
    """
    Input: patch result with fields mean_rgb, std_rgb, normalized_delta, reliable, edge_score
    Output: map with component colour indices
    """
    params = _patch_workflows.get(workflow, _patch_workflows["DCP"])

    # Normalise components from input data
    delta_norm = max(0.0, 1.0 - (patch['normalized_delta'] / params['delta_tolerance']))
    noise_norm = max(0.0, 1.0 - (np.mean(patch['std_rgb']) / params['noise_tolerance']))
    edge_norm = max(0.0, 1.0 - (patch['edge_score'] / params['edge_tolerance']))
    reliable_norm = 1.0 if patch['reliable'] else 0.0

    def get_colour_index(score: float) -> int:
        for i, threshold in enumerate(params['thresholds']):
            if score >= threshold:
                return i
        return 4

    # Return map with colour indices for actual fields from patch_result
    return GENERIC_OK, {
        'normalized_delta': get_colour_index(delta_norm),
        'std_rgb': get_colour_index(noise_norm),
        'edge_score': get_colour_index(edge_norm),
        'reliable': get_colour_index(reliable_norm)
    }

# USAGE EXAMPLES:
# Positive workflows:
# dcp_quality = analyze_positive_workflow_quality(patch_data, "DCP")
# icc_quality = analyze_positive_workflow_quality(patch_data, "ICC")
# lut_quality = analyze_positive_workflow_quality(patch_data, "LUT")

# Negative workflows:
# c1_negative = analyze_negative_workflow_quality(patch_data, "ICC_NEGATIVE")
# color_neg_lut = analyze_negative_workflow_quality(patch_data, "LUT_COLOR_NEG")
# bw_neg_lut = analyze_negative_workflow_quality(patch_data, "LUT_BW_NEG")