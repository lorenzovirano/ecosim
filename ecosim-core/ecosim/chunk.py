from .terrain import generate_heightmap

class Chunk:
    def __init__(self, x_index, y_index, size = 64, scale = 10.0):
        self.xIndex = x_index
        self.yIndex = y_index
        self.size = size
        self.scale = scale

        safe_seed = abs(x_index * 1000 + y_index) % (2 ** 32 - 1)
        self.heightmap = generate_heightmap(size, scale, seed=safe_seed)

        self.terrain_id = None

    def load_into_pybullet(self, offset_x = 0, offset_y = 0, mesh_scale = 1.0):
        from .world import load_heightfield

        base_position = [offset_x, offset_y, 0]

        self.terrain_id = load_heightfield(self.heightmap, base_position = base_position, mesh_scale = mesh_scale)

        return self.terrain_id
