from __future__ import annotations

from typing import Optional

import numpy as np


class Viewport:

    @property
    def fov(self) -> np.ndarray:
        return self._fov

    @fov.setter
    def fov(self, value: float | np.ndarray):
        if not isinstance(value, np.ndarray):
            # TODO: better handling of resolutions
            value = np.array([value, value * self.resolution[1] / self.resolution[0]])

        self._fov = value

        fov = value / 180 * np.pi

        x = 2 * self.focal_length * np.tan(fov / 2.0)

        self.camera_plane = np.array([
            x[0],
            x[1],
            self.focal_length,
        ])

    @property
    def focal_length(self) -> float:
        return self._focal_length

    @focal_length.setter
    def focal_length(self, value: float):
        self.camera_plane *= value / self.focal_length
        self._focal_length = value

    @property
    def orientation(self) -> np.ndarray:
        return self._orientation

    @orientation.setter
    def orientation(self, value: np.ndarray):
        self._orientation = value

        sin_x = np.sin(self.orientation[2])
        sin_y = np.sin(self.orientation[1])
        cos_x = np.cos(self.orientation[2])
        cos_y = np.cos(self.orientation[1])
        sin_z = np.sin(self.orientation[0])
        cos_z = np.cos(self.orientation[0])

        self._rot_yaw_matrix = np.array([cos_z, -sin_z, sin_z, cos_z]).reshape((2, 2))
        self._rot_pitch_matrix = np.array([cos_y, -sin_y, sin_y, cos_y]).reshape((2, 2))
        self._rot_roll_matrix = np.array([cos_x, -sin_x, sin_x, cos_x]).reshape((2, 2))

    def __init__(self,
                 resolution: np.ndarray,
                 fov: float = 90.0,
                 focal_length: float = 1e-5,
                 initial_position: np.ndarray = None,
                 initial_rotation: np.ndarray = None
                 ):
        self._rot_roll_matrix = None
        self._rot_yaw_matrix = None
        self._rot_pitch_matrix = None
        self.camera_plane = None
        self._fov = None
        self._focal_length = focal_length

        self.resolution = resolution

        self.fov = fov

        self.position = np.zeros(3, dtype=float) if initial_position is None else initial_position
        self.orientation = np.zeros(3, dtype=float) if initial_rotation is None else initial_rotation

    def _to_camera_space(self, point: np.ndarray) -> np.ndarray:

        transformed = point - self.position

        # TODO: rewrite camera space rotation
        transformed[:2] = np.matmul(
            self._rot_yaw_matrix,
            transformed[:2]
        )  # yaw
        transformed[::2] = np.matmul(
            self._rot_pitch_matrix,
            transformed[::2]
        )  # pitch
        transformed[1:] = np.matmul(
            self._rot_roll_matrix,
            transformed[1:]
        )  # roll

        return transformed

    def uv_to_pixel(self, point: Optional[np.ndarray]) -> Optional[np.ndarray]:
        if point is None:
            return None
        else:
            return point * self.resolution * np.array([1, -1]) + self.resolution / 2

    def _project_camera_space_point(self, point: np.ndarray) -> Optional[np.ndarray]:

        if point[2] < self.focal_length:
            return None

        # print(f"{self.focal_length=}, {self.camera_plane=}")
        return (point[:2] * self.focal_length) / (point[2]) / self.camera_plane[:2]

    def project_point(self, point: np.ndarray) -> Optional[np.ndarray]:

        camera_space_point = self._to_camera_space(point)

        if camera_space_point[2] < self.focal_length:
            return None

        return self.uv_to_pixel(self._project_camera_space_point(camera_space_point))

    def project_line(self, start_point, end_point) -> Optional[tuple[np.ndarray, np.ndarray]]:
        cs_start = self._to_camera_space(start_point)
        cs_end = self._to_camera_space(end_point)

        if cs_start[2] >= self.focal_length:

            if cs_end[2] >= self.focal_length:
                return self.uv_to_pixel(self._project_camera_space_point(cs_start)), self.uv_to_pixel(
                    self._project_camera_space_point(cs_end))

            else:
                return self._project_line_cut(cs_start, cs_end)

        else:
            if cs_end[2] >= self.focal_length:
                return self._project_line_cut(cs_end, cs_start)

            else:
                return self._project_line_cut(cs_end, cs_start)

    def _project_line_cut(self, onscreen: np.ndarray, offscreen: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        plane_normal = np.array([0, 0, 1])
        plane_point = np.array([0, 0, self.focal_length])

        dotp = np.dot(plane_normal, (offscreen - onscreen))
        if dotp == 0.0:
            return self.uv_to_pixel(self._project_camera_space_point(onscreen)), self.uv_to_pixel(
                self._project_camera_space_point(offscreen))

        # computes the intersection bewteen the line and the camera plane
        intersection = onscreen + (offscreen - onscreen) * (
                np.dot(plane_normal, plane_point) - np.dot(plane_normal, onscreen)) / dotp

        return self.uv_to_pixel(self._project_camera_space_point(onscreen)), self.uv_to_pixel(
            self._project_camera_space_point(intersection))
