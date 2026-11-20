#!/usr/bin/env python3
"""
Borabora - Partie 2, étape 4 : un verrou (asyncio.Lock) par employé.
Les 2 tâches d'Alice (prendre / servir) restent concurrentes, mais une activité
commencée est terminée avant qu'elle en commence une autre : plus de "zapping".
Usage : python3 partie2_etape4.py mardi ; puis cat /tmp/borabora.log
"""
import asyncio
import re
import sys
import time

FIN = None

# Durées (en secondes) des actions élémentaires. Ce sont ces attentes qui
# donnent à la boucle d'évènements l'occasion de faire avancer une autre tâche.
UNITE = 1.0          # 1 "unité de temps" du fichier de commandes
DUREE_PRISE = 0.2    # écrire un post-it
DUREE_PREPA = 0.3    # préparer 1 cocktail
DUREE_SERVICE = 0.5  # servir 1 cocktail


class Logable:
    def __init__(self, name, verbose):
        self.name = name
        self.verbose = verbose

    def log(self, msg):
        if self.verbose:
            print(f"[{self.name}] {msg}", file=logf, flush=True)


class Accessoire(asyncio.Queue, Logable):
    def __init__(self, name, verbose):
        asyncio.Queue.__init__(self)
        Logable.__init__(self, name, verbose)


class Pic(Accessoire):
    async def embrocher(self, postit):
        await self.put(postit)
        self.log(f"post-it '{postit}' embroché, {self.qsize()} post-it(s) à traiter")

    async def liberer(self):
        postit = await self.get()
        self.log(f"post-it '{postit}' libéré, {self.qsize()} post-it(s) à traiter")
        return postit


class Bar(Accessoire):
    async def recevoir(self, commande):
        await self.put(commande)
        self.log(f"'{commande}' posée, {self.qsize()} commande(s) à servir")

    async def evacuer(self):
        commande = await self.get()
        self.log(f"'{commande}' évacuée, {self.qsize()} commande(s) à servir")
        return commande


class Employé(Logable):
    def __init__(self, pic, bar, clients, name, verbose):
        Logable.__init__(self, name, verbose)
        self.pic = pic
        self.bar = bar
        self.clients = clients
        # Le verrou représente "l'employé est occupé". Une seule activité peut le détenir.
        self.occupe = asyncio.Lock()
        self.log("prêt pour le service")


class Serveur(Employé):

    async def prendre_commande(self):
        while True:
            self.log("prêt pour prendre une nouvelle commande...")
            # On attend le client SANS tenir le verrou : attendre n'est pas travailler.
            # Pendant ces 4 unités d'attente (mardi), Alice reste libre pour servir.
            commande = await self.clients.commande()
            if commande is None:
                await self.pic.embrocher(FIN)
                break
            async with self.occupe:                     # début de l'activité "prise de commande"
                self.log(f"j'ai la commande '{commande}'")
                self.log(f"j'écris sur le post-it '{commande}'")
                await asyncio.sleep(DUREE_PRISE)        # coopère, mais garde le verrou
                await self.pic.embrocher(commande)
            # sortie du "async with" : verrou relâché, l'autre tâche d'Alice peut le prendre

    async def servir(self):
        while True:
            commande = await self.bar.evacuer()         # attente du plateau, verrou libre
            if commande is FIN:
                break
            async with self.occupe:                     # tout le plateau est servi d'un bloc
                self.log(f"j'apporte la commande '{commande}'")
                for conso in commande:
                    self.log(f"je sers '{conso}'")
                    # Ici la boucle d'évènements peut réveiller prendre_commande(),
                    # mais celle-ci bloque sur "async with self.occupe" jusqu'à la fin du plateau.
                    await asyncio.sleep(DUREE_SERVICE)

    async def run(self):
        await asyncio.gather(self.prendre_commande(), self.servir())


class Bariste(Employé):

    async def preparer(self):
        while True:
            postit = await self.pic.liberer()
            if postit is FIN:
                await self.bar.recevoir(FIN)
                break
            self.log(f"je commence la fabrication de '{postit}'")
            for conso in postit:
                self.log(f"je prépare '{conso}'")
                await asyncio.sleep(DUREE_PREPA)        # point de coopération
            await self.bar.recevoir(postit)
            self.log(f"la commande {postit} est prête")

    async def run(self):
        await self.preparer()


def usage():
    print(f"usage: {sys.argv[0]} fichier")
    exit(1)


class Clients:
    def __init__(self, fname):
        commandes = []
        start = time.time()
        t = 0                                    # instant (en unités) depuis l'ouverture
        fmt = re.compile(r"(\d+)\s+(.*)")
        with open(fname, "r", encoding="utf-8") as f:
            for line in f:
                found = fmt.search(line)
                if found:
                    # CORRECTION : l'énoncé dit que chaque délai compte "après la commande
                    # précédente" => délais CUMULÉS. Le code fourni faisait start+when,
                    # donc dans "mardi" la 3e commande (délai 2) arrivait à t=4 au lieu de t=6.
                    t += int(found.group(1))
                    commandes.append((start + t * UNITE, found.group(2).split(",")))
        self.commandes = commandes[::-1]

    async def commande(self):
        if len(self.commandes) == 0:
            return None
        quand, quoi = self.commandes[-1]
        # Au lieu de boucler en consommant du CPU (attente active), on dort exactement
        # le temps restant : pendant ce temps, les autres tâches avancent.
        await asyncio.sleep(max(0.0, quand - time.time()))
        self.commandes.pop()
        return quoi


async def main():
    await asyncio.gather(bob.run(), alice.run())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()
    logfile = "/tmp/borabora.log"
    print(f"logging in {logfile}...")
    logf = open(logfile, "w", encoding="utf-8")
    print("\n---", file=logf, flush=True)

    les_clients = Clients(sys.argv[1])
    le_pic = Pic(name="le_pic", verbose=False)
    le_bar = Bar(name="le_bar", verbose=False)
    bob = Bariste(le_pic, le_bar, les_clients, name="bob", verbose=True)
    alice = Serveur(le_pic, le_bar, les_clients, name="alice", verbose=True)
    asyncio.run(main())
