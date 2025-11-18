#!/usr/bin/env python3
"""
Script d'introspection pour découvrir TOUTES les propriétés et méthodes
disponibles sur un Device dans Live 12.

Ce script interroge le nouveau handler /live/device/introspect qui a été
ajouté à AbletonOSC pour lister tous les attributs disponibles.

Instructions:
1. Rechargez AbletonOSC dans Live (ou redémarrez Live)
2. Assurez-vous d'avoir un Rack sur le premier track
3. Exécutez: ./introspect_device.py
"""

from client.client import AbletonOSCClient
import time
import socket

def find_free_port(start_port=11001, max_attempts=10):
    """Trouve un port UDP libre en commençant par start_port."""
    for port in range(start_port, start_port + max_attempts):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            continue
    return None

def introspect_device():
    """Introspectionne un device pour découvrir ses propriétés et méthodes."""
    # Trouver un port client libre
    client_port = find_free_port()
    if client_port is None:
        print("❌ Impossible de trouver un port UDP libre.")
        return

    if client_port != 11001:
        print(f"ℹ️  Utilisation du port client {client_port} (11001 était occupé)")
        print()

    try:
        client = AbletonOSCClient(client_port=client_port)
    except Exception as e:
        print(f"❌ Erreur lors de la connexion: {e}")
        print()
        print("⚠️  Vérifiez que:")
        print("   1. Ableton Live 12 est ouvert")
        print("   2. AbletonOSC est chargé comme Remote Script")
        print("   3. Vous avez REDÉMARRÉ Live après avoir modifié device.py")
        print()
        return

    print("="*80)
    print("INTROSPECTION COMPLÈTE D'UN DEVICE - LIVE 12")
    print("="*80)
    print()

    # Demander à l'utilisateur quel track/device introspectionner
    print("ℹ️  Configuration:")
    print()

    # Obtenir le nombre de tracks
    try:
        num_tracks = client.query("/live/song/get/num_tracks")
        print(f"📊 Nombre de tracks dans le set: {num_tracks[0]}")
        print()

        # Par défaut, on introspectionne le premier device du track 0
        # Mais on peut le modifier selon le device trouvé
        track_index = 2  # Le track où vous avez votre Rack
        device_index = 0

        # Obtenir des infos basiques sur le device
        print(f"🔍 Introspection du Device {device_index} sur Track {track_index}")
        print("-" * 80)

        name = client.query("/live/device/get/name", [track_index, device_index])
        class_name = client.query("/live/device/get/class_name", [track_index, device_index])
        device_type = client.query("/live/device/get/type", [track_index, device_index])

        print(f"  📝 Name: {name[2] if len(name) > 2 else 'N/A'}")
        print(f"  📦 Class Name: {class_name[2] if len(class_name) > 2 else 'N/A'}")
        print(f"  🏷️  Type: {device_type[2] if len(device_type) > 2 else 'N/A'}")
        print()

        # Maintenant, utilisons le nouveau handler d'introspection
        print("🧪 INTROSPECTION COMPLÈTE (toutes propriétés et méthodes):")
        print("-" * 80)
        print()

        result = client.query("/live/device/introspect", [track_index, device_index])

        # Le résultat contient: (track_id, device_id, "PROPERTIES:", props..., "METHODS:", methods...)
        if result and len(result) > 2:
            # Analyser le résultat
            current_section = None
            properties = []
            methods = []

            for item in result[2:]:  # Skip track_id and device_id
                if item == "PROPERTIES:":
                    current_section = "properties"
                elif item == "METHODS:":
                    current_section = "methods"
                elif current_section == "properties":
                    properties.append(item)
                elif current_section == "methods":
                    methods.append(item)

            # Afficher les propriétés
            print("📋 PROPRIÉTÉS DISPONIBLES:")
            print("-" * 80)
            if properties:
                # Filtrer et afficher les propriétés intéressantes en premier
                interesting_keywords = ['variation', 'macro', 'chain', 'preset', 'rack']
                interesting_props = [p for p in properties if any(k in p.lower() for k in interesting_keywords)]
                other_props = [p for p in properties if p not in interesting_props]

                if interesting_props:
                    print("\n🎯 PROPRIÉTÉS POTENTIELLEMENT LIÉES AUX VARIATIONS:")
                    for prop in sorted(interesting_props):
                        print(f"  ✨ {prop}")

                print(f"\n📝 TOUTES LES PROPRIÉTÉS ({len(properties)} au total):")
                for prop in sorted(properties):
                    print(f"  • {prop}")
            else:
                print("  (Aucune propriété trouvée)")

            print()
            print("🔧 MÉTHODES DISPONIBLES:")
            print("-" * 80)
            if methods:
                # Filtrer les méthodes intéressantes
                interesting_methods = [m for m in methods if any(k in m.lower() for k in interesting_keywords)]
                other_methods = [m for m in methods if m not in interesting_methods]

                if interesting_methods:
                    print("\n🎯 MÉTHODES POTENTIELLEMENT LIÉES AUX VARIATIONS:")
                    for method in sorted(interesting_methods):
                        print(f"  ✨ {method}()")

                print(f"\n📝 TOUTES LES MÉTHODES ({len(methods)} au total):")
                for method in sorted(methods):
                    print(f"  • {method}()")
            else:
                print("  (Aucune méthode trouvée)")

            print()
            print("="*80)
            print("💡 PROCHAINES ÉTAPES:")
            print("-" * 80)
            print("  1. Regardez les propriétés/méthodes marquées ✨")
            print("  2. Testez-les dans explore_device_variations.py")
            print("  3. Implémentez celles qui fonctionnent dans device.py")
            print()

        else:
            print("❌ L'introspection n'a rien retourné.")
            print("   Avez-vous bien redémarré Live après avoir modifié device.py?")
            print()

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.stop()

    print("="*80)
    print("FIN DE L'INTROSPECTION")
    print("="*80)

if __name__ == "__main__":
    introspect_device()
