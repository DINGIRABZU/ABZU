"""Ensure OpenCV can be imported and has a spec."""


def test_cv2_has_spec():
    import cv2

    assert cv2.__spec__ is not None
