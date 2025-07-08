
#self.state = {
#    "header": {
#        "pcl_file": None,
#        "ti3_file": None,
#        "current_cht_file": None,
#    },
#    "data": {
#        "chart1.cht": {
#            "image_file": None,
#            "is_parsed": False,
#            "cht_data": None,
#        },
#        ...
#    }
#}

import pickle
from typing import Dict, Optional, Any
from read_cht import parse_cht_file, convert_cht_to_pixels
from pathlib import Path
from PIL import Image

# Qt translation support
def get_translator():
    """Get Qt translator function"""
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            return lambda text, context="RawConverter": app.translate(context, text)
    except ImportError:
        pass
    return lambda text, context="RawConverter": text

# Global translation function
tr = get_translator()

def check_tif_file(cht_file: str) -> bool:
    """Replace extension with .tif and check if file exists"""
    tif_file = Path(cht_file).with_suffix('.tif')
    return tif_file.exists()

# Or if you need path to tif file:
def get_tif_file(cht_file: str) -> str | None:
    """Return path to .tif file if it exists, otherwise None"""
    tif_file = Path(cht_file).with_suffix('.tif')
    return str(tif_file) if tif_file.exists() else None

def get_tiff_physical_size(tiff_path):
    """

    :param tiff_path:
    :return:
        {
            'width_px': 4000,
            'height_px': 6000,
            'dpi_x': 300,
            'dpi_y': 300,
            'width_mm': 338.66,
            'height_mm': 508.0
        }
    """
    with Image.open(tiff_path) as img:
        width_px, height_px = img.size

        # Try to extract DPI (dots per inch)
        dpi = img.info.get('dpi', (300, 300))  # default 300 DPI
        dpi_x, dpi_y = dpi

        # Convert pixels to mm: 1 inch = 25.4 mm
        width_mm = width_px / dpi_x * 25.4
        height_mm = height_px / dpi_y * 25.4

        return {
            "width_px": width_px,
            "height_px": height_px,
            "dpi_x": dpi_x,
            "dpi_y": dpi_y,
            "width_mm": width_mm,
            "height_mm": height_mm
        }

class TargetsManager:
    def __init__(self):
        self.header = {
            "pcl_file": "",
            "ti3_file": "",
            "current_cht_file": "",
        }
        self.data: Dict[str, Dict[str, Any]] = {}

# class storage operations
    def save_as(self, path: str):
        self.header["pcl_file"] = path
        with open(path, "wb") as f:
            pickle.dump({"header": self.header, "data": self.data}, f)

    def save(self):
        path = self.header["pcl_file"]
        with open(path, "wb") as f:
            pickle.dump({"header": self.header, "data": self.data}, f)

    def load(self, path: str):
        with open(path, "rb") as f:
            state = pickle.load(f)
            self.header = state["header"]
            self.data = state["data"]

    def add_cht_file(self, cht_file: str) ->bool:
        """Read cht file and tiff additions. Build cht_data from them,
        return True on success, False on error."""

        if not cht_file:
            print(tr("Empty file name passed to add_cht_file"))
            return False

        spare_tif_file= get_tif_file(cht_file)
        if not spare_tif_file:
            print(tr("Spare TIFF file not found"))
            return False

        data = {
            "image_file": None,
             "is_parsed": False,
             "cht_data": parse_cht_file(cht_file)
         }

        if spare_tif_file:
            try:
                s_size = get_tiff_physical_size(spare_tif_file)
                # Get image width and height
                image_width = s_size["width_px"]
                image_height = s_size["height_px"]
                dpi = s_size["dpi_x"]  # default value
                cht_data = parse_cht_file(cht_file)
                cht_data = convert_cht_to_pixels(cht_data, image_width, image_height, dpi)

                cht_name = Path(cht_file).name
                self.header["current_cht_file"] = cht_name

                if cht_name not in self.data:
                    self.data[cht_name] = {
                        "image_file": None,
                        "is_parsed": False,
                        "cht_data": cht_data
                    }
                else:
                    self.data[cht_name]["is_parsed"] = False
                    self.data[cht_name]["cht_data"] = cht_data
            except Exception as e:
                print(tr("Spare tiff not found: {0}").format(spare_tif_file))
                return False

        return True

# data access
    def drop_cht(self) -> int:
        self.data.pop(self.header["current_cht_file"], None)
        if self.get_size() > 0:
            return self.set_cht("")
        return -1

    def is_has_tiff(self) -> bool:
        current = self.header.get("current_cht_file")
        if not current:
            return False
        entry = self.data.get(current)
        return bool(entry and entry.get("image_file"))

    def set_tiff(self, image_file: str) -> bool:
        try:
            s_size = get_tiff_physical_size(image_file)
            # Get image width and height
            image_width = s_size["width_px"]
            image_height = s_size["height_px"]

            target = self.header.get("current_cht_file")
            self.data[target]["image_file"] = image_file

            # Check bounds
            reference_grid= self.data[target]["reference_grid"]
            margin = 10
            needs_fix = any(
                x < 0 or x >= image_width or y < 0 or y >= image_height
                for x, y in reference_grid.values()
            )

            if needs_fix:
                reference_grid.update({
                    'top_left': (margin, margin),
                    'top_right': (image_width - margin, margin),
                    'bottom_left': (margin, image_height - margin),
                    'bottom_right': (image_width - margin, image_height - margin)
                })
            return True

        except Exception as e:
            print(tr("Error reading tiff: {0}").format(image_file))
            return False

    # data on position
    def get_current_cht_name(self) -> Optional[str]:
        return self.header["current_cht_file"]

    def get_cht_data(self) -> Optional[dict]:
        """Return data from current cht file
        dict {
             "image_file": Str,
             "is_parsed": bool,
             "cht_data": cht_data
             "ref_target_file": Str
             "work_targets": {"ICM": filePath, "LUT": filePath}

             }
             or
             None if something went wrong
        """
        target = self.get_current_cht_name()
        return self.data[target]

# Iterations
    def next_cht(self) -> int:
        if not self.data:
            return -1

        current = self.header.get("current_cht_file")

        if not current or current not in self.data:
            first_key = next(iter(self.data))
            self.header["current_cht_file"] = first_key
            return 0

        keys_iter = iter(self.data.keys())
        for idx, key in enumerate(keys_iter):
            if key == current:
                # Try to get next element
                try:
                    next_key = next(keys_iter)
                    self.header["current_cht_file"] = next_key
                    return idx + 1
                except StopIteration:
                    # Current was the last one
                    return -1

        return -1

    def prev_cht(self) -> int:
        current = self.header.get("current_cht_file")

        if not current or current not in self.data:
            first_key = next(iter(self.data))
            self.header["current_cht_file"] = first_key
            return 0

        # Find previous key in one pass
        prev_key = None
        for idx, key in enumerate(self.data):
            if key == current:
                if prev_key is not None:
                    self.header["current_cht_file"] = prev_key
                    return idx - 1
                else:
                    # Already at first element
                    return -1
            prev_key = key

        return -1

    def set_cht(self, cht_name: str) -> int:
        if not self.data:
            return -1

        keys = list(self.data)

        if not cht_name:
            self.header["current_cht_file"] = keys[0]
            return 0

        # Fastest way - one pass through enumerate
        for idx, key in enumerate(keys):
            if key == cht_name:
                self.header["current_cht_file"] = key
                return idx

        return -1

    # total number of records in data
    def get_size(self) -> int:
        return len(self.data)