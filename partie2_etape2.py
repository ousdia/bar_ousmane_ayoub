#!/usr/bin/env python3
"""
Borabora - Partie 2, étape 2 : list remplacée par asyncio.Queue (file FIFO asynchrone).
Toutes les tâches s'exécutent à nouveau, mais l'une après l'autre (pas encore de coopération).
Usage : python3 partie2_etape2.py lundi ; puis cat /tmp/borabora.log
"""
import asyncio
import re
import sys
import time

FIN = None   # "post-it de fin" (sentinelle, ou poison pill) : signale qu'il n'y aura plus rien


class Logable:
    def __init__(self, name, verbose):
        self.name = name
        self.verbose = verbose

    def log(self, msg):
        if self.verbose:
            print(f"[{self.name}] {msg}", file=logf, flush=True)


class Accessoire(asyncio.Queue, Logable):
    """Un accessoire est maintenant une file asyncio.Queue (FIFO) qui sait se loguer."""

    def __init__(self, name, verbose):
        asyncio.Queue.__init__(self)
        Logable.__init__(self, name, verbose)


class Pic(Accessoire):
    async def embrocher(self, postit):
        await self.put(postit)
        self.log(f"post-it '{postit}' embroché, {self.qsize()} post-it(s) à traiter")

    async def liberer(self):
        # get() est BLOQUANT au sens asyncio : si la file est vide, la coroutine est
        # suspendue (sans consommer de CPU) jusqu'à ce qu'un post-it arrive.
        # C'est LA différence avec list.pop() qui répondait "rien" tout de suite.
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
        self.log("prêt pour le service")


class Serveur(Employé):

    async def prendre_commande(self):
        while True:
            self.log("prêt pour prendre une nouvelle commande...")
            commande = self.clients.commande()
            if commande is None:
                # Plus de clients : on embroche le post-it de fin pour prévenir le bariste.
                # Sans ça, Bob attendrait éternellement dans get() et le programme ne finirait jamais.
                await self.pic.embrocher(FIN)
                break
            self.log(f"j'ai la commande '{commande}'")
            self.log(f"j'écris sur le post-it '{commande}'")
            await self.pic.embrocher(commande)

    async def servir(self):
        while True:
            commande = await self.bar.evacuer()   # attend qu'un plateau arrive
            if commande is FIN:
                break
            self.log(f"j'apporte la commande '{commande}'")
            for conso in commande:
                self.log(f"je sers '{conso}'")

    async def run(self):
        await asyncio.gather(self.prendre_commande(), self.servir())


class Bariste(Employé):

    async def preparer(self):
        while True:
            postit = await self.pic.liberer()     # attend qu'un post-it arrive
            if postit is FIN:
                await self.bar.recevoir(FIN)      # on transmet la fin au serveur
                break
            self.log(f"je commence la fabrication de '{postit}'")
            for conso in postit:
                self.log(f"je prépare '{conso}'")
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
        fmt = re.compile(r"(\d+)\s+(.*)")
        with open(fname, "r", encoding="utf-8") as f:
            for line in f:
                found = fmt.search(line)
                if found:
                    commandes.append((start + int(found.group(1)), found.group(2).split(",")))
        self.commandes = commandes[::-1]

    def commande(self):
        # Toujours une attente ACTIVE et synchrone : elle bloque toute la boucle d'évènements.
        if len(self.commandes) > 0:
            while True:
                if time.time() >= self.commandes[-1][0]:
                    return self.commandes.pop()[1]
        return None


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
