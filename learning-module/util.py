import numpy as np


# Returns the inputted frame as a numpy array of floats
# add_dim is useful for 1D vectors (i.e. label columns)
def frame_to_nparray(frame, add_dim=False):
    if add_dim:
        return np.array([frame]).T.astype("float32")
    return np.array(frame).astype("float32")
