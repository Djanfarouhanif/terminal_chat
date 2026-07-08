# Installer le client Relay sur une autre machine

Le client est une application terminal en Python. La machine cible a besoin de :

- **Python 3.11 ou plus** (`python --version`)
- un **vrai terminal** (sur Windows : **Windows Terminal** ou PowerShell — évite `cmd.exe` pour les couleurs/Unicode)
- un accès Internet vers le serveur (par défaut `https://api-chat.hanifcode.fr`)

Aucune installation du backend n'est nécessaire côté client.

---

## Méthode 1 — pipx (recommandée, une seule commande)

`pipx` installe l'outil dans un environnement isolé et ajoute la commande
`relay` au PATH, disponible partout.

```bash
python -m pip install --user pipx
python -m pipx ensurepath          # rouvrir le terminal ensuite
pipx install "git+https://github.com/Djanfarouhanif/terminal_chat.git#subdirectory=client"
```

Lancer :
```bash
relay
```

Mettre à jour plus tard :
```bash
pipx upgrade relay-cli
```

---

## Méthode 2 — clone + environnement virtuel

```bash
git clone https://github.com/Djanfarouhanif/terminal_chat.git
cd terminal_chat/client

python -m venv .venv
# Windows PowerShell :
.venv\Scripts\Activate.ps1
# Linux / macOS :
source .venv/bin/activate

pip install .
relay
```

Variante sans installer le paquet (juste les dépendances) :
```bash
pip install -r requirements.txt
python -m relay_cli
```

---

## Premier lancement

1. Le client se connecte par défaut à **https://api-chat.hanifcode.fr**.
2. Au démarrage, la liste des commandes s'affiche. Créez un compte :
   ```
   /register monpseudo mon@email.fr monMotDePasse
   ```
   ou connectez-vous : `/login monpseudo monMotDePasse`
3. Rejoignez un salon puis discutez :
   ```
   /join general
   Salut tout le monde !
   ```

Les jetons de connexion sont mémorisés dans `~/.relay/config.json`
(auto-login aux lancements suivants).

---

## Pointer vers un autre serveur

Le serveur par défaut est la prod. Pour en viser un autre :

```bash
# de façon persistante (enregistré dans la config) :
relay chat --api https://mon-serveur.exemple.fr

# ponctuellement, via variable d'environnement :
#   Windows PowerShell :
$env:RELAY_API="http://127.0.0.1:8000"; relay
#   Linux / macOS :
RELAY_API=http://127.0.0.1:8000 relay
```

---

## Désinstaller

```bash
pipx uninstall relay-cli        # méthode 1
# ou supprimez simplement le dossier cloné + .venv   (méthode 2)
rm -rf ~/.relay                      # efface la config et les jetons
```
