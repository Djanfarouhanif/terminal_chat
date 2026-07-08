# Construire l'exécutable autonome (relay.exe)

Génère un exécutable Windows unique, à envoyer à quelqu'un qui n'a pas Python.
À lancer **sur Windows** (l'exe produit est spécifique à l'OS de build).

```bash
cd client
python -m venv .venv
.venv\Scripts\Activate.ps1          # PowerShell
pip install -r requirements.txt pyinstaller

python -m PyInstaller \
  --onefile --name relay --noconfirm --clean \
  --collect-all textual \
  --collect-submodules relay_cli \
  --paths . \
  --distpath dist --workpath build/pyi --specpath build \
  build_entry.py
```

Résultat : `client/dist/relay.exe` (~17 Mo).

Vérifier :
```bash
dist\relay.exe version      # -> Relay 0.1.0
dist\relay.exe selftest     # -> OK (l'interface démarre)
```

> Le CSS est intégré au code (`HACKER_CSS` dans `app.py`), donc aucun fichier
> externe n'est nécessaire dans l'exe.
>
> Pour un binaire Linux/macOS, relancer la même commande sur l'OS cible.

---

## Installeur Windows (Setup.exe)

Produit un `Relay-Setup.exe` que n'importe qui double-clique : il installe
`relay.exe`, **l'ajoute au PATH** (la commande `relay` marche alors dans tout
terminal) et crée les raccourcis menu Démarrer + bureau. Installation par
utilisateur, **sans droits administrateur**.

Prérequis : avoir d'abord construit `dist/relay.exe` (ci-dessus) et installé
[Inno Setup 6](https://jrsoftware.org/isdl.php) (`winget install JRSoftware.InnoSetup`).

```bash
cd client
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer\relay.iss
```

Résultat : `client/installer/Output/Relay-Setup.exe` (~18 Mo).

Installation / désinstallation silencieuses (pour tests) :
```bash
installer\Output\Relay-Setup.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
"%LOCALAPPDATA%\Programs\Relay\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES
```

Après installation, `relay` est disponible dans **tout nouveau terminal**.

---

## Publier une mise à jour du client (avis automatique)

Le client vérifie au démarrage l'endpoint `GET /api/client-version` et, si le
serveur annonce une version plus récente que la sienne, affiche un avis
« mise à jour disponible » avec le lien de téléchargement.

Pour publier une nouvelle version du client :

1. **Bumper la version** dans `relay_cli/__init__.py` (`__version__`) et
   `pyproject.toml` (`version`) — et `AppVersion` dans `installer/relay.iss`.
2. **Reconstruire** : `.\build.ps1`.
3. **Distribuer** le nouveau `Relay-Setup.exe` (ou publier une Release GitHub).
4. **Annoncer la version côté serveur** (sans rebuild du backend) :
   ```bash
   ssh root@srv1153432.hstgr.cloud
   cd ~/hanif-backend
   sed -i 's/^CLIENT_LATEST_VERSION=.*/CLIENT_LATEST_VERSION=0.2.0/' .env.prod
   # (option) mettre à jour CLIENT_DOWNLOAD_URL vers la Release
   docker compose -f docker-compose.app.yml --env-file .env.prod up -d web
   ```
   Dès lors, tous les clients encore en 0.1.0 verront l'avis au démarrage.
