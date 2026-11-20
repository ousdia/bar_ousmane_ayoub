# Bar à cocktails (asyncio)

Projet du cours de Big Data (Concurrence / Asynchronisme), Master 2 Data Science, Université d'Angers.
Enseignant : Jacquelin Charbonnel.

Auteurs : Mohamed Ayoub Zerrouki, Ousmane Dia.

On simule le bar « Borabora » : un serveur prend les commandes des clients, un bariste prépare les cocktails, puis on les sert. Le projet part d'une version séquentielle et la rend concurrente avec `asyncio`.

## Fichiers

| Fichier | Contenu |
|---|---|
| `partie1_etape1.py` | Classes de base (Pic, Bar, Serveur, Bariste), version séquentielle |
| `partie1_etape2.py` | Lecture des commandes clients depuis un fichier (`lundi`, `mardi`) |
| `partie1_etape3.py` | Journalisation dans `/tmp/borabora.log` avec la classe `Logable` |
| `partie2_etape1.py` | Passage en coroutines avec `asyncio.gather` |
| `partie2_etape2.py` | `asyncio.Queue` et sentinelle de fin |
| `partie2_etape3.py` | Tâches qui avancent vraiment en parallèle (`asyncio.sleep`) |
| `partie2_etape4.py` | Ajout d'un `asyncio.Lock` |
| `partie3.py` | Version finale : deux serveurs, terminaison propre |
| `lundi`, `mardi` | Fichiers de commandes (`délai cocktail1,cocktail2,...`) |
| `rapport.pdf` | Compte rendu : démarche suivie et difficulté principale |

## Lancer

Il faut Python 3.10 ou plus récent. Aucune bibliothèque externe.

```
python partie3.py mardi
```

Même chose pour les autres étapes (`python partie2_etape3.py lundi`, etc.). L'étape 1 de la partie 1 se lance sans argument : on tape les commandes au clavier (par exemple `mojito,margarita`), puis une ligne vide pour finir.

Sous Windows, le chemin `/tmp/borabora.log` correspond à `C:\tmp\borabora.log`. Le dossier `C:\tmp` doit exister avant de lancer :

```
mkdir C:\tmp
```

## Logs

Les logs ne sont pas dans le dépôt : chaque script les recrée quand on le lance.

- `partie1_etape1.py` et `partie1_etape2.py` affichent leur trace dans la console.
- À partir de `partie1_etape3.py`, la trace est écrite dans `/tmp/borabora.log` (sous Windows : `C:\tmp\borabora.log`). Le fichier est écrasé à chaque exécution.

Pour suivre le log en direct sous PowerShell :

```
Get-Content C:\tmp\borabora.log -Wait
```
