"""Image preprocessing for OCR."""

import cv2
import numpy as np
from PIL import Image
import structlog

logger = structlog.get_logger()


class ImagePreprocessor:
    """Image preprocessing for improved OCR accuracy."""

    def __init__(self, enable_deskew: bool = True, enable_denoise: bool = True,
                 enable_binarize: bool = True):
        """Initialize preprocessor."""
        self.enable_deskew = enable_deskew
        self.enable_denoise = enable_denoise
        self.enable_binarize = enable_binarize

    def preprocess(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for OCR.

        Args:
            image: PIL Image

        Returns:
            Preprocessed PIL Image
        """
        # Convert PIL to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Deskew
        if self.enable_deskew:
            cv_image = self._deskew(cv_image)

        # Denoise
        if self.enable_denoise:
            cv_image = self._denoise(cv_image)

        # Binarize
        if self.enable_binarize:
            cv_image = self._binarize(cv_image)

        # Convert back to PIL
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        return Image.fromarray(cv_image)

    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """
        Deskew the image using Hough transform.

        Args:
            image: OpenCV image

        Returns:
            Deskewed image
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)

            if lines is None or len(lines) == 0:
                return image

            # Calculate angle
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle = np.degrees(theta) - 90
                if -45 <= angle <= 45:
                    angles.append(angle)

            if not angles:
                return image

            median_angle = np.median(angles)

            # Rotate image
            h, w = image.shape[:2]
            center = (w // 2, h // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(
                image, rotation_matrix, (w, h),
                borderMode=cv2.BORDER_REPLICATE
            )

            return rotated
        except Exception as e:
            logger.warning("deskew_failed", error=str(e))
            return image

    def _denoise(self, image: np.ndarray) -> np.ndarray:
        """
        Denoise the image.

        Args:
            image: OpenCV image

        Returns:
            Denoised image
        """
        try:
            # Apply bilateral filter for noise reduction
            denoised = cv2.bilateralFilter(image, 9, 75, 75)
            return denoised
        except Exception as e:
            logger.warning("denoise_failed", error=str(e))
            return image

    def _binarize(self, image: np.ndarray) -> np.ndarray:
        """
        Convert image to binary (black and white).

        Args:
            image: OpenCV image

        Returns:
            Binarized image
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply adaptive threshold for better results with varying lighting
            binary = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11, 2
            )

            return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        except Exception as e:
            logger.warning("binarize_failed", error=str(e))
            return image

    def upscale(self, image: Image.Image, target_dpi: int = 300) -> Image.Image:
        """
        Upscale low-resolution images.

        Args:
            image: PIL Image
            target_dpi: Target DPI

        Returns:
            Upscaled image
        """
        try:
            # Simple upscaling using PIL
            current_width, current_height = image.size

            # Estimate current DPI (assume 72 if not specified)
            current_dpi = 72

            # Calculate scale factor
            scale_factor = target_dpi / current_dpi

            if scale_factor > 1.0:
                new_size = (
                    int(current_width * scale_factor),
                    int(current_height * scale_factor),
                )
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            return image
        except Exception as e:
            logger.warning("upscale_failed", error=str(e))
            return image
