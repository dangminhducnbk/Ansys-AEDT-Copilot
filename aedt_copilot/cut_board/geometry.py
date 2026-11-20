"""Giữ đường dẫn cũ (re-export). Dùng aedt_copilot.core.geometry / core.geometry_edb cho code mới."""
import math  # noqa: F401  (giữ tên public cũ)

from ..core.geometry import _cross, bbox_of, edges, point_in_poly, point_seg_dist, poly_area, seg_seg_dist  # noqa: F401
from ..core.geometry_edb import prim_points  # noqa: F401
