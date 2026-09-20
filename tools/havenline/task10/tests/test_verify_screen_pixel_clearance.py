import copy
import importlib.util
import math
import unittest
from pathlib import Path

PATH=Path(__file__).parents[1]/"verify_screen_pixel_clearance.py"
spec=importlib.util.spec_from_file_location("screen_verifier",PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class ScreenFontUnitTests(unittest.TestCase):
    def core(self):
        basis={"basis_x":[1,0,0],"basis_y":[0,1,0],"basis_z":[0,0,1]}
        return {"camera_transform":dict(basis,origin=[0,0,10]),
                "label_transform":dict(basis,origin=[0,0,0]),
                "camera_near":0.05,"camera_far":4000,"camera_keep_aspect":1,
                "camera_fov":90,"label_realization":{"pixel_size":0.1}}

    def test_independent_focal_depth_and_axis_units(self):
        c=self.core()
        self.assertAlmostEqual(1,m.nominal_screen_unit_scale(c,[320,200]))
        c["camera_keep_aspect"]=0
        self.assertAlmostEqual(1.6,m.nominal_screen_unit_scale(c,[320,200]))
        c["label_realization"]["pixel_size"]=0.0625
        self.assertAlmostEqual(1,m.nominal_screen_unit_scale(c,[320,200]))
        c["camera_transform"]["origin"][2]=20
        c["label_realization"]["pixel_size"]=0.125
        self.assertAlmostEqual(1,m.nominal_screen_unit_scale(c,[320,200]))

    def test_physical_native_scale_does_not_change_logical_units(self):
        c=self.core()
        c["label_realization"]["pixel_size"]=10/(540/math.tan(math.pi/4))
        self.assertAlmostEqual(1,m.nominal_screen_unit_scale(c,[1920,1080]))
        # Passing physical rather than logical dimensions would incorrectly double it.
        self.assertAlmostEqual(2,m.nominal_screen_unit_scale(c,[3840,2160]))
        self.assertEqual(((1920,1080),(3840,2160),1.0),m.PROFILES["native4k_full"])
        self.assertEqual(36,len(m.profile_cases("native4k_full")))

    def test_invalid_projection_and_parent_basis_reject(self):
        for depth in [0,-1,0.01,4001]:
            c=self.core();c["camera_transform"]["origin"][2]=depth
            with self.assertRaisesRegex(ValueError,"frustum"):m.nominal_screen_unit_scale(c,[320,200])
        for axis in [[0,0,0],[2,0,0],[-1,0,0],[0,1,0]]:
            c=self.core();c["label_transform"]["basis_x"]=axis
            with self.assertRaisesRegex(ValueError,"uniform"):m.nominal_screen_unit_scale(c,[320,200])
        c=self.core();c["camera_keep_aspect"]=True
        with self.assertRaisesRegex(ValueError,"aspect"):m.nominal_screen_unit_scale(c,[320,200])
        c=self.core();c["camera_transform"]["basis_x"]=[2,0,0]
        with self.assertRaisesRegex(ValueError,"orthonormal"):m.nominal_screen_unit_scale(c,[320,200])

    def test_protected_range_and_version_contract_reject_mutants(self):
        for scale in [.85,1,1.35]:
            for fit in [.85,1,.84,1.01]:
                c=self.core();c["evidence_scale"]=scale
                c["lifecycle_descriptor"]={"label_layout_policy":"constrained_screen_pixels_v3","label_size_coordinate_space":"logical_viewport_pixels"}
                c["label_realization"]["pixel_size"]*=scale*fit
                if fit in [.85,1]:m.validate_screen_font_size(c,[320,200])
                else:
                    with self.assertRaisesRegex(ValueError,"protected fit range"):m.validate_screen_font_size(c,[320,200])
        c=self.core();c["evidence_scale"]=1;c["lifecycle_descriptor"]={}
        with self.assertRaisesRegex(ValueError,"versioned"):m.validate_screen_font_size(c,[320,200])

    def test_all_readability_endpoint_units_and_canary_family(self):
        for scale in [.85,1,1.35]:
            for fit in [.85,1]:
                c=self.core();c["label_realization"]["pixel_size"]*=scale*fit
                self.assertAlmostEqual(scale*fit,m.nominal_screen_unit_scale(c,[320,200]))
        profiles=["phone_16_9__0.85","phone_16_9__1.0","phone_16_9__1.35","native4k_full"]
        self.assertEqual(144,sum(len(m.profile_cases(p)) for p in profiles))

if __name__=="__main__":unittest.main()
