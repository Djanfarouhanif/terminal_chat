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
