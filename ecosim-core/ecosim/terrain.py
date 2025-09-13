import numpy as np
import noise

def generate_heightmap(size = 64, scale = 10.0, seed = 42):
    safe_seed = abs(int(seed)) % (2 ** 32 - 1)
    np.random.seed(safe_seed)
    heightmap = np.zeros((size, size))

    for i in range(size):
        for j in range(size):
            #Perlin noise
            height = noise.pnoise2(
                i / scale,
                j / scale,
                octaves = 4,
                persistence = 0.5,
                lacunarity = 2.0,
                repeatx = 1024,
                repeaty = 1024,
                base = seed
            )
            heightmap[i, j] = height

    heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min())

    return heightmap