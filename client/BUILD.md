# Construire l'exécutable autonome (hanif.exe)

Génère un exécutable Windows unique, à envoyer à quelqu'un qui n'a pas Python.
À lancer **sur Windows** (l'exe produit est spécifique à l'OS de build).

```bash
cd client
python -m venv .venv
.venv\Scripts\Activate.ps1          # PowerShell
pip install -r requirements.txt pyinstaller

python -m PyInstaller \
  --onefile --name hanif --noconfirm --clean \
  --collect-all textual \
  --collect-submodules hanif_cli \
  --paths . \
  --distpath dist --workpath build/pyi --specpath build \
  build_entry.py
```

Résultat : `client/dist/hanif.exe` (~17 Mo).

Vérifier :
```bash
dist\hanif.exe version      # -> Hanif Chat CLI 0.1.0
dist\hanif.exe selftest     # -> OK (l'interface démarre)
```

> Le CSS est intégré au code (`HACKER_CSS` dans `app.py`), donc aucun fichier
> externe n'est nécessaire dans l'exe.
>
> Pour un binaire Linux/macOS, relancer la même commande sur l'OS cible.

---

## Installeur Windows (Setup.exe)

Produit un `HanifChat-Setup.exe` que n'importe qui double-clique : il installe
`hanif.exe`, **l'ajoute au PATH** (la commande `hanif` marche alors dans tout
terminal) et crée les raccourcis menu Démarrer + bureau. Installation par
utilisateur, **sans droits administrateur**.

Prérequis : avoir d'abord construit `dist/hanif.exe` (ci-dessus) et installé
[Inno Setup 6](https://jrsoftware.org/isdl.php) (`winget install JRSoftware.InnoSetup`).

```bash
cd client
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer\hanif.iss
```

Résultat : `client/installer/Output/HanifChat-Setup.exe` (~18 Mo).

Installation / désinstallation silencieuses (pour tests) :
```bash
installer\Output\HanifChat-Setup.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
"%LOCALAPPDATA%\Programs\HanifChat\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES
```

Après installation, `hanif` est disponible dans **tout nouveau terminal**.
