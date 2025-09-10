import pybullet as p
import pybullet_data
import time

print("Inizializzo PyBullet...")

# Connetti PyBullet
physicsClient = p.connect(p.GUI)
print("PyBullet GUI avviato!")

# IMPORTANTE: Aggiungi il percorso ai file URDF di esempio
p.setAdditionalSearchPath(pybullet_data.getDataPath())

p.setGravity(0, 0, -9.81)

# Carica piano (ora dovrebbe funzionare)
planeId = p.loadURDF("plane.urdf")
print("Piano caricato")

# Carica un oggetto
startPos = [0, 0, 1]
startOrientation = p.getQuaternionFromEuler([0, 0, 0])
boxId = p.loadURDF("r2d2.urdf", startPos, startOrientation)
print("R2D2 caricato!")

print("Avvio simulazione per 5 secondi...")

# Simula per 5 secondi
for i in range(1200):  # 5 secondi a 240 FPS
    p.stepSimulation()
    time.sleep(1./240.)
    
    if i % 240 == 0:  # Ogni secondo
        pos, orn = p.getBasePositionAndOrientation(boxId)
        print(f"Secondo {i//240}: posizione R2D2 = {pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}")

p.disconnect()
print("Test completato!")