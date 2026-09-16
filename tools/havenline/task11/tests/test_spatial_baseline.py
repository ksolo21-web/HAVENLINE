import json
import math
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASELINE_PATH = ROOT / "Docs/Production/T11/SPATIAL_BASELINE.json"
CATALOG_PATH = ROOT / "HavenlineGodot/assets/stations_v2/catalog.json"


def load(path: Path):
    return json.loads(path.read_text())


def blob_sha(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path.relative_to(ROOT))], cwd=ROOT, text=True).strip()


def point_segment_distance(p, a, b):
    px, pz = p
    ax, az = a
    bx, bz = b
    dx, dz = bx - ax, bz - az
    den = dx * dx + dz * dz
    if den <= 1e-12:
        return math.hypot(px - ax, pz - az)
    t = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / den))
    return math.hypot(px - (ax + t * dx), pz - (az + t * dz))


def orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def on_segment(a, b, p):
    return (
        min(a[0], b[0]) - 1e-9 <= p[0] <= max(a[0], b[0]) + 1e-9
        and min(a[1], b[1]) - 1e-9 <= p[1] <= max(a[1], b[1]) + 1e-9
        and abs(orient(a, b, p)) <= 1e-9
    )


def segments_intersect(a, b, c, d):
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if abs(o1) <= 1e-9 and on_segment(a, b, c):
        return True
    if abs(o2) <= 1e-9 and on_segment(a, b, d):
        return True
    if abs(o3) <= 1e-9 and on_segment(c, d, a):
        return True
    if abs(o4) <= 1e-9 and on_segment(c, d, b):
        return True
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def segment_segment_distance(a, b, c, d):
    if segments_intersect(a, b, c, d):
        return 0.0
    return min(
        point_segment_distance(a, c, d),
        point_segment_distance(b, c, d),
        point_segment_distance(c, a, b),
        point_segment_distance(d, a, b),
    )


def segment_rect_distance(a, b, center, footprint):
    x, z = center
    w, d = footprint
    corners = [
        (x - w / 2.0, z - d / 2.0),
        (x + w / 2.0, z - d / 2.0),
        (x + w / 2.0, z + d / 2.0),
        (x - w / 2.0, z + d / 2.0),
    ]
    edges = list(zip(corners, corners[1:] + corners[:1]))
    return min(segment_segment_distance(a, b, c, d_) for c, d_ in edges)


class RiverAuthority:
    def __init__(self, spec):
        self.anchors = [tuple(v) for v in spec["anchors"]]
        self.widths = list(spec["widths"])
        parts = spec["build_margin_components"]
        self.build_margin = sum(parts.values())

    def segment_index(self, x):
        if x <= self.anchors[0][0]:
            return 0
        for i in range(len(self.anchors) - 1):
            if x <= self.anchors[i + 1][0]:
                return i
        return len(self.anchors) - 2

    def slope(self, index):
        if index <= 0:
            a, b = self.anchors[0], self.anchors[1]
            return (b[1] - a[1]) / (b[0] - a[0])
        if index >= len(self.anchors) - 1:
            a, b = self.anchors[-2], self.anchors[-1]
            return (b[1] - a[1]) / (b[0] - a[0])
        a, b = self.anchors[index - 1], self.anchors[index + 1]
        return (b[1] - a[1]) / (b[0] - a[0])

    @staticmethod
    def hermite(y0, y1, m0, m1, h, t):
        t2, t3 = t * t, t * t * t
        return (
            (2 * t3 - 3 * t2 + 1) * y0
            + (t3 - 2 * t2 + t) * h * m0
            + (-2 * t3 + 3 * t2) * y1
            + (t3 - t2) * h * m1
        )

    @staticmethod
    def hermite_derivative(y0, y1, m0, m1, h, t):
        t2 = t * t
        return (
            (6 * t2 - 6 * t) * y0
            + (3 * t2 - 4 * t + 1) * h * m0
            + (-6 * t2 + 6 * t) * y1
            + (3 * t2 - 2 * t) * h * m1
        ) / h

    def center_at_x(self, x):
        x = max(self.anchors[0][0], min(self.anchors[-1][0], x))
        i = self.segment_index(x)
        a, b = self.anchors[i], self.anchors[i + 1]
        h = b[0] - a[0]
        t = max(0.0, min(1.0, (x - a[0]) / h))
        return (x, self.hermite(a[1], b[1], self.slope(i), self.slope(i + 1), h, t))

    def tangent_at_x(self, x):
        x = max(self.anchors[0][0], min(self.anchors[-1][0], x))
        i = self.segment_index(x)
        a, b = self.anchors[i], self.anchors[i + 1]
        h = b[0] - a[0]
        t = max(0.0, min(1.0, (x - a[0]) / h))
        dzdx = self.hermite_derivative(a[1], b[1], self.slope(i), self.slope(i + 1), h, t)
        length = math.hypot(1.0, dzdx)
        return (1.0 / length, dzdx / length)

    def width_at_x(self, x):
        x = max(self.anchors[0][0], min(self.anchors[-1][0], x))
        i = self.segment_index(x)
        a, b = self.anchors[i], self.anchors[i + 1]
        t = max(0.0, min(1.0, (x - a[0]) / (b[0] - a[0])))
        smooth = t * t * (3.0 - 2.0 * t)
        return self.widths[i] + (self.widths[i + 1] - self.widths[i]) * smooth

    def query(self, p):
        x = max(self.anchors[0][0], min(self.anchors[-1][0], p[0]))
        for _ in range(4):
            center = self.center_at_x(x)
            tangent = self.tangent_at_x(x)
            delta = (p[0] - center[0], p[1] - center[1])
            projection = delta[0] * tangent[0] + delta[1] * tangent[1]
            x = max(self.anchors[0][0], min(self.anchors[-1][0], x + projection * tangent[0]))
        center = self.center_at_x(x)
        tangent = self.tangent_at_x(x)
        north_normal = (-tangent[1], tangent[0])
        delta = (p[0] - center[0], p[1] - center[1])
        lateral = delta[0] * north_normal[0] + delta[1] * north_normal[1]
        half_width = self.width_at_x(x) * 0.5
        return {"shore_distance": abs(lateral) - half_width, "side": 1.0 if lateral >= 0.0 else -1.0}


class SpatialBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = load(BASELINE_PATH)
        cls.catalog = load(CATALOG_PATH)
        cls.entries = {row["id"]: row for row in cls.catalog["entries"]}

    def test_authority_blobs_are_exact(self):
        for authority in self.spec["authorities"].values():
            path = authority.get("path")
            expected = authority.get("git_blob_sha")
            if path and expected:
                self.assertEqual(blob_sha(ROOT / path), expected, path)

    def test_approved_t05_camp_arrangement_is_bound_exactly(self):
        actual = [
            {"asset_id": row["id"], "position_xz": [row["position"][0], row["position"][2]], "rotation_y": float(row["rotation_y"])}
            for row in self.catalog["arrangements"]["camp"]
        ]
        expected = [dict(row, rotation_y=float(row["rotation_y"])) for row in self.spec["approved_t05_camp_baseline"]]
        self.assertEqual(actual, expected)

    def test_construction_assets_are_approved_for_t11(self):
        for asset_id in ("pad_build", "hearth_vessel", "pad_upgrade"):
            self.assertIn(asset_id, self.entries)
            self.assertEqual(self.entries[asset_id]["later_task"], "T11")
        unbuilt = self.spec["construction_state_shells"]["site-unbuilt"]["spawn"][0]
        built = self.spec["construction_state_shells"]["camp-initial"]["construction_replacement"]
        self.assertEqual(unbuilt["position_xz"], built["position_xz"])
        self.assertEqual(unbuilt["asset_id"], "pad_build")
        self.assertEqual(built["add_asset_id"], "hearth_vessel")

    def test_no_shipping_prices_or_t10_recipe_ids_are_invented(self):
        for shell in self.spec["construction_state_shells"].values():
            self.assertIsNone(shell.get("shipping_price"))
            self.assertIsNone(shell.get("t10_recipe_id"))

    def test_fixed_boundary_and_river_build_setback(self):
        t03 = self.spec["authorities"]["t03_boundary"]["constants"]
        river = RiverAuthority(self.spec["authorities"]["t02_river"])
        for placement in self.spec["approved_t05_camp_baseline"]:
            entry = self.entries[placement["asset_id"]]
            x, z = placement["position_xz"]
            w, d = entry["footprint"]
            self.assertLessEqual(abs(x) + w / 2.0, t03["side_x"] + 1e-6, placement["asset_id"])
            self.assertLessEqual(z + d / 2.0, t03["north_z"] + 1e-6, placement["asset_id"])
            for corner in ((x - w / 2, z - d / 2), (x + w / 2, z - d / 2), (x - w / 2, z + d / 2), (x + w / 2, z + d / 2)):
                q = river.query(corner)
                self.assertGreaterEqual(q["side"], 0.0, f"{placement['asset_id']} crossed to south river side")
                self.assertGreaterEqual(q["shore_distance"], river.build_margin - 1e-3, f"{placement['asset_id']} violates T02 build setback")

    def test_hard_footprints_preserve_t03_lane_corridors(self):
        t03 = self.spec["authorities"]["t03_boundary"]
        lane_half = t03["constants"]["lane_half"]
        exemptions = {(row["asset_id"], lane) for row in self.spec["spatial_acceptance"]["lane_overlap_exemptions"] for lane in row["lanes"]}
        for placement in self.spec["approved_t05_camp_baseline"]:
            asset_id = placement["asset_id"]
            entry = self.entries[asset_id]
            for lane_id, points in t03["interior_lane_segments"].items():
                distance = min(segment_rect_distance(a, b, placement["position_xz"], entry["footprint"]) for a, b in zip(points, points[1:]))
                if distance < lane_half - 1e-6:
                    self.assertIn((asset_id, lane_id), exemptions, f"{asset_id} intrudes {lane_id} by {lane_half - distance:.3f}")
        # The walkable build pad intentionally uses the future hearth anchor.
        build = self.spec["construction_state_shells"]["site-unbuilt"]["spawn"][0]
        for lane_id in ("central-spine", "cross-camp"):
            self.assertIn((build["asset_id"], lane_id), exemptions)

    def test_t11_interaction_cluster_is_camera_safe(self):
        camera = self.spec["authorities"]["t04_camera"]["constants"]
        unbuilt = self.spec["construction_state_shells"]["site-unbuilt"]["spawn"][0]
        upgrade = self.spec["construction_state_shells"]["camp-initial"]["upgrade_pad"]
        a, b = unbuilt["position_xz"], upgrade["position_xz"]
        self.assertLessEqual(math.dist(a, b), camera["target_max_distance"] + 1e-6)
        rectangles = []
        for asset_id, pos in (("pad_build", a), ("pad_upgrade", b)):
            w, d = self.entries[asset_id]["footprint"]
            rectangles.append((pos[0] - w / 2, pos[1] - d / 2, pos[0] + w / 2, pos[1] + d / 2))
        xmin = min(r[0] for r in rectangles)
        zmin = min(r[1] for r in rectangles)
        xmax = max(r[2] for r in rectangles)
        zmax = max(r[3] for r in rectangles)
        self.assertLessEqual(xmax - xmin, camera["minimum_horizontal_span"] + 1e-6)
        self.assertLessEqual(zmax - zmin, camera["base_full_height"] + 1e-6)

    def test_later_task_behavior_boundaries_remain_explicit(self):
        policy = self.spec["construction_state_shells"]["camp-initial"]["passive_visual_context_policy"]
        self.assertIn("defense_platform", policy["reserved_not_spawned_by_t11"])
        self.assertIn("pad_payment", policy["allowed_without_later_behavior"])
        self.assertIn("processing_counter", policy["allowed_without_later_behavior"])
        self.assertEqual(self.entries["defense_platform"]["later_task"], "T22")
        self.assertEqual(self.entries["pad_payment"]["later_task"], "T17")
        self.assertEqual(self.entries["processing_counter"]["later_task"], "T16")


if __name__ == "__main__":
    unittest.main()
