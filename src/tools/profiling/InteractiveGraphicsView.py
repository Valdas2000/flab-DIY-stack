
import copy
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import QResizeEvent, QMouseEvent, QPainter, QBrush, QPen, QCursor
from PyQt5.QtGui import QImage


class InteractiveGraphicsView(QGraphicsView):
    resized = pyqtSignal()  # Signal for size change (can be bound to redraw)
    mouse_moved = pyqtSignal(QPointF)
    mouse_clicked = pyqtSignal(QPointF)
    mouse_released = pyqtSignal(QPointF)
    mouse_dragged = pyqtSignal(QPointF)

    # New signals for reference point dragging
    corner_drag_started = pyqtSignal(str)    # (corner_name)
    corner_drag_finished = pyqtSignal(str)   # (corner_name)
    corner_position_changed = pyqtSignal(str, QPointF)  # (corner_name, new_position)


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

        self.parametric_uv = []
        self.patch_centers = []
        self.patch_size = []
        self.reference_grid = {}
        self.patch_scale =  100

        self.gridpoint_radius = 3
        self.gridpoint_diameter = self.gridpoint_radius * 2
        self.gridpoint_color =  Qt.GlobalColor.yellow

        self.corner_radius = 5
        self.corner_diameter = self.corner_radius * 2
        self.corner_color = Qt.GlobalColor.green

        self.patch_linewidth = 2
        self.patch_color = Qt.GlobalColor.cyan
        self.patch_pen = QPen(self.patch_color, self.patch_linewidth)

        # Reference point drag state (as in old code)
        self.dragging = False
        self.dragged_corner = None
        self.original_patches_state = False

        # Capture and visual feedback parameters
        self.corner_area = 25  # Area around reference point for capture
        self.corner_on_drag_color = Qt.GlobalColor.red  # Point color during drag
        self.hover_corner = None

    def set_background_image(self, img_array, cht_data , background_brightness: int):
        """Get an image as a NumPy-array, converts it and save for future use."""
        self._original_image_array = img_array.copy()
        self._update_qimage_from_array(img_array)

        self.parametric_uv = copy.copy(cht_data['parametric_uv'])  # disable any updates for the parametric_uv
        self.patch_centers = cht_data['grid_linear']
        self.patch_size =  cht_data['patch_size']
        self.reference_grid = cht_data['reference_grid']
        self.patch_scale=cht_data['patch_scale']
        self.show_patches=cht_data.get('is_draw_patches', False)

        self._scene.setSceneRect(0, 0, self._background_image.width(), self._background_image.height())  # Key line
        # self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

        self.zoom_to_fit()

        self.apply_grid_transform()
        self.viewport().update()

    def set_show_patches(self, is_draw_patches):
        if self.show_patches == is_draw_patches:
            return
        self.show_patches = is_draw_patches
        self.viewport().update()

    def set_patch_scale(self, patch_scale):
        if self.patch_scale == patch_scale:
            return
        self.patch_scale = patch_scale
        if self.show_patches:
            self.viewport().update()

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
        self.viewport().update()

    def clear_background(self):
        """Removes current background and updates display."""
        if self._background_image:
            self._scene.setBackgroundBrush(QBrush(Qt.GlobalColor.white))
        self._background_image = None
        self.parametric_uv = []

        self.resetTransform()
        self.viewport().update()

    def set_grid_drawer(self, drawer):
        """drawer should have draw(painter, rect) method."""
        self._grid_drawer = drawer
        self.viewport().update()

    def draw_patch_centers_foreground(self, painter, rect):
        """Draw patch centers in foreground."""
        if not self.patch_centers:
            return

        # Set up brush ONCE
        painter.setPen(self.gridpoint_color)
        painter.setBrush(QBrush(self.gridpoint_color))

        # Draw circles WITHOUT unnecessary calculations
        for x, y in self.patch_centers:
            painter.drawEllipse(int(x) - self.gridpoint_radius , int(y) - self.gridpoint_radius , self.gridpoint_diameter, self.gridpoint_diameter)

    def draw_corner_points_foreground(self, painter, rect):
        """Draw corner points in foreground."""
        if not self.reference_grid:
            return

        # Set up brush ONCE
        painter.setPen(self.corner_color)
        painter.setBrush(QBrush(self.corner_color))

        # Draw circles WITHOUT unnecessary calculations
        for corner_name, (x, y) in self.reference_grid.items():
            painter.drawEllipse(int(x) - self.corner_radius, int(y) - self.corner_radius, self.corner_diameter, self.corner_diameter)

    def draw_patches_foreground(self, painter, rect):
        """Draw patch boundaries in foreground."""
        if not self.patch_centers or not self.patch_size:
            return

        # Calculate sizes ONCE
        patch_width, patch_height = self.patch_size
        scaled_width = int(patch_width * self.patch_scale) // 100
        scaled_height = int(patch_height * self.patch_scale) // 100
        half_width = scaled_width >> 1  # Bit shift is faster than division
        half_height = scaled_height >> 1

        # Set up brush for specific point
        painter.setPen(self.patch_pen)
        painter.setBrush(Qt.NoBrush)

        # Draw rectangle based on center coordinates
        for x, y in self.patch_centers:
            painter.drawRect(int(x) - half_width, int(y) - half_height,
                     scaled_width, scaled_height)

    def find_nearest_corner(self, scene_pos):
            """Find nearest reference point within tolerance zone.

            Args:
                scene_pos (QPointF): Mouse position in scene coordinates

            Returns:
                str or None: Reference point name or None if not found
            """
            if not self.reference_grid:
                return None

            for corner_name, (x, y) in self.reference_grid.items():
                distance = ((scene_pos.x() - x) ** 2 + (scene_pos.y() - y) ** 2) ** 0.5
                if distance <= self.corner_area:
                    return corner_name
            return None

    def update_cursor_for_corner(self, corner_name):
        """Update cursor depending on hover state.

        Args:
            corner_name (str or None): Name of reference point under cursor
        """
        if corner_name and not self.dragging:
            # Hovering over reference point - "hand" cursor
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            self.hover_corner = corner_name
        elif not self.dragging:
            # Normal cursor
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.hover_corner = None

    def start_corner_drag(self, corner_name):
        """Start dragging reference point.

        Args:
            corner_name (str): Reference point name
        """
        self.dragging = True
        self.dragged_corner = corner_name

        # Change cursor to "move"
        self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

        # Remember patch display state and hide them
        self.original_patches_state = self.show_patches
        if self.show_patches and self.is_fit_scale():
            self.show_patches = False

        # Update display
        self.viewport().update()

        # Notify about drag start
        self.corner_drag_started.emit(corner_name)

    def update_corner_position(self, corner_name, new_position):
        """Update reference point position during drag.

        Args:
            corner_name (str): Reference point name
            new_position (QPointF): New position
        """
        if corner_name in self.reference_grid:
            self.reference_grid[corner_name] = (new_position.x(), new_position.y())

            # Recalculate patch centers
            self.apply_grid_transform()

            # Update display
            self.viewport().update()

            # Notify about position change
            self.corner_position_changed.emit(corner_name, new_position)

    def finish_corner_drag(self):
        """Finish dragging reference point."""
        if self.dragging and self.dragged_corner:
            # Return cursor to normal
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

            # Restore patch display state
            self.show_patches = self.original_patches_state

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

        if self.dragging and self.dragged_corner:
            # Analog of on_motion - update position of dragged point
            self.update_corner_position(self.dragged_corner, scene_pos)
            # Notify about dragging
            self.mouse_dragged.emit(scene_pos)
        else:
            # Analog of on_hover - check hover over reference point
            corner = self.find_nearest_corner(scene_pos)
            self.update_cursor_for_corner(corner)
            # Notify about mouse movement
            self.mouse_moved.emit(scene_pos)

        # Standard behavior for other cases
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """Mouse press event handler (analog of on_click)."""
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())

            # Check if user clicked on reference point
            corner = self.find_nearest_corner(scene_pos)
            if corner:
                # Start dragging reference point
                self.start_corner_drag(corner)
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
            self.hover_corner = None

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
        scene_pos = self.mapToScene(event.pos())

        # Determine scroll direction
        if event.angleDelta().y() > 0:
            # Wheel up - zoom in
            self.zoom_to_point(scene_pos, 1.25)
        else:
            # Wheel down - zoom out
            self.zoom_to_point(scene_pos, 1.0 / 1.25)

    def apply_grid_transform(self):
        """Recalculate grid_linear based on current reference_grid and pre-prepared UV."""
        if  not self.parametric_uv:
            return
        print("apply_grid_transform")
        tl = self.reference_grid['top_left']
        tr = self.reference_grid['top_right']
        bl = self.reference_grid['bottom_left']
        br = self.reference_grid['bottom_right']

        new_centers = []
        for u, v in self.parametric_uv:
            x = (
                    (1 - u) * (1 - v) * tl[0] +
                    u * (1 - v) * tr[0] +
                    (1 - u) * v * bl[0] +
                    u * v * br[0]
            )
            y = (
                    (1 - u) * (1 - v) * tl[1] +
                    u * (1 - v) * tr[1] +
                    (1 - u) * v * bl[1] +
                    u * v * br[1]
            )
            new_centers.append((x, y))

        # Replace contents of existing list
        self.patch_centers[:] = new_centers

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if self._background_image:
            painter.drawImage(0, 0, self._background_image)

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)

        if self._grid_drawer:
            self._grid_drawer.draw(painter, rect)

        # no foreground for empty data
        if not self.parametric_uv:
            return

        # Draw patch centers
        self.draw_patch_centers_foreground(painter, rect)

        # Draw corner points
        self.draw_corner_points_foreground(painter, rect)

        # Draw patches
        if self.show_patches:
            self.draw_patches_foreground(painter, rect)

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

    def update_view(self):
        # Here you can add logic for redrawing background and grid
        self.scene().update()