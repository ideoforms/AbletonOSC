#!/usr/bin/env python3
"""
Script d'exploration pour découvrir les APIs de Device Variations dans Live 12.

Ce script doit être placé dans le dossier AbletonOSC et exécuté pendant que Live est ouvert
avec AbletonOSC chargé.

Instructions:
1. Ouvrez Ableton Live 12
2. Créez un Instrument Rack avec au moins 2 macro variations
3. Exécutez: ./explore_device_variations.py

Le script va interroger les propriétés et méthodes disponibles pour les devices/racks.
"""

from client.client import AbletonOSCClient
import time

def wait_tick():
    """Attend un tick Live pour que les changements prennent effet."""
    time.sleep(0.150)

def explore_device_apis():
    """Explore les APIs disponibles pour les devices et racks."""
    client = AbletonOSCClient()

    print("="*80)
    print("EXPLORATION DES APIS DE DEVICE VARIATIONS - LIVE 12")
    print("="*80)
    print()

    # Obtenir le nombre de tracks
    num_tracks = client.query("/live/song/get/num_tracks")
    print(f"📊 Nombre de tracks: {num_tracks[0]}")
    print()

    # Explorer le premier track (index 0)
    track_index = 2

    try:
        # Obtenir le nombre de devices sur le track
        num_devices_response = client.query(f"/live/track/get/num_devices", [track_index])
        if num_devices_response and len(num_devices_response) >= 2:
            num_devices = num_devices_response[1]
            print(f"🎛️  Track {track_index} - Nombre de devices: {num_devices}")
            print()

            if num_devices > 0:
                # Explorer le premier device
                device_index = 0

                print(f"🔍 Exploration du Device {device_index} sur Track {track_index}")
                print("-" * 80)

                # Propriétés de base
                name = client.query("/live/device/get/name", [track_index, device_index])
                class_name = client.query("/live/device/get/class_name", [track_index, device_index])
                device_type = client.query("/live/device/get/type", [track_index, device_index])

                print(f"  📝 Name: {name}")
                print(f"  📦 Class Name: {class_name}")
                print(f"  🏷️  Type: {device_type}")
                print()

                # Essayer d'accéder aux propriétés potentielles de variations
                print("🧪 Test des propriétés potentielles de variations:")
                print("-" * 80)

                potential_properties = [
                    # Propriétés potentielles basées sur les patterns Live API
                    "selected_variation",
                    "selected_macro_variation",
                    "variation_count",
                    "macro_variation_count",
                    "variations",
                    "macro_variations",
                    "can_have_variations",
                    "has_variations",
                    "selected_preset_variation",
                    "preset_variations",
                    # Propriétés liées aux chains (pour les racks)
                    "chains",
                    "can_have_chains",
                    "has_drum_pads",
                    "is_showing_chain_devices",
                    "view",
                ]

                for prop in potential_properties:
                    try:
                        # Note: Ceci va probablement échouer pour les propriétés non existantes
                        # mais c'est ce qu'on veut découvrir
                        result = client.query(f"/live/device/get/{prop}", [track_index, device_index])
                        print(f"  ✅ {prop}: {result}")
                    except Exception as e:
                        print(f"  ❌ {prop}: Non disponible ou erreur")

                print()
                print("💡 INSTRUCTIONS POUR PLUS D'EXPLORATION:")
                print("-" * 80)
                print("  1. Créez un Instrument Rack ou Effect Rack sur le track 1 (premier track)")
                print("  2. Configurez des macro variations dans le rack")
                print("  3. Relancez ce script")
                print()
                print("  Si le device testé est déjà un Rack avec variations,")
                print("  les propriétés marquées ✅ ci-dessus sont disponibles dans l'API.")
                print()
            else:
                print("⚠️  Aucun device trouvé sur le track 0.")
                print("   Ajoutez un Instrument Rack ou Effect Rack et relancez le script.")
                print()
        else:
            print("⚠️  Impossible de récupérer le nombre de devices.")
            print()

    except Exception as e:
        print(f"❌ Erreur lors de l'exploration: {e}")
        import traceback
        traceback.print_exc()

    finally:
        client.stop()

    print("="*80)
    print("FIN DE L'EXPLORATION")
    print("="*80)

if __name__ == "__main__":
    explore_device_apis()
