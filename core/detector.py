import os
import re
import xml.etree.ElementTree as ET
from typing import Tuple, List, Dict, Any, Optional


class WidgetDetector:
    """
    Lightweight widget detector (local implementation, replacing ScenGen).

    - Input: Screenshot path.
    - Output: Annotated screenshot path (original image), resize ratio (1.0), element list (with text and pixel boundaries).
    - Element fields compatible with TestEngine existing logic:
      column_min/x1, column_max/x2, row_min/y1, row_max/y2, text_content.
    - Constructs elements by reading the latest window_dump_*.xml (uiautomator dump) from temp/ directory.
    """

    def detect(self, screenshot_path: str) -> Tuple[str, float, List[Dict[str, Any]]]:
        screen_with_bbox_path = screenshot_path
        resize_ratio = 1.0
        elements: List[Dict[str, Any]] = []

        xml_path = self._find_latest_ui_dump()
        if xml_path and os.path.exists(xml_path):
            try:
                elements = self._parse_ui_dump(xml_path)
            except Exception:
                elements = []

        return screen_with_bbox_path, resize_ratio, elements

    def _find_latest_ui_dump(self) -> str:
        temp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "temp"))
        if not os.path.isdir(temp_dir):
            return ""
        cand = []
        for name in os.listdir(temp_dir):
            if name.startswith("window_dump_") and name.endswith(".xml"):
                full = os.path.join(temp_dir, name)
                try:
                    cand.append((os.path.getmtime(full), full))
                except Exception:
                    pass
        if not cand:
            return ""
        cand.sort(reverse=True)
        return cand[0][1]

    def _parse_ui_dump(self, xml_path: str) -> List[Dict[str, Any]]:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        elements: List[Dict[str, Any]] = []

        for node in root.iter():
            bounds = node.attrib.get("bounds")
            text = node.attrib.get("text", "")
            desc = node.attrib.get("content-desc", "")

            if not bounds:
                continue
            xy = self._parse_bounds(bounds)
            if not xy:
                continue

            x1, y1, x2, y2 = xy
            elements.append({
                "column_min": int(x1),
                "column_max": int(x2),
                "row_min": int(y1),
                "row_max": int(y2),
                "text_content": (text or desc or "").strip(),
            })

        return elements

    def _parse_bounds(self, bounds: str) -> Optional[Tuple[int, int, int, int]]:
        # Format like "[x1,y1][x2,y2]"
        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
        if not m:
            return None
        x1, y1, x2, y2 = map(int, m.groups())
        if x2 < x1 or y2 < y1:
            return None
        return x1, y1, x2, y2