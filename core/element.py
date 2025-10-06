from dataclasses import dataclass
from typing import Tuple, List


@dataclass
class ElementRect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)

    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)


@dataclass
class Element:
    """通用元素对象，统一承载定位信息与中心点。"""
    rect: ElementRect
    center: Tuple[int, int]

    @staticmethod
    def from_pixel_bbox(bbox_px: List[int]) -> "Element":
        if not isinstance(bbox_px, list) or len(bbox_px) != 4:
            raise ValueError("bbox_px must be [xmin, ymin, xmax, ymax]")
        left, top, right, bottom = map(int, bbox_px)
        cx = int(round((left + right) / 2))
        cy = int(round((top + bottom) / 2))
        return Element(ElementRect(left, top, right, bottom), (cx, cy))

    @staticmethod
    def from_point(x: int, y: int) -> "Element":
        # 点元素（无矩形），用于坐标点击场景
        return Element(ElementRect(x, y, x, y), (int(x), int(y)))