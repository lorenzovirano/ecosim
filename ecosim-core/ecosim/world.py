from .chunk import Chunk

import numpy as np
import pybullet as p
import pybullet_data
import noise

class World:
    def __init__(self, chunk_size = 64, world_scale = 1.0):
        self.chunk_size = chunk_size
        self.world_scale = world_scale
        self.chunks = {}

    def add_chunk(self, x_index, y_index):
        chunk = Chunk(x_index, y_index, size = self.chunk_size)

        offset_x = x_index * self.chunk_size * self.world_scale
        offset_y = y_index * self.chunk_size * self.world_scale

        chunk.load_into_pybullet(offset_x, offset_y)

        self.chunks[(x_index, y_index)] = chunk

        return chunk

    def generate_grid(self, radius = 2):
        total_chunks = (2 * radius + 1) ** 2
        current = 0

        for i in range(-radius, radius + 1):
            for j in range(-radius, radius + 1):
                current += 1
                self.add_chunk(i, j)

def load_heightfield(heightmap, base_position, mesh_scale = 1.0):
    terrain_data = heightmap.flatten()

    terrain_shape = p.createCollisionShape(
        shapeType = p.GEOM_HEIGHTFIELD,
        meshScale = [mesh_scale, mesh_scale, 5],
        heightfieldTextureScaling = heightmap.shape[0] /2,
        heightfieldData = terrain_data.tolist(),
        numHeightfieldRows = heightmap.shape[0],
        numHeightfieldColumns = heightmap.shape[1],
    )

    terrain = p.createMultiBody(
        baseMass = 0,
        baseCollisionShapeIndex = terrain_shape,
        basePosition = base_position,
    )

    x, y, z = base_position
    color_r = 0.3 + abs(x) * 0.01  # Rosso varia con X
    color_g = 0.6 + abs(y) * 0.01  # Verde varia con Y
    color_b = 0.2
    p.changeVisualShape(terrain, -1, rgbaColor=[color_r, color_g, color_b, 1.0])

    return terrain
