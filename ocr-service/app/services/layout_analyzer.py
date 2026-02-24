"""Layout analysis for text region detection and table recognition."""

from typing import Optional
import cv2
import numpy as np
from PIL import Image
import structlog

logger = structlog.get_logger()


class LayoutAnalyzer:
    """Analyze document layout to detect regions, tables, and headers."""

    def __init__(self):
        """Initialize layout analyzer."""
        pass

    def detect_regions(self, image: Image.Image) -> list[dict]:
        """
        Detect text regions in image.

        Args:
            image: PIL Image

        Returns:
            List of region dicts with bounding boxes and types
        """
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

            # Detect text regions using morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            dilated = cv2.dilate(gray, kernel, iterations=2)

            # Find contours
            contours, _ = cv2.findContours(
                dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
            )

            regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # Filter small regions
                if w < 10 or h < 10:
                    continue

                # Estimate region type based on aspect ratio
                aspect_ratio = w / h if h > 0 else 0
                if aspect_ratio > 3:
                    region_type = "heading"
                elif aspect_ratio > 1.5:
                    region_type = "paragraph"
                else:
                    region_type = "paragraph"

                regions.append(
                    {
                        "bounding_box": [x, y, x + w, y + h],
                        "type": region_type,
                        "width": w,
                        "height": h,
                    }
                )

            return regions

        except Exception as e:
            logger.warning("layout_analysis_failed", error=str(e))
            return []

    def detect_tables(self, image: Image.Image) -> list[dict]:
        """
        Detect table regions in image.

        Args:
            image: PIL Image

        Returns:
            List of table bounding boxes
        """
        try:
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

            # Detect lines using Hough transform
            edges = cv2.Canny(gray, 50, 150)

            # Detect horizontal lines
            h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            h_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, h_kernel, iterations=1)

            # Detect vertical lines
            v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            v_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, v_kernel, iterations=1)

            # Combine
            grid = cv2.add(h_lines, v_lines)

            # Find contours of table regions
            contours, _ = cv2.findContours(
                grid, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
            )

            tables = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # Filter by size (tables should be reasonably large)
                if w < 50 or h < 50:
                    continue

                tables.append(
                    {
                        "bounding_box": [x, y, x + w, y + h],
                        "width": w,
                        "height": h,
                    }
                )

            return tables

        except Exception as e:
            logger.warning("table_detection_failed", error=str(e))
            return []

    def detect_headers(self, image: Image.Image) -> list[dict]:
        """
        Detect header regions (typically top of page with larger text).

        Args:
            image: PIL Image

        Returns:
            List of header bounding boxes
        """
        try:
            width, height = image.size

            # Headers are typically in the top 20% of the page
            header_height = int(height * 0.2)

            # Subdivide header region
            headers = [
                {
                    "bounding_box": [0, 0, width, header_height],
                    "type": "page_header",
                }
            ]

            return headers

        except Exception as e:
            logger.warning("header_detection_failed", error=str(e))
            return []

    def detect_columns(self, image: Image.Image, min_column_width: int = 50) -> list[dict]:
        """
        Detect column layout in document.

        Args:
            image: PIL Image
            min_column_width: Minimum width for a column

        Returns:
            List of column regions
        """
        try:
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

            # Detect vertical lines using Sobel
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=5)

            # Threshold
            _, binary = cv2.threshold(sobelx, 50, 255, cv2.THRESH_BINARY)

            # Dilate to connect nearby lines
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20))
            dilated = cv2.dilate(binary.astype(np.uint8), kernel, iterations=1)

            # Project onto x-axis
            x_projection = np.sum(dilated, axis=0)

            # Find peaks (columns)
            height, width = image.size[1], image.size[0]
            columns = []

            threshold = np.mean(x_projection) + np.std(x_projection)
            in_column = False
            col_start = 0

            for x in range(len(x_projection)):
                if x_projection[x] > threshold:
                    if not in_column:
                        col_start = x
                        in_column = True
                else:
                    if in_column:
                        col_width = x - col_start
                        if col_width >= min_column_width:
                            columns.append(
                                {
                                    "bounding_box": [col_start, 0, x, height],
                                    "type": "column",
                                    "width": col_width,
                                }
                            )
                        in_column = False

            return columns if columns else [{"bounding_box": [0, 0, width, height]}]

        except Exception as e:
            logger.warning("column_detection_failed", error=str(e))
            return []
