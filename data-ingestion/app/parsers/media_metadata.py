"""Extract media metadata from web pages."""

import structlog
from typing import Dict, List, Optional
import re

from bs4 import BeautifulSoup

logger = structlog.get_logger()


class MediaMetadataExtractor:
    """Extractor for media metadata (images, videos, captions)."""

    async def extract(self, soup: BeautifulSoup) -> Dict:
        """Extract media metadata from HTML page.

        Args:
            soup: BeautifulSoup object

        Returns:
            Dictionary with media metadata
        """
        metadata = {
            "image_metadata": await self._extract_image_metadata(soup),
            "video_metadata": await self._extract_video_metadata(soup),
            "gallery_metadata": await self._extract_gallery_metadata(soup),
        }

        return metadata

    async def _extract_image_metadata(
        self, soup: BeautifulSoup
    ) -> List[Dict]:
        """Extract detailed image metadata.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of image metadata dictionaries
        """
        images = []

        try:
            for img in soup.find_all("img", limit=100):
                img_meta = {
                    "src": img.get("src", ""),
                    "alt": img.get("alt", ""),
                    "title": img.get("title", ""),
                    "width": img.get("width"),
                    "height": img.get("height"),
                    "data_src": img.get("data-src", ""),  # Lazy loading
                    "data_lazy_src": img.get("data-lazy-src", ""),
                    "loading": img.get("loading"),
                }

                # Extract figure caption if present
                parent = img.parent
                if parent and parent.name == "figure":
                    figcaption = parent.find("figcaption")
                    if figcaption:
                        img_meta["caption"] = figcaption.get_text().strip()

                # Get parent link if exists
                link_parent = img.find_parent("a")
                if link_parent:
                    img_meta["link"] = link_parent.get("href", "")

                images.append(img_meta)

        except Exception as e:
            logger.warning("image_metadata_extraction_error", error=str(e))

        return images

    async def _extract_video_metadata(
        self, soup: BeautifulSoup
    ) -> List[Dict]:
        """Extract detailed video metadata.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of video metadata dictionaries
        """
        videos = []

        try:
            # Extract from <video> tags
            for video in soup.find_all("video", limit=50):
                video_meta = {
                    "type": "html5_video",
                    "poster": video.get("poster", ""),
                    "title": video.get("title", ""),
                    "duration": video.get("duration"),
                    "width": video.get("width"),
                    "height": video.get("height"),
                    "controls": video.get("controls") is not None,
                    "autoplay": video.get("autoplay") is not None,
                    "loop": video.get("loop") is not None,
                    "sources": [],
                }

                # Extract source elements
                for source in video.find_all("source"):
                    video_meta["sources"].append(
                        {
                            "src": source.get("src", ""),
                            "type": source.get("type", ""),
                        }
                    )

                # Extract track elements (subtitles, etc)
                tracks = []
                for track in video.find_all("track"):
                    tracks.append(
                        {
                            "src": track.get("src", ""),
                            "kind": track.get("kind", ""),
                            "srclang": track.get("srclang", ""),
                            "label": track.get("label", ""),
                        }
                    )
                if tracks:
                    video_meta["tracks"] = tracks

                videos.append(video_meta)

            # Extract from <iframe> tags (YouTube, Vimeo, etc)
            for iframe in soup.find_all("iframe", limit=50):
                iframe_src = iframe.get("src", "")

                if any(
                    domain in iframe_src
                    for domain in ["youtube", "youtu.be", "vimeo", "dailymotion"]
                ):
                    video_meta = {
                        "type": "embedded_video",
                        "provider": self._detect_provider(iframe_src),
                        "src": iframe_src,
                        "title": iframe.get("title", ""),
                        "width": iframe.get("width"),
                        "height": iframe.get("height"),
                        "allow": iframe.get("allow", ""),
                    }

                    videos.append(video_meta)

        except Exception as e:
            logger.warning("video_metadata_extraction_error", error=str(e))

        return videos

    async def _extract_gallery_metadata(
        self, soup: BeautifulSoup
    ) -> List[Dict]:
        """Extract gallery/carousel metadata.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of gallery metadata dictionaries
        """
        galleries = []

        try:
            # Look for common gallery patterns
            gallery_classes = [
                "gallery",
                "carousel",
                "slider",
                "lightbox",
                "photos",
                "album",
            ]

            for gallery_class in gallery_classes:
                gallery_containers = soup.find_all(
                    class_=re.compile(gallery_class, re.I), limit=10
                )

                for container in gallery_containers:
                    images = []

                    for img in container.find_all("img", limit=50):
                        images.append(
                            {
                                "src": img.get("src", ""),
                                "alt": img.get("alt", ""),
                                "title": img.get("title", ""),
                            }
                        )

                    if images:
                        gallery_meta = {
                            "type": gallery_class,
                            "image_count": len(images),
                            "images": images,
                            "title": container.get("data-title", "")
                            or container.find(["h1", "h2", "h3"]),
                        }

                        galleries.append(gallery_meta)

        except Exception as e:
            logger.warning("gallery_metadata_extraction_error", error=str(e))

        return galleries

    @staticmethod
    def _detect_provider(iframe_src: str) -> str:
        """Detect video provider from iframe src.

        Args:
            iframe_src: Iframe src attribute

        Returns:
            Provider name
        """
        if "youtube" in iframe_src or "youtu.be" in iframe_src:
            return "youtube"
        elif "vimeo" in iframe_src:
            return "vimeo"
        elif "dailymotion" in iframe_src:
            return "dailymotion"
        elif "bilibili" in iframe_src:
            return "bilibili"
        else:
            return "unknown"
