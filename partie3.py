#!/usr/bin/env python3
"""
Borabora - Partie 3 : extensions
  1. un second serveur ;
  2. un rythme de travail propre à chaque employé ;
  3. le bariste sert lui-même ce qu'il vient de préparer quand le pic est vide.
Usage : python3 partie3.py mardi ; puis cat /tmp/borabora.log
"""
import asyncio
import re
import sys
import time

UNITE = 1.0                      # 1 unité de temps du fichier de commandes, en secondes
T0 = time.time()                 # pour horodater les logs (lisibilité de la concurrence)


class Logable:
    def __init__(self, name, verbose):
        self.name = name
        self.verbose = verbose

    def log(self, msg):
        if self.verbose:
            print(f"{time.time() - T0:5.1f}s [{self.name}] {msg}", file=logf, flush=True)


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
    def __init__(self, pic, bar, clients, name, verbose, rythme=0.5):
        Logable.__init__(self, name, verbose)
        self.pic = pic
        self.bar = bar
        self.clients = clients
        # EXTENSION 2 : durée (s) d'une action élémentaire pour CET employé.
        # Plus rythme est petit, plus l'employé est rapide.
        self.rythme = rythme
        self.occupe = asyncio.Lock()
        self.log(f"prêt pour le service (rythme {rythme}s/action)")

    async def travailler(self, n=1):
        """Simule n actions élémentaires : durée = n x rythme. Rend la main à la boucle."""
        await asyncio.sleep(n * self.rythme)

    async def servir_plateau(self, commande):
        """Apporter un plateau et servir chaque consommation (utilisé par serveur ET bariste)."""
        self.log(f"j'apporte la commande '{commande}'")
        for conso in commande:
            self.log(f"je sers '{conso}'")
            await self.travailler()


class Serveur(Employé):

    async def prendre_commande(self):
        while True:
            self.log("prêt pour prendre une nouvelle commande...")
            commande = await self.clients.commande()
            if commande is None:
                break                    # plus de clients : la fin est gérée dans main()
            async with self.occupe:
                self.log(f"j'ai la commande '{commande}'")
                self.log(f"j'écris sur le post-it '{commande}'")
                await self.travailler()
                await self.pic.embrocher(commande)

    async def servir(self):
        while True:                      # boucle infinie : arrêtée par cancel() dans main()
            commande = await self.bar.evacuer()
            async with self.occupe:
                await self.servir_plateau(commande)
            self.bar.task_done()         # "ce plateau est entièrement traité" (pour bar.join())


class Bariste(Employé):

    async def preparer(self):
        while True:                      # arrêtée par cancel() dans main()
            postit = await self.pic.liberer()
            self.log(f"je commence la fabrication de '{postit}'")
            for conso in postit:
                self.log(f"je prépare '{conso}'")
                await self.travailler()
            self.log(f"la commande {postit} est prête")
            # EXTENSION 3 : s'il n'y a aucun post-it en attente, le bariste n'a rien de
            # mieux à faire : il sert lui-même, directement, sans passer par le bar.
            # Tout se fait dans la MÊME coroutine, donc il ne fait jamais deux choses à la fois.
            if self.pic.empty():
                self.log("le pic est vide, je sers moi-même")
                await self.servir_plateau(postit)
            else:
                await self.bar.recevoir(postit)
            self.pic.task_done()         # "ce post-it est entièrement traité" (pour pic.join())


def usage():
    print(f"usage: {sys.argv[0]} fichier")
    exit(1)


class Clients:
    def __init__(self, fname):
        commandes = []
        start = time.time()
        t = 0
        fmt = re.compile(r"(\d+)\s+(.*)")
        with open(fname, "r", encoding="utf-8") as f:
            for line in f:
                found = fmt.search(line)
                if found:
                    t += int(found.group(1))                     # délais cumulés
                    commandes.append((start + t * UNITE, found.group(2).split(",")))
        self.commandes = commandes[::-1]
        # EXTENSION 1 : la liste des clients est maintenant PARTAGÉE par 2 serveurs.
        self.verrou = asyncio.Lock()

    async def commande(self):
        # Sans verrou, les 2 serveurs liraient la même "prochaine commande", dormiraient
        # jusqu'à son heure, puis feraient chacun un pop() : le 2e récupérerait la commande
        # SUIVANTE en avance (condition de course). On réserve donc la commande (pop) sous
        # verrou, puis on attend son heure HORS verrou pour ne pas bloquer l'autre serveur.
        async with self.verrou:
            if len(self.commandes) == 0:
                return None
            quand, quoi = self.commandes.pop()
        await asyncio.sleep(max(0.0, quand - time.time()))
        return quoi


async def main(bariste, serveurs, pic, bar):
    # Tâches "de fond" : préparer et servir n'ont pas de fin naturelle (elles attendent
    # dans get()). On les lance, puis on les arrêtera explicitement.
    fond = [asyncio.create_task(bariste.preparer())]
    fond += [asyncio.create_task(s.servir()) for s in serveurs]

    # 1) tous les serveurs prennent les commandes jusqu'à épuisement des clients
    await asyncio.gather(*(s.prendre_commande() for s in serveurs))
    # 2) on attend que chaque post-it ait été traité (un task_done() par get())
    await pic.join()
    # 3) puis que chaque plateau posé sur le bar ait été servi
    await bar.join()
    # 4) plus rien ne peut arriver : on arrête les tâches de fond qui attendent dans get()
    for t in fond:
        t.cancel()
    await asyncio.gather(*fond, return_exceptions=True)   # attend la fin propre des annulations
    bariste.log("fin du service")


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
    bob = Bariste(le_pic, le_bar, les_clients, name="bob", verbose=True, rythme=0.3)
    alice = Serveur(le_pic, le_bar, les_clients, name="alice", verbose=True, rythme=0.5)
    charlie = Serveur(le_pic, le_bar, les_clients, name="charlie", verbose=True, rythme=0.8)
    asyncio.run(main(bob, [alice, charlie], le_pic, le_bar))
