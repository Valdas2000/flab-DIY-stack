
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
import copy
import re
import os
import traceback
from pathlib import Path

import numpy as np
from PIL import Image
from typing import Dict, Optional, Any

from const import GENERIC_ERROR, GENERIC_OK
from read_cht import parse_cht_file
from cht_data_calcs import convert_cht_to_pixels
from raw_converter import convert_raw_batch
from patch_analyse import analyze_patches
from patch_calcs import evaluate_patches_quality

# Qt translation support
def get_translator():
    """Get Qt translator function"""
    try:
        from PySide6.QtWidgets import QApplication
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
    def __init__(self, create_new_project_dict: dict|None = None):
        self.header = {
            "argyll_path": "",
            "pcl_name": "",
            "color_ref": "",
            "remake": { },
            "image_options": { },
            "outputs": [],
            'markers':[''],         # No markers by default

            "current_cht_file": "",
        }
        self.data: Dict[str, Dict[str, Any]] = {}
        self._c_data = {}

        self.conv={"ICC":"ICC","DCP":"DCP","LUT":"LUT","Cineon":"Cineon"}

        if create_new_project_dict:
            self.parce_init(create_new_project_dict)


    def parce_init(self,new_project_dict):
        self.header["argyll_path"]= new_project_dict["argyll_path"]
        self.header["pcl_name"] = new_project_dict["pcl_name"]
        self.header["color_ref"] = new_project_dict["color_ref"]
        self.header["remake"] = new_project_dict["remake"]
        self.header["outputs"] = new_project_dict["outputs"]                # the list target artifacts like ICC, LUT etc
        self.header["image_options"] = new_project_dict["image_options"]

        conversions = []

        for conversion in self.header["outputs"]:
            conversions.append(self.conv[conversion])
        if not conversions:
            conversions.append("icc")

        self.header["conversions"] = list(set(conversions))                 # the RAW conversion types need to builf the ["outputs"]

        cht = new_project_dict["targets"]["cht_names"]
        self.header['markers'] = new_project_dict["targets"]["markers"]
        for cht_name in cht:
            self.add_cht_file(cht_name)

        self.set_cht("")
        return True

# class storage operations

    def save(self):
        path = self.header["pcl_name"]
        with open(path, "wb") as f:
            pickle.dump({"header": self.header, "data": self.data}, f)

    def load(self, path: str):
        with open(path, "rb") as f:
            state = pickle.load(f)
            self.header = state["header"]
            self.data = state["data"]
            key = self.header["current_cht_file"]
            if key not in self.data:
                key = next(iter(self.data))
            self._c_data = self.data[key]

            directory = os.path.dirname(path)
            os.chdir(directory)


    def get_project_name(self):
        return self.header["pcl_name"]

    def add_cht_file(self, cht_file: str) ->bool:
        """Read cht file and tiff additions. Build cht_data from them,
        return True on success, False on error."""
        from create_target_preview import create_color_target_tiff , resize_tiff_to_96dpi
        if not cht_file:
            print(tr("Empty file name passed to add_cht_file"))
            return False

        ret, cht_data = parse_cht_file(cht_file)
        if ret != GENERIC_OK:
            print(tr("Error: parsing error: {0}").format(cht_file))
            return False

        # create a preview file based on cht or on the original target
        spare_tif_file= get_tif_file(cht_file)
        cht_file_path = Path(cht_file)
        cht_name = cht_file_path.stem
        preview_file = cht_name + "_preview.tif"
        if  spare_tif_file:
            resize_tiff_to_96dpi(spare_tif_file, preview_file)
        else:
            create_color_target_tiff(cht_data, preview_file, cht_file_path.stem)

        spare_tif_file = preview_file

        s_size = get_tiff_physical_size(spare_tif_file)
        # Get image width and height
        image_width = s_size["width_px"]
        image_height = s_size["height_px"]
        dpi = s_size["dpi_x"]  # default value

        ret = convert_cht_to_pixels(cht_data, image_width, image_height, dpi)
        data = {
            "image_file": None,
            "preview_file": preview_file,
            "is_parsed": False,
            "file_name" : Path(cht_file).name,
            "cht_data": cht_data
         }

        if ret == GENERIC_OK:
            range_names = cht_data['range_names']
            name = first = range_names[0]
            # Извлекаем буквенную часть из первого элемента
            first_letters = re.match(r'([A-Za-z]+)', first).group(1)
            # Ищем первое вхождение с отличающейся буквенной частью
            for item in range_names[1:]:
                item_letters = re.match(r'([A-Za-z]+)', item).group(1)
                if item_letters != first_letters:
                    name =  f"{first_letters}-{item_letters}"
                    break

            if not self.header.get('markers', None):
                self.header['markers'] = ['']

            for marker in self.header['markers']:
                nme = f"{name} {marker}"
                self.data[nme] = copy.deepcopy(data)
                self.data[nme]['tag']= marker

        return True

    def get_outputs(self):
        """Provide the list of target artifacts of the project (ICC, LUT ....)"""
        return self.header.get("outputs")

    # data access
    def drop_cht(self) -> int:
        self.data.pop(self.header["current_cht_file"], None)
        if self.get_size() > 0:
            return self.set_cht("")
        return -1

    def get_tif_demo_file(self) -> tuple[int, str]:
        """Return path to .tif file if it exists, otherwise None"""
        if not self._c_data:
            print(tr("No current cht file selected"))
            return GENERIC_ERROR,""
        return GENERIC_OK, self._c_data["preview_file"]

    def is_has_tiff(self) -> bool:
        if not self._c_data:
            return False
        return bool(self._c_data and self._c_data.get("image_file"))

    def get_tif_file(self, output: str|None) -> tuple[int, str]:
        ret, metadata = self.get_tiff_file_metadata()
        if ret != GENERIC_OK:
            return GENERIC_ERROR, ""
        if not output:
            output = metadata["file_selection"]
        conv = self.conv.get(output,"icc")
        metadata["file_selection"] = output
        return GENERIC_OK, metadata["output_files"][conv]

    def get_tiff_file_metadata(self) -> tuple[int,Dict[str, Any]]:
        if not self.is_has_tiff:
            return GENERIC_ERROR,{}
        return GENERIC_OK, self._c_data["image_file"]

    def is_fiff_parsed(self):
        return self._c_data.get("is_parsed", False)

    def get_tif_patches_quality(self, flow):
        if not self.is_fiff_parsed():
            return GENERIC_ERROR,[]
        internal_flow_name = self.conv.get(flow,"")
        if internal_flow_name:
            metadata = self.get_tiff_file_metadata()[1]
            return GENERIC_OK, metadata["patches_quality"].get(internal_flow_name, [])
        print(tr("Unknown flow type: {0}").format(flow))
        return GENERIC_ERROR,[]

    def get_tif_patches_quality_byId(self, flow_id):
        if not self.is_fiff_parsed():
            return GENERIC_ERROR,[]
        flow = ""
        internal_flow_name = ""
        try:
            flow = self.header["outputs"][flow_id]
            internal_flow_name = self.conv.get(flow,"")
            metadata = self.get_tiff_file_metadata()[1]
            return GENERIC_OK, metadata["patches_quality"][internal_flow_name]
        except KeyError:
            print(tr("Unknown flow type: {0}").format(internal_flow_name))
        except IndexError:
            print(tr("Index value {0} is out of scope").format(flow_id))
        return GENERIC_ERROR,[]

    def get_current_output(self) -> tuple [int, str, int]:
        """in case of success return GENERIC_OK. current output type, and the type index in outputs list"""
        if not self.is_has_tiff():
            return GENERIC_ERROR, "", -1
        output = self._c_data["image_file"]["file_selection"]
        if not output:
            return GENERIC_OK, "", -1
        return GENERIC_OK, output, self.get_outputs().index(output)

    def get_tif_file_name(self):
        if not self.is_has_tiff():
            return GENERIC_ERROR,""
        return GENERIC_OK, self._c_data["image_file"]["original_file"]

    def set_tiff(self, image_file: str) -> bool:
        try:
            if not self._c_data:
                print(tr("No current cht file selected"))
                return False
            ret, metadata = convert_raw_batch(image_file, "./", self.header["conversions"])
            if ret != GENERIC_OK:
                return False

            file_name = str(Path(image_file).name)
            mdata = metadata.get(file_name)
            if not metadata:
                return False
            mdata["file_selection"] = self.header["outputs"][0]
            mdata["original_file"] = file_name
            image_width = mdata["width"]
            image_height = mdata["height"]

            self._c_data["image_file"] = mdata
            convert_cht_to_pixels(self._c_data['cht_data'],image_width,image_height)
            self._c_data['patch_scale'] = 100   # reset patch scale to initial value
            return True

        except Exception as e:
            print(tr("Error reading tiff: {0}").format(image_file))
            traceback.print_exc()
            return False

    # data on position
    def get_current_cht_name(self) -> Optional[str]:
        return self.header["current_cht_file"]

    def get_current_cht_data(self) -> Optional[dict]:
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
        return self._c_data

    def get_current_cht(self):
        return  self.header["current_cht_file"]


# Iterations
    def next_cht(self) -> int:
        if not self.data:
            return -1

        current = self.header.get("current_cht_file")

        if not current or current not in self.data:
            first_key = next(iter(self.data))
            self.header["current_cht_file"] = first_key
            self._c_data=self.data[first_key]
            return 0

        keys_iter = iter(self.data.keys())
        for idx, key in enumerate(keys_iter):
            if key == current:
                # Try to get next element
                try:
                    next_key = next(keys_iter)
                    self.header["current_cht_file"] = next_key
                    self._c_data = self.data[next_key]
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
            self._c_data=self.data[first_key]
            return 0

        # Find previous key in one pass
        prev_key = None
        for idx, key in enumerate(self.data):
            if key == current:
                if prev_key is not None:
                    self.header["current_cht_file"] = prev_key
                    self._c_data = self.data[prev_key]
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
            self._c_data=self.data[keys[0]]
            return 0

        # Fastest way - one pass through enumerate
        for idx, key in enumerate(keys):
            if key == cht_name:
                self.header["current_cht_file"] = key
                self._c_data = self.data[key]
                return idx

        return -1

    # total number of records in data
    def get_size(self) -> int:
        return len(self.data)

    def read_analyse_current_cht(self):
        if not self.is_has_tiff():
            return GENERIC_ERROR, ""
        try:
            points = self._c_data["cht_data"]["points"]
            wh = self._c_data["cht_data"]["patch_wh"]
            metadata = self.get_tiff_file_metadata()[1]
            files = metadata["output_files"]
            rez, read_data = analyze_patches(points, wh, files, self.get_tiff_file_metadata()[1])
            if rez == GENERIC_OK:
                metadata["patches"] = read_data
                # analyze patches quality
                patches_quality={}
                for key, data in read_data.items():
                    rez, qa = evaluate_patches_quality(data, key)
                    patches_quality[key]=qa
                metadata["patches_quality"] = patches_quality

                self._c_data["is_parsed"] = True
                return rez
        except Exception as e:
            print(tr("Error reading tiff: {0}").format(e))
            traceback.print_exc()
            self._c_data["is_parsed"] = False

        return GENERIC_ERROR

    def get_patches_current_cht(self, flow):
        metadata = self.get_tiff_file_metadata()[1]
        return metadata["patches"][flow]

    # the function is to be enhanced to multitarget
    def get_patch_map_current_cht(self, flow):
        patches = self.get_patches_current_cht(flow)
        patch_dict = self.get_current_cht_data()["cht_data"]["patch_dict"]
        rez = {}
        rez_lst = [None] * len(patch_dict)
        try:
            for key, p_info in patch_dict.items():
                idx = p_info["array_idx"]
                rez[key] = {
                    "xyz": p_info["xyz"],
                    'mean_rgb': patches[idx]['mean_rgb'],
                    'median_rgb': patches[idx]['median_rgb'],
                }
                rez_lst[idx] = patches[idx]['mean_rgb'] * 255

        except KeyError:
            print(tr("Unknown flow type: {0}").format(flow))
        return rez

    def get_cht_array(self, tag_name, flow = None):
        # join cht data in a dict
        rez = {}
        from ti3_calcs import xyz_to_lab

        for key, data in self.data.items():
            if data["tag"] != tag_name:
                continue

            patches = data["cht_data"]["patch_dict"]
            metadata = data.get("image_file", None)
            flow_id = self.conv.get(flow, None)
            is_read = bool(metadata and flow and flow_id)

            if is_read and flow_id not in metadata['patches'].keys():
                print(tr("No flow type: {0}").format(flow))
                continue

            for p_id, patch in patches.items():
                xyz = np.array([patch["xyz"]['X'],patch["xyz"]['Y'],patch["xyz"]['Z']])
                row_idx = patch['array_idx']
                rez[p_id] = {
                     "xyz": xyz,
                     "lab": xyz_to_lab(xyz, 'D65')
                }
                if is_read:
                    data = metadata['patches'][flow_id][row_idx]
                    rez[p_id].update(data)

        return GENERIC_OK, rez
