#B&W

#printtarg -v -h -i i1 -p 210x148 -M 2 -C -L -S -a 1.07 -b -T 610 -R 2 reverse_bw220_a5_target
#scanin -v -p -dipn reverse_bw220_a5_target.tif reverse_bw220_a5_target.cht reverse_bw220_a5_target.ti2


#printtarg -v -h -i i1 -p 210x148 -M 2 -C -L -S -a 1.07 -b -T 610 -R 2  reverse_bw220_a5_target

# targen -v -d2 -G -g200 -e10 -B12 -f0 reverse_gray_rgb
# printtarg -v -h -i i1 -p 210x148 -M 2 -C -L -S -a 1.07 -b -T 610 -R 3  reverse_gray_rgb
# cctiff -v -p -f T -N -i r FOMEI_Baryta_MONO_290_PIXMA_G540_PPPL_HQ_RB4.icm  -i a sRGB.icm reverse_gray_rgb.tif reverse_gray_rgb_barita.tif

# scanin -v -p -dipn reverse_gray_rgb.tif reverse_bw220_a5_target.cht reverse_bw220_a5_target.ti2

#💡 Рекомендации по выбору -R
# Тип	Цель	Критерий выбора -R
# Ч/Б (grayscale)	Линейность градаций	direction ΔE в диапазоне 12–18, worst ΔE < 2
# Цветной (RGB)	Различимость цветов и серого	direction ΔE ≥ 20, worst ΔE < 3

import copy
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QApplication
from PySide6.QtCore import Qt, QPointF
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QResizeEvent, QMouseEvent, QPainter, QBrush, QPen, QCursor, QFont
from PySide6.QtGui import QImage, QColor
import numpy as np
import math
from const import GENERIC_OK, QUALITY_COLOURS_16BIT


class InteractiveGraphicsView(QGraphicsView):
    resized = pyqtSignal()  # Signal for size change (can be bound to redraw)
    mouse_moved = pyqtSignal(QPointF)
    mouse_clicked = pyqtSignal(QPointF)
    mouse_released = pyqtSignal(QPointF)
    mouse_dragged = pyqtSignal(QPointF)

    # New signals for reference point dragging
    corner_drag_started = pyqtSignal(int)    # (corner_idx)
    corner_drag_finished = pyqtSignal(int)   # (corner_idx)
    corner_position_changed = pyqtSignal(int, QPointF)  # (corner_idx, new_position)


    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setRenderHint(QPainter.RenderHints.Antialiasing)
        self.setMouseTracking(True)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

        self._dragging = False
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # Add attribute for brightness
        self._background_image = None  # can be set via set_background_image()
        self._original_image_array = None  # Store original numpy array
        self._is_fit_mode = True  # Fit mode by default

        self._grid_drawer = None       # can be set to object with draw(painter, rect) method
        self.show_patches = False
        self.show_colors = False
        self.show_patches_ref = False
        self.show_colors_ref = False

        self.uv = np.array([], dtype=np.float32)
        self.uv_wh = np.array([], dtype=np.float32)

        self.points = []
        self.patch_wh = []
        self.half_patch = []
        self.corner = []
        self.rgb = []
        self.patches_quality  = []
        self.range_names = None
        self.range_idx = None
        self.patch_scale =  100

        self.gridpoint_radius_ref = 5
        self.gridpoint_radius = self.gridpoint_radius_ref
        self.gridpoint_diameter = self.gridpoint_radius * 2
        self.gridpoint_color =  Qt.GlobalColor.yellow

        self.corner_radius_ref = 10
        self.corner_radius = self.corner_radius_ref
        self.corner_diameter = self.corner_radius * 2
        self.corner_color = Qt.GlobalColor.green

        self.patch_linewidth_ref = 4
        self.patch_linewidth = self.patch_linewidth_ref
        self.patch_color = Qt.GlobalColor.cyan
        self.patch_pen = QPen(self.patch_color, self.patch_linewidth)

        self.solid_brush = QBrush()
        self.solid_brush.setStyle(Qt.SolidPattern)

        self.no_brush = QBrush()

        self.font_size_ref = 24
        self.font_size = self.font_size_ref

        # Reference point drag state (as in old code)
        self.dragging = False
        self.dragged_corner = None          # corner index


        # Capture and visual feedback parameters
        self.corner_area_ref = 25
        self.corner_area = self.corner_area_ref  # Area around reference point for capture
        self.corner_on_drag_color = Qt.GlobalColor.red  # Point color during drag
        self.corner_idx = None            # corner index

    def set_background_image(self, img_array, record , is_demo = True,  background_brightness: int = 100):
        """Get an image as a NumPy-array, converts it and save for future use."""
        cht_data = record["cht_data"]
        height, width = img_array.shape[:2]
        self._original_image_array = img_array.copy()
        self._update_qimage_from_array(img_array)

        self.uv = copy.copy(cht_data['uv'])  # disable any updates for the parametric_uv
        self.uv_wh = copy.copy(cht_data['uv_wh'])  # disable any updates for the parametric_uv

        if is_demo:
            self.points = copy.copy(cht_data['points'])
            self.patch_wh= copy.copy(cht_data['patch_wh'])
            self.corner = cht_data['corner_demo']
        else :
            self.points = cht_data['points']
            self.patch_wh= cht_data['patch_wh']
            self.corner = cht_data['corner']

        self.half_patch  = copy.copy(self.patch_wh) / 2

        self.rgb = cht_data['RGB']

        from cht_data_calcs import adopt_corner_target
        adopt_corner_target(self.corner, width , height)

        self.patch_scale= cht_data['patch_scale']
        self.show_patches_ref = self.show_patches= record.get('is_draw_patches', False)
        self.show_colors_ref = self.show_colors= record.get('is_draw_colors', False)
        self.corner_idx= None

        self.range_names = copy.copy(cht_data['range_names'])
        self.range_idx = []
        for patch_name in self.range_names:
            self.range_idx.append(cht_data['patch_dict'][patch_name]['array_idx'])

        self._scene.setSceneRect(0, 0, width, height)  # Key line
        # self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

        self.zoom_to_fit()
        self.update_view()

        self.apply_grid_transform()
        self.update_brightness(background_brightness)
        # is not need because update_brightness is alredy does it
        # self.update_view(background_changed=True)


    def set_show_patches(self, is_draw_patches):
        if self.show_patches == is_draw_patches:
            return
        self.show_patches_ref = self.show_patches = is_draw_patches
        self.update_view()

    def set_show_patches_quality(self, patches_quality: list[int] | None):
        self.patches_quality = patches_quality
        self.update_view()


    def set_show_colors(self, is_show_colors):
        if self.show_colors == is_show_colors:
            return
        self.show_colors_ref = self.show_colors = is_show_colors
        self.update_view()


    def set_patch_scale(self, patch_scale):
        if self.patch_scale == patch_scale:
            return
        self.patch_scale = patch_scale
        self.apply_grid_transform()
        self.update_view()


    def _update_qimage_from_array(self, img_array):
        """Creates QImage from numpy array."""
        if img_array.ndim == 2:  # Grayscale
            height, width = img_array.shape
            self._background_image = QImage(img_array.data, width, height, QImage.Format_Grayscale8)
        elif img_array.shape[2] == 3:  # RGB
            height, width, _ = img_array.shape
            self._background_image = QImage(img_array.data, width, height, 3 * width, QImage.Format_RGB888)
        elif img_array.shape[2] == 4:  # RGBA
            height, width, _ = img_array.shape
            self._background_image = QImage(img_array.data, width, height, 4 * width, QImage.Format_RGBA8888)
        else:
            raise ValueError("Unsupported image format")

        self._background_image = self._background_image.copy()

    def update_brightness(self, brightness_factor):
        """Updates brightness of background image through numpy.

        Args:
            brightness_factor (float): Brightness factor (0.0 - 2.0)
        """
        if self._original_image_array is None:
            return

        brightness_value = brightness_factor / 100.0

        # Apply brightness to original array - FAST!
        import numpy as np
        img_array = self._original_image_array * brightness_value
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)

        # Create new QImage
        self._update_qimage_from_array(img_array)

        # Update display
        self.update_view(background_changed=True)

    def clear_background(self):
        """Removes current background and updates display."""
        if self._background_image:
            self._scene.setBackgroundBrush(QBrush(Qt.GlobalColor.white))
        self._background_image = None
        self.uv = np.array([], dtype=np.float32)

        self.resetTransform()
        self.viewport().update()

    def set_grid_drawer(self, drawer):
        """drawer should have draw(painter, rect) method."""
        self._grid_drawer = drawer
        self.viewport().update()

    def draw_patch_centers_foreground(self, painter, rect):
        """Draw patch centers in foreground."""
        if self.uv is None or self.uv.size == 0:
            return

        # Set up brush ONCE
        painter.setPen(self.gridpoint_color)
        painter.setBrush(QBrush(self.gridpoint_color))

        # Draw circles WITHOUT unnecessary calculations
        for idx, (x, y) in enumerate(self.points):
            painter.drawEllipse(int(x) - self.gridpoint_radius , int(y) - self.gridpoint_radius , self.gridpoint_diameter, self.gridpoint_diameter)

    def draw_corner_points_foreground(self, painter, rect):
        """Draw corner points in foreground."""
        if self.uv is None or self.uv.size == 0:
            return

        # Set up brush ONCE
        painter.setPen(self.corner_color)
        painter.setBrush(QBrush(self.corner_color))

        # Draw circles WITHOUT unnecessary calculations
        for idx, (x, y) in enumerate(self.corner):
            painter.drawEllipse(int(x) - self.corner_radius, int(y) - self.corner_radius, self.corner_diameter, self.corner_diameter)

    def draw_labels_foreground(self, painter, rect):
        """Draw patch labels with scaling."""
        if self.uv is None or self.uv.size == 0:
            return

        painter.setPen(self.patch_pen)
        painter.setBrush(Qt.NoBrush)

        # Общий масштаб = масштаб сцены * масштаб патчей

        font = QFont()
        font.setPointSize(self.font_size)
        painter.setFont(font)

        for idx, lbl in enumerate(self.range_names):
            patch_idx = self.range_idx[idx]
            w2, h2 = (self.half_patch[patch_idx]).astype(int)
            x, y = self.points[patch_idx]

            painter.drawText(int(x-w2), int(y-h2-self.font_size//4), lbl)

    def draw_patches_foreground(self, painter, rect):
        """Draw patch boundaries in foreground."""
        if self.uv is None or self.uv.size == 0:
            return

        # Set up brush for specific point
        painter.setPen(self.patch_pen)
        painter.setBrush(Qt.NoBrush)

        for idx, (x, y) in enumerate(self.points):
            w2, h2 = (self.half_patch[idx]).astype(int)
            w, h = (self.patch_wh[idx]).astype(int)
            painter.drawRect(int(x - w2), int(y - h2), w, h )

    def draw_colors_foreground(self, painter, rect):
        """Draw patch boundaries in foreground."""
        if self.uv is None or self.uv.size == 0:
            return

        # Set up brush for specific point
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.solid_brush)
        temp_color = QColor()

        for idx, (x, y) in enumerate(self.points):
            color = int(self.rgb[idx])
            w2, h2 = (self.half_patch[idx]).astype(int)
            temp_color.setRgb(color)
            self.solid_brush.setColor(temp_color)
            painter.setBrush(self.solid_brush)
            painter.drawRect(int(x - w2), int(y - h2), w2, h2 )

    def draw_risks_foreground(self, painter, rect):
        """Draw patch boundaries in foreground."""
        if self.uv is None or self.uv.size == 0:
            return
        if not self.patches_quality:
            return

        painter.setPen(Qt.NoPen)
        painter.setBrush(self.solid_brush)
        temp_color = QColor()

        for idx, (x, y) in enumerate(self.points):
            color = int(QUALITY_COLOURS_16BIT[self.patches_quality[idx][0]])
            w2, h2 = (self.half_patch[idx]).astype(int)
            temp_color.setRgb(color)
            self.solid_brush.setColor(temp_color)
            painter.setBrush(self.solid_brush)
            painter.drawRect(int(x), int(y), w2, h2 )

            color = self.patches_quality[idx][1]
            w2, h2 = (self.half_patch[idx]).astype(int)
            temp_color.setRgb(color)
            self.solid_brush.setColor(temp_color)
            painter.setBrush(self.solid_brush)
            painter.drawRect(int(x)-w2, int(y), w2, h2 )


            color = self.patches_quality[idx][2]
            w2, h2 = (self.half_patch[idx]).astype(int)
            temp_color.setRgb(color)
            self.solid_brush.setColor(temp_color)
            painter.setBrush(self.solid_brush)
            painter.drawRect(int(x), int(y)-h2, w2, h2 )




    def find_nearest_corner(self, scene_pos) -> int | None:
            """Find nearest reference point within tolerance zone.

            Args:
                scene_pos (QPointF): Mouse position in scene coordinates

            Returns:
                str or None: Reference point name or None if not found
            """
            if self.uv is None or self.uv.size == 0:
                return None

            idx = 0
            for idx, (x, y) in enumerate(self.corner):
                distance = ((scene_pos.x() - x) ** 2 + (scene_pos.y() - y) ** 2) ** 0.5
                if distance <= self.corner_area:
                    return idx
                idx += 1

            return None

    def update_cursor_for_corner(self, corner_idx):
        """Update cursor depending on hover state.

        Args:
            corner_name (str or None): Name of reference point under cursor
        """
        if corner_idx is not None:
            # Hovering over reference point - "hand" cursor
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            self.corner_idx = corner_idx
        elif not self.dragging:
            # Normal cursor
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.corner_idx = None

    def start_corner_drag(self, corner_idx: int):
        """Start dragging reference point.

        Args:
            corner_name (str): Reference point name
        """
        self.dragging = True
        self.dragged_corner = corner_idx

        # Change cursor to "move"
        self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

        # Remember patch display state and hide them
        if self.show_patches and self.is_fit_scale():
            self.show_patches = False

        # Update display
        self.viewport().update()

        # Notify about drag start
        self.corner_drag_started.emit(corner_idx)

    def update_corner_position(self, corner_idx, new_position):
        """Update reference point position during drag.

        Args:
            corner_idx (int): Reference point name
            new_position (QPointF): New position
        """
        self.corner[corner_idx][:] = [new_position.x(), new_position.y()]

        # Recalculate patch centers
        self.apply_grid_transform()

        # Update display
        self.viewport().update()

        # Notify about position change
        self.corner_position_changed.emit(corner_idx, new_position)

    def finish_corner_drag(self):
        """Finish dragging reference point."""
        if self.dragging and self.dragged_corner is not None:
            # Return cursor to normal
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

            # Restore patch display state
            self.show_patches = self.show_patches_ref
            self.show_colors = self.show_colors_ref

            # Update display
            self.viewport().update()

            # Notify about drag finish
            self.corner_drag_finished.emit(self.dragged_corner)

            self.dragging = False
            self.dragged_corner = None

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        if self._background_image:
            # self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            if self._is_fit_mode:
                self.zoom_to_fit()

        self.resized.emit()
        # self.viewport().update()

    def mouseMoveEvent(self, event):
        """Mouse move event handler (analog of on_motion + on_hover)."""
        scene_pos = self.mapToScene(event.pos())

        if self.dragging and self.dragged_corner is not None:
            # Analog of on_motion - update position of dragged point
            self.update_corner_position(self.dragged_corner, scene_pos)
            # Notify about dragging
            self.mouse_dragged.emit(scene_pos)
        else:
            # Analog of on_hover - check hover over reference point
            idx = self.find_nearest_corner(scene_pos)
            self.update_cursor_for_corner(idx)
            # Notify about mouse movement
            self.mouse_moved.emit(scene_pos)

        # Standard behavior for other cases
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """Mouse press event handler (analog of on_click)."""
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())

            # Check if user clicked on reference point
            idx = self.find_nearest_corner(scene_pos)
            if idx is not None:
                # Start dragging reference point
                self.start_corner_drag(idx)
                # Notify about click
                self.mouse_clicked.emit(scene_pos)
                return  # Don't call standard behavior

        # Standard behavior for other cases
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Mouse release event handler (analog of on_release)."""
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())

            if self.dragging:
                # Finish dragging reference point
                self.finish_corner_drag()
                # Notify about release
                self.mouse_released.emit(scene_pos)
                return  # Don't call standard behavior

        # Standard behavior for other cases
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        """Mouse leave event handler."""
        # Reset hover state when mouse leaves
        if not self.dragging:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.corner_idx = None

        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Double click event handler - toggle fit/100%."""
        if self.dragging:
            # Block during dragging
            return

        if not self._background_image:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())

            if self._is_fit_mode:
                self.zoom_to_100_percent(scene_pos)
            else:
                self.zoom_to_fit()

        # Don't call super() to avoid conflicts

    def wheelEvent(self, event):
        """Mouse wheel event handler - scaling with point anchoring."""
        if self.dragging:
            # Block scaling during dragging
            return

        if not self._background_image:
            return

        # Get mouse point in scene coordinates
        scene_pos = self.mapToScene(event.position().toPoint())

        # Determine scroll direction
        if event.angleDelta().y() > 0:
            # Wheel up - zoom in
            self.zoom_to_point(scene_pos, 1.25)
        else:
            # Wheel down - zoom out
            self.zoom_to_point(scene_pos, 1.0 / 1.25)

        visible_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        self.apply_grid_transform()
        self.scene().update(visible_rect)


    def apply_grid_transform(self):
        """Recalculate grid_linear based on current reference_grid and pre-prepared UV."""
        if self.uv is None or self.uv.size == 0:
            return

        from cht_data_calcs import compute_patch_wh_aligned
        ret, centers, wh = compute_patch_wh_aligned(self.uv, self.uv_wh, self.corner, self.patch_scale)
        if ret == GENERIC_OK:
            self.points[:] = centers
            self.patch_wh[:] = wh
            self.half_patch[:] =  wh / 2

        # Minimum scale
        c_scale = self.get_current_scale()
        image_scale = max(1., -math.log2(c_scale))

        self.gridpoint_radius = int(self.gridpoint_radius_ref * image_scale)
        self.gridpoint_diameter = self.gridpoint_radius * 2
        self.gridpoint_color =  Qt.GlobalColor.yellow

        self.corner_radius = int(self.corner_radius_ref * image_scale)
        self.corner_diameter = self.corner_radius * 2

        self.patch_linewidth = int(self.patch_linewidth_ref * image_scale)
        self.patch_pen = QPen(self.patch_color, self.patch_linewidth)

        self.font_size = int(self.font_size_ref * image_scale)
        self.corner_area = int(self.corner_area_ref * image_scale) # Area around reference point for capture


    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if self._background_image:
            painter.drawImage(0, 0, self._background_image)

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)

        if self._grid_drawer:
            self._grid_drawer.draw(painter, rect)

        # no foreground for empty data
        if self.uv is None or self.uv.size == 0:
            return

        # Draw patch centers
        self.draw_patch_centers_foreground(painter, rect)

        # Draw corner points
        self.draw_corner_points_foreground(painter, rect)

        # Draw patches
        if self.show_patches:
            self.draw_patches_foreground(painter, rect)

        if self.show_colors:
            self.draw_colors_foreground(painter, rect)

        self.draw_risks_foreground(painter, rect)

        self.draw_labels_foreground(painter, rect)

    def get_current_scale(self):
        """Get current view scale."""
        return self.transform().m11()

    def get_fit_scale(self):
        """Calculate scale for fitInView."""
        if not self._background_image:
            return 1.0

        scene_rect = self._scene.sceneRect()
        view_rect = self.viewport().rect()

        scale_x = view_rect.width() / scene_rect.width()
        scale_y = view_rect.height() / scene_rect.height()

        return min(scale_x, scale_y)

    def is_fit_scale(self):
        """Check if view is in fitInView mode."""
        if not self._background_image:
            return True

        current_scale = self.get_current_scale()
        fit_scale = self.get_fit_scale()

        # Allow small tolerance
        return abs(current_scale - fit_scale) < 0.01

    def zoom_to_point(self, scene_point, scale_factor):
        """Scale view with point anchoring.

        Args:
            scene_point (QPointF): Point in scene coordinates
            scale_factor (float): Scale factor
        """
        # Get current scale
        current_scale = self.get_current_scale()
        new_scale = current_scale * scale_factor

        # Check boundaries
        fit_scale = self.get_fit_scale()
        max_scale = 1.0  # 100%

        if new_scale > max_scale:
            new_scale = max_scale
        elif new_scale < fit_scale:
            new_scale = fit_scale

        # If scale hasn't changed, exit
        if abs(new_scale - current_scale) < 0.01:
            return

        # Apply scale
        actual_factor = new_scale / current_scale
        self.scale(actual_factor, actual_factor)

        # Center on point
        self.centerOn(scene_point)

        # If exited fit mode, update flag
        if self._is_fit_mode:
            fit_scale = self.get_fit_scale()
            if abs(self.get_current_scale() - fit_scale) > 0.01:
                self._is_fit_mode = False

    def zoom_to_fit(self):
        """Set fitInView mode."""
        if not self._background_image:
            return

        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._is_fit_mode = True

    def zoom_to_100_percent(self, scene_point):
        """Set 100% scale with point anchoring.

        Args:
            scene_point (QPointF): Point in scene coordinates
        """
        if not self._background_image:
            return

        # Reset transformation
        self.resetTransform()

        # Center on point
        self.centerOn(scene_point)
        self._is_fit_mode = False

    def update_view(self, background_changed=False):
        # Here you can add logic for redrawing background and grid
        if background_changed:
            # full update
            self.viewport().update()
        else:
            # fast update
            visible_rect = self.mapToScene(self.viewport().rect()).boundingRect()
            self.scene().update(visible_rect)

