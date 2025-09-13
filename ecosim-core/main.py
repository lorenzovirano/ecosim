#!/usr/bin/env python3
"""
Test minimale per identificare il problema PyBullet
"""

import pybullet as p
import pybullet_data
import os
import sys

print("🧪 Test PyBullet minimale...")

# Configurazioni per macOS
configs = [
    ("Standard GUI", {}),
    ("OpenGL2", {"options": "--opengl2"}),
    ("No shadows", {"options": "--disable_shadows"}),
    ("Software render", {"options": "--software_render"}),
    ("Combined", {"options": "--opengl2 --disable_shadows --software_render"}),
]

# Variabili ambiente da testare
env_configs = [
    ("Default", {}),
    ("EGL disabled", {"PYBULLET_EGL": "0"}),
    ("Mesa override", {
        "MESA_GL_VERSION_OVERRIDE": "3.3",
        "MESA_GLSL_VERSION_OVERRIDE": "330"
    }),
    ("All fixes", {
        "PYBULLET_EGL": "0",
        "MESA_GL_VERSION_OVERRIDE": "3.3",
        "MESA_GLSL_VERSION_OVERRIDE": "330"
    })
]


def test_connection(config_name, connect_args, env_vars=None):
    """Test una configurazione specifica"""
    print(f"\n🔍 Test: {config_name}")

    # Imposta variabili ambiente se specificate
    old_env = {}
    if env_vars:
        for key, value in env_vars.items():
            old_env[key] = os.environ.get(key)
            os.environ[key] = value
            print(f"   ENV: {key}={value}")

    try:
        # Tentativo connessione
        client = p.connect(p.GUI, **connect_args)
        print(f"   ✅ Connessione riuscita!")

        # Test base - imposta search path e gravità
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.81)
        print(f"   ✅ Configurazione base OK")

        # Test camera (qui spesso crasha)
        try:
            p.resetDebugVisualizerCamera(
                cameraDistance=10,
                cameraYaw=0,
                cameraPitch=-45,
                cameraTargetPosition=[0, 0, 0]
            )
            print(f"   ✅ Camera OK")
        except Exception as e:
            print(f"   ❌ Camera fallita: {e}")
            raise

        # Test caricamento oggetto semplice
        try:
            cube = p.loadURDF("cube.urdf", basePosition=[0, 0, 1])
            print(f"   ✅ Caricamento URDF OK (ID: {cube})")
        except Exception as e:
            print(f"   ❌ Caricamento URDF fallito: {e}")
            raise

        # Test step simulazione
        try:
            for _ in range(10):
                p.stepSimulation()
            print(f"   ✅ Step simulazione OK")
        except Exception as e:
            print(f"   ❌ Step simulazione fallito: {e}")
            raise

        # Chiusura
        p.disconnect()
        print(f"   ✅ {config_name} - SUCCESSO COMPLETO!")
        return True

    except Exception as e:
        print(f"   ❌ {config_name} - FALLITO: {e}")
        try:
            p.disconnect()
        except:
            pass
        return False

    finally:
        # Ripristina variabili ambiente
        for key in old_env:
            if old_env[key] is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_env[key]


def main():
    """Esegue tutti i test"""
    print("🚀 Inizio test sistematico PyBullet")
    print(f"   Sistema: {sys.platform}")
    print(f"   Python: {sys.version}")

    successful_configs = []

    # Prima test configurazioni base
    for config_name, connect_args in configs:
        if test_connection(config_name, connect_args):
            successful_configs.append((config_name, connect_args, {}))
            break  # Se una funziona, non serve testare le altre

    # Se nessuna configurazione base funziona, testa con variabili ambiente
    if not successful_configs:
        print("\n🔄 Nessuna configurazione base funziona, testo con env vars...")

        for env_name, env_vars in env_configs:
            for config_name, connect_args in configs:
                test_name = f"{config_name} + {env_name}"
                if test_connection(test_name, connect_args, env_vars):
                    successful_configs.append((test_name, connect_args, env_vars))
                    break
            if successful_configs:
                break

    # Test modalità DIRECT come fallback
    if not successful_configs:
        print("\n🔄 Test modalità DIRECT come fallback...")
        if test_connection("DIRECT mode", {}, {}):
            # Per DIRECT mode, fai connessione reale
            try:
                client = p.connect(p.DIRECT)
                p.setAdditionalSearchPath(pybullet_data.getDataPath())
                p.setGravity(0, 0, -9.81)
                cube = p.loadURDF("cube.urdf", basePosition=[0, 0, 1])
                for _ in range(100):
                    p.stepSimulation()
                cube_pos, _ = p.getBasePositionAndOrientation(cube)
                print(f"   📦 Posizione finale cubo: {cube_pos}")
                p.disconnect()
                successful_configs.append(("DIRECT mode", {}, {}))
            except Exception as e:
                print(f"   ❌ DIRECT mode fallito: {e}")

    # Risultati finali
    print("\n" + "=" * 50)
    if successful_configs:
        print("🎉 CONFIGURAZIONI FUNZIONANTI:")
        for config_name, connect_args, env_vars in successful_configs:
            print(f"   ✅ {config_name}")
            if connect_args:
                print(f"      Args: {connect_args}")
            if env_vars:
                print(f"      Env: {env_vars}")

        print("\n💡 RACCOMANDAZIONE:")
        config_name, connect_args, env_vars = successful_configs[0]
        print(f"   Usa: {config_name}")

        if env_vars:
            print("   Aggiungi all'inizio del tuo script:")
            print("   import os")
            for key, value in env_vars.items():
                print(f'   os.environ["{key}"] = "{value}"')

        if connect_args:
            print(f"   Connessione: p.connect(p.GUI, **{connect_args})")
        else:
            print("   Connessione: p.connect(p.GUI)")

    else:
        print("😞 Nessuna configurazione funziona!")
        print("   Possibili cause:")
        print("   - Driver GPU incompatibili")
        print("   - PyBullet compilato male per macOS")
        print("   - Problema sistema")
        print("   ")
        print("   Soluzioni da provare:")
        print("   1. Reinstalla PyBullet: pip install --force-reinstall pybullet")
        print("   2. Usa conda: conda install pybullet")
        print("   3. Compila da sorgenti")

    print("=" * 50)


if __name__ == "__main__":
    main()