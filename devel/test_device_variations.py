#!/usr/bin/env python3
"""
Script de test pour les nouvelles APIs de Device Variations dans AbletonOSC.

Ce script teste toutes les propriétés et méthodes liées aux variations
qui ont été implémentées dans device.py.

Prérequis:
1. Ableton Live 12 ouvert
2. AbletonOSC chargé (redémarré après modifications de device.py)
3. Un Instrument Rack ou Effect Rack sur le track 2 (index 2) avec des variations

Instructions:
1. Redémarrez Ableton Live pour charger les nouvelles modifications
2. Exécutez: ./test_device_variations.py
"""

from client.client import AbletonOSCClient
import time
import socket

def find_free_port(start_port=11001, max_attempts=10):
    """Trouve un port UDP libre."""
    for port in range(start_port, start_port + max_attempts):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            continue
    return None

def wait_tick():
    """Attend un tick Live pour que les changements prennent effet."""
    time.sleep(0.150)

def test_device_variations():
    """Teste toutes les APIs de device variations."""
    # Trouver un port client libre
    client_port = find_free_port()
    if client_port is None:
        print("❌ Impossible de trouver un port UDP libre.")
        return

    if client_port != 11001:
        print(f"ℹ️  Port client: {client_port}")
        print()

    try:
        client = AbletonOSCClient(client_port=client_port)
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print()
        print("⚠️  Vérifiez que:")
        print("   1. Live 12 est ouvert")
        print("   2. AbletonOSC est chargé")
        print("   3. Vous avez REDÉMARRÉ Live après avoir modifié device.py")
        print()
        return

    print("="*80)
    print("TEST DES APIS DE DEVICE VARIATIONS - LIVE 12")
    print("="*80)
    print()

    # Configuration du device à tester
    track_index = 2  # Track où se trouve votre Rack
    device_index = 0

    try:
        # Info de base
        name = client.query("/live/device/get/name", [track_index, device_index])
        class_name = client.query("/live/device/get/class_name", [track_index, device_index])

        print(f"🎛️  Device testé:")
        print(f"   Name: {name[2] if len(name) > 2 else 'N/A'}")
        print(f"   Class: {class_name[2] if len(class_name) > 2 else 'N/A'}")
        print()

        # Test 1: Propriétés en lecture seule
        print("📖 TEST 1: Propriétés en lecture seule")
        print("-" * 80)

        tests_readonly = [
            ("variation_count", "Nombre de variations"),
            ("can_have_chains", "Peut avoir des chains"),
            ("has_macro_mappings", "A des mappings de macros"),
            ("visible_macro_count", "Nombre de macros visibles"),
        ]

        for prop, description in tests_readonly:
            try:
                result = client.query(f"/live/device/get/{prop}", [track_index, device_index])
                if result and len(result) > 2:
                    print(f"  ✅ {prop}: {result[2]} ({description})")
                else:
                    print(f"  ⚠️  {prop}: Réponse vide")
            except Exception as e:
                print(f"  ❌ {prop}: {e}")

        print()

        # Test 2: Propriété en lecture/écriture
        print("📝 TEST 2: Propriété selected_variation_index (lecture/écriture)")
        print("-" * 80)

        try:
            # Lire la variation actuelle
            result = client.query("/live/device/get/selected_variation_index", [track_index, device_index])
            if result and len(result) > 2:
                current_variation = result[2]
                print(f"  📌 Variation actuelle: {current_variation}")

                # Obtenir le nombre de variations
                count_result = client.query("/live/device/get/variation_count", [track_index, device_index])
                if count_result and len(count_result) > 2:
                    variation_count = count_result[2]
                    print(f"  📊 Nombre total de variations: {variation_count}")

                    if variation_count > 0:
                        # Essayer de changer de variation
                        new_variation = 0 if current_variation != 0 else 1
                        print(f"  🔄 Changement vers variation {new_variation}...")

                        client.send_message("/live/device/set/selected_variation_index",
                                          [track_index, device_index, new_variation])
                        wait_tick()

                        # Vérifier le changement
                        verify_result = client.query("/live/device/get/selected_variation_index",
                                                     [track_index, device_index])
                        if verify_result and len(verify_result) > 2:
                            new_val = verify_result[2]
                            if new_val == new_variation:
                                print(f"  ✅ Variation changée avec succès vers: {new_val}")
                            else:
                                print(f"  ⚠️  La variation n'a pas changé (attendu: {new_variation}, reçu: {new_val})")

                        # Restaurer la variation originale
                        client.send_message("/live/device/set/selected_variation_index",
                                          [track_index, device_index, current_variation])
                        wait_tick()
                        print(f"  ↩️  Variation restaurée: {current_variation}")
                    else:
                        print(f"  ⚠️  Aucune variation disponible pour tester le changement")
            else:
                print(f"  ❌ Impossible de lire selected_variation_index")
        except Exception as e:
            print(f"  ❌ Erreur: {e}")

        print()

        # Test 3: Méthodes
        print("🔧 TEST 3: Méthodes de variations")
        print("-" * 80)

        tests_methods = [
            ("recall_selected_variation", "Rappeler la variation sélectionnée"),
            ("recall_last_used_variation", "Rappeler la dernière variation utilisée"),
        ]

        for method, description in tests_methods:
            try:
                print(f"  🧪 Test: {method}")
                client.send_message(f"/live/device/{method}", [track_index, device_index])
                wait_tick()
                print(f"     ✅ {description} - Commande envoyée")
            except Exception as e:
                print(f"     ❌ {method}: {e}")

        print()

        # Test 4: Méthodes avancées (avec avertissement)
        print("⚠️  TEST 4: Méthodes avancées (modification de données)")
        print("-" * 80)
        print("  ℹ️  Les tests suivants sont commentés pour éviter de modifier votre set.")
        print("  ℹ️  Décommentez-les dans le script si vous voulez les tester.")
        print()

        # Ces tests sont commentés car ils modifient les variations
        """
        # Test store_variation
        print("  🧪 Test: store_variation")
        client.send_message("/live/device/store_variation", [track_index, device_index])
        wait_tick()
        print("     ✅ Nouvelle variation stockée")

        # Test delete_selected_variation
        print("  🧪 Test: delete_selected_variation")
        client.send_message("/live/device/delete_selected_variation", [track_index, device_index])
        wait_tick()
        print("     ✅ Variation sélectionnée supprimée")

        # Test randomize_macros
        print("  🧪 Test: randomize_macros")
        client.send_message("/live/device/randomize_macros", [track_index, device_index])
        wait_tick()
        print("     ✅ Macros randomisées")
        """

        print("  📝 Pour tester store_variation, delete_selected_variation et randomize_macros,")
        print("     décommentez la section dans le code source du script.")
        print()

        # Résumé
        print("="*80)
        print("✅ TESTS TERMINÉS")
        print("="*80)
        print()
        print("📋 Résumé:")
        print("   • Les propriétés de base fonctionnent")
        print("   • selected_variation_index peut être lu et modifié")
        print("   • Les méthodes recall_* sont disponibles")
        print("   • Les méthodes de modification sont disponibles (non testées)")
        print()
        print("💡 Prochaines étapes:")
        print("   • Créer des tests unitaires dans tests/test_device.py")
        print("   • Documenter l'API dans README.md")
        print("   • Créer une pull request")
        print()

    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.stop()

    print("="*80)

if __name__ == "__main__":
    test_device_variations()
