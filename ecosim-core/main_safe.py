import pybullet as p
import pybullet_data
import time
import numpy as np
import noise


def generate_heightmap_safe(size=32, scale=10.0, seed=42):
    """Versione sicura e ottimizzata della generazione heightmap"""
    safe_seed = abs(int(seed)) % (2 ** 32 - 1)

    heightmap = np.zeros((size, size), dtype=np.float32)

    # Genera Perlin noise
    for i in range(size):
        for j in range(size):
            height = noise.pnoise2(
                i / scale,
                j / scale,
                octaves=3,  # Ridotto per performance
                persistence=0.5,
                lacunarity=2.0,
                repeatx=512,  # Ridotto
                repeaty=512,
                base=safe_seed
            )
            heightmap[i, j] = height

    # Normalizzazione sicura
    height_range = heightmap.max() - heightmap.min()
    if height_range < 1e-6:
        heightmap = np.random.uniform(0, 3, (size, size)).astype(np.float32)
    else:
        heightmap = (heightmap - heightmap.min()) / height_range * 3.0  # Max 3 unità

    return np.nan_to_num(heightmap, nan=0.0, posinf=3.0, neginf=0.0)


class DynamicWorld:
    def __init__(self, chunk_size=32, world_scale=1.0, max_chunks=3):
        self.chunk_size = chunk_size
        self.world_scale = world_scale
        self.max_chunks = max_chunks  # Limite di chunk simultanei
        self.chunks = {}
        self.chunk_order = []  # Per tracking ordine di caricamento

    def unload_chunk(self, x_index, y_index):
        """Scarica un chunk dalla memoria"""
        key = (x_index, y_index)
        if key in self.chunks:
            chunk = self.chunks[key]
            if chunk['terrain_id'] is not None:
                try:
                    p.removeBody(chunk['terrain_id'])
                    print(f"   🗑️  Chunk ({x_index},{y_index}) rimosso")
                except:
                    pass
            del self.chunks[key]
            if key in self.chunk_order:
                self.chunk_order.remove(key)

    def load_chunk(self, x_index, y_index):
        """Carica un singolo chunk con gestione memoria"""
        key = (x_index, y_index)

        # Se già caricato, non fare nulla
        if key in self.chunks:
            return self.chunks[key]['terrain_id']

        # Se abbiamo troppi chunk, rimuovi il più vecchio
        while len(self.chunks) >= self.max_chunks:
            oldest_key = self.chunk_order.pop(0)
            self.unload_chunk(oldest_key[0], oldest_key[1])

        print(f"📦 Caricando chunk ({x_index},{y_index})")

        try:
            # Genera heightmap
            safe_seed = abs(x_index * 1000 + y_index) % (2 ** 32 - 1)
            heightmap = generate_heightmap_safe(self.chunk_size, 10.0, safe_seed)

            # Posizione
            offset_x = x_index * self.chunk_size * self.world_scale
            offset_y = y_index * self.chunk_size * self.world_scale

            # Carica in PyBullet con parametri conservativi
            terrain_data = heightmap.flatten()

            terrain_shape = p.createCollisionShape(
                shapeType=p.GEOM_HEIGHTFIELD,
                meshScale=[0.8, 0.8, 0.8],  # Più piccolo
                heightfieldTextureScaling=self.chunk_size - 1,
                heightfieldData=terrain_data.tolist(),
                numHeightfieldRows=heightmap.shape[0],
                numHeightfieldColumns=heightmap.shape[1],
            )

            terrain_id = p.createMultiBody(
                baseMass=0,
                baseCollisionShapeIndex=terrain_shape,
                basePosition=[offset_x, offset_y, 0],
            )

            # Colore unico per chunk
            color_r = 0.3 + (abs(x_index) * 0.1) % 0.4
            color_g = 0.5 + (abs(y_index) * 0.1) % 0.4
            color_b = 0.3
            p.changeVisualShape(terrain_id, -1, rgbaColor=[color_r, color_g, color_b, 1.0])

            # Salva chunk
            self.chunks[key] = {
                'terrain_id': terrain_id,
                'heightmap': heightmap,
                'position': (offset_x, offset_y)
            }
            self.chunk_order.append(key)

            print(f"   ✅ Chunk caricato (ID: {terrain_id})")
            return terrain_id

        except Exception as e:
            print(f"   ❌ Errore caricamento chunk ({x_index},{y_index}): {e}")
            return None

    def update_around_position(self, x, y, radius=1):
        """Aggiorna chunk attorno a una posizione"""
        # Converti posizione mondo in indici chunk
        chunk_x = int(x // (self.chunk_size * self.world_scale))
        chunk_y = int(y // (self.chunk_size * self.world_scale))

        needed_chunks = []
        for i in range(-radius, radius + 1):
            for j in range(-radius, radius + 1):
                needed_chunks.append((chunk_x + i, chunk_y + j))

        # Rimuovi chunk troppo lontani
        to_remove = []
        for key in self.chunks:
            if key not in needed_chunks:
                to_remove.append(key)

        for key in to_remove:
            self.unload_chunk(key[0], key[1])

        # Carica chunk necessari
        for chunk_key in needed_chunks:
            self.load_chunk(chunk_key[0], chunk_key[1])


print("🚀 Avvio ECOSIM (versione dinamica)...")

# Setup PyBullet
physicsClient = p.connect(p.GUI)
print("✅ GUI PyBullet connessa")

p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.81)

p.resetDebugVisualizerCamera(
    cameraDistance=60,
    cameraYaw=45,
    cameraPitch=-45,
    cameraTargetPosition=[0, 0, 0]
)

# Mondo dinamico
world = DynamicWorld(chunk_size=32, world_scale=1.0, max_chunks=4)  # Max 4 chunk

print("\n🌍 Caricamento iniziale...")
world.load_chunk(0, 0)  # Centro
world.load_chunk(0, 1)  # Nord
world.load_chunk(1, 0)  # Est

print("\n📦 Aggiungendo oggetti...")

# Cubo controllabile
cubeId = p.loadURDF("cube.urdf", basePosition=[0, 0, 15])

# Sfere di test
spheres = []
positions = [[10, 10, 15], [20, 20, 15], [-10, -10, 15]]
colors = [[1, 0, 0, 1], [0, 1, 0, 1], [0, 0, 1, 1]]

for i, (pos, color) in enumerate(zip(positions, colors)):
    sphere_shape = p.createCollisionShape(p.GEOM_SPHERE, radius=0.8)
    sphere = p.createMultiBody(1.0, sphere_shape, basePosition=pos)
    p.changeVisualShape(sphere, -1, rgbaColor=color)
    spheres.append(sphere)

print(f"   {len(spheres)} oggetti creati")

# Simulazione con chunk loading dinamico
physics_timestamp = 1 / 240
p.setTimeStep(physics_timestamp)
start_time = time.time()
frame_count = 0

print(f"\n▶️  Simulazione dinamica avviata!")
print("   🔄 I chunk si caricheranno/scaricheranno automaticamente")
print("   ⏹️  Ctrl+C per fermare")

try:
    last_update = 0

    while True:
        p.stepSimulation()
        frame_count += 1

        # Aggiorna chunk ogni 2 secondi
        if frame_count - last_update > 480:  # 2 secondi a 240 FPS
            last_update = frame_count

            # Posizione cubo per chunk loading
            try:
                cube_pos, _ = p.getBasePositionAndOrientation(cubeId)
                world.update_around_position(cube_pos[0], cube_pos[1], radius=1)

                elapsed = time.time() - start_time
                print(f"⏱️  {elapsed:.1f}s - Cubo: ({cube_pos[0]:.1f}, {cube_pos[1]:.1f}, {cube_pos[2]:.1f})")
                print(f"   📊 Chunk attivi: {len(world.chunks)}")

            except Exception as e:
                print(f"   ⚠️  Errore aggiornamento: {e}")

        time.sleep(physics_timestamp)

except KeyboardInterrupt:
    print(f"\n🛑 Fermato dopo {time.time() - start_time:.1f}s")

finally:
    print("🧹 Pulendo...")
    # Rimuovi tutti i chunk
    for key in list(world.chunks.keys()):
        world.unload_chunk(key[0], key[1])

    try:
        p.disconnect()
        print("✅ Chiuso!")
    except:
        pass