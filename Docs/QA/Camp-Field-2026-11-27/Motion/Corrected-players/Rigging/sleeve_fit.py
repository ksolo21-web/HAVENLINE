"""Extend sleeve segments in a measured T-pose while rigidly translating each mitten."""
import numpy as np


def arm_joint(name):
    return name.startswith(("UpperArm.", "Forearm.", "Hand.", "Thumb", "Index", "Middle", "Ring", "Little"))


def displacement(x, fit):
    if not fit:
        return np.zeros_like(x),np.zeros_like(x)
    start, end, delta = (fit[k] for k in ("shoulder_x", "wrist_x", "extension_each_m"))
    t=np.clip((np.abs(x)-start)/(end-start),0.,1.)
    distance=delta*t*t*(3.-2.*t)
    derivative=delta*6.*t*(1.-t)/(end-start)
    return np.sign(x)*distance,derivative
