"""Analytic fixture checks, not a game or renderer."""
import unittest
import numpy as np
from audit_lip import point_tri_sq,seg_seg_sq,clip_box,area
class GeometricChecks(unittest.TestCase):
    def test_point_over_plane_interior(self):
        t=np.array([[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]])
        p=np.array([.2,.3,.05])
        self.assertAlmostEqual(point_tri_sq(p,t)[0],.05**2,places=13)
    def test_two_segments_have_interior_closest_pair(self):
        a=np.array([-1.,0.,0.]);b=np.array([1.,0.,0.])
        c=np.array([[0.,-1.,.07]]);d=np.array([[0.,1.,.07]])
        self.assertAlmostEqual(seg_seg_sq(a,b,c,d)[0],.07**2,places=13)
    def test_clip_rectangle_area(self):
        p=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
        q=clip_box(p,[(0,.1,.4),(1,.3,.7)])
        self.assertAlmostEqual(area(q),.12,places=13)
