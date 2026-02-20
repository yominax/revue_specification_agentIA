"""
Script d'installation et de configuration du projet
"""
from pathlib import Path
import sys

def check_python_version():
    """Vérifie la version de Python"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 ou supérieur est requis")
        print(f"Version actuelle: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} détecté")
    return True

def create_directories():
    """Crée les répertoires nécessaires"""
    dirs = [
        Path("documents"),
        Path("vector_store"),
        Path("reports"),
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(exist_ok=True)
        print(f"✅ Dossier créé/vérifié: {dir_path}")

def check_env_file():
    """Vérifie la présence du fichier .env"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️  Fichier .env non trouvé")
            print(f"   Copiez {env_example} vers .env et configurez votre clé API")
        else:
            print("⚠️  Fichier .env non trouvé")
    else:
        print("✅ Fichier .env trouvé")

def main():
    """Fonction principale"""
    print("=" * 60)
    print("Configuration de l'Assistant GenAI")
    print("=" * 60)
    print()
    
    # Vérifier Python
    if not check_python_version():
        sys.exit(1)
    
    print()
    
    # Créer les répertoires
    print("Création des répertoires...")
    create_directories()
    
    print()
    
    # Vérifier .env
    print("Vérification de la configuration...")
    check_env_file()
    
    print()
    print("=" * 60)
    print("✅ Configuration terminée!")
    print()
    print("Prochaines étapes:")
    print("1. Configurez votre fichier .env avec votre clé API OpenAI")
    print("2. Placez vos documents dans le dossier 'documents/'")
    print("3. Lancez: python cli.py init")
    print("4. Lancez: python cli.py review")
    print("=" * 60)

if __name__ == "__main__":
    main()
