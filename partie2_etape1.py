#!/usr/bin/env python3
"""
Borabora - Partie 2, étape 1 : les 3 tâches deviennent des coroutines lancées par gather().
Les 3 tâches de haut niveau : (1) prendre les commandes, (2) préparer, (3) servir.

ATTENDU (voulu par l'énoncé) : cette version N'EXÉCUTE PAS toutes les tâches.
Usage : python3 partie2_etape1.py lundi ; puis cat /tmp/borabora.log
"""
import asyncio
import re
import sys
import time


class Logable:
    def __init__(self, name, verbose):
        self.name = name
        self.verbose = verbose

    def log(self, msg):
        if self.verbose:
            print(f"[{self.name}] {msg}", file=logf, flush=True)


class Accessoire(list, Logable):
    def __init__(self, name, verbose):
        list.__init__(self)
        Logable.__init__(self, name, verbose)


class Pic(Accessoire):
    def embrocher(self, postit):
        self.log(f"post-it '{postit}' embroché, {len(self)} post-it(s) à traiter")
        self.append(postit)

    def liberer(self):
        if len(self) > 0:
            postit = self.pop()
            self.log(f"post-it '{postit}' libéré, {len(self)} post-it(s) à traiter")
            return postit
        return None


class Bar(Accessoire):
    def recevoir(self, commande):
        self.log(f"'{commande}' posée, {len(self)} commande(s) à servir")
        self.append(commande)

    def evacuer(self):
        if len(self) > 0:
            commande = self.pop()
            self.log(f"'{commande}' évacuée, {len(self)} commande(s) à servir")
            return commande
        return None


class Employé(Logable):
    def __init__(self, pic, bar, clients, name, verbose):
        Logable.__init__(self, name, verbose)
        self.pic = pic
        self.bar = bar
        self.clients = clients
        self.log("prêt pour le service")


class Serveur(Employé):

    async def prendre_commande(self):          # TÂCHE 1 (coroutine)
        while True:
            self.log("prêt pour prendre une nouvelle commande...")
            commande = self.clients.commande()
            if commande is None:
                break
            self.log(f"j'ai la commande '{commande}'")
            self.log(f"j'écris sur le post-it '{commande}'")
            self.pic.embrocher(commande)

    async def servir(self):                    # TÂCHE 3 (coroutine)
        while True:
            commande = self.bar.evacuer()
            if commande is None:               # bar vide AU MOMENT où on regarde => on s'arrête
                break
            self.log(f"j'apporte la commande '{commande}'")
            for conso in commande:
                self.log(f"je sers '{conso}'")

    async def run(self):
        # le serveur porte 2 des 3 tâches : on les lance toutes les deux
        await asyncio.gather(self.prendre_commande(), self.servir())


class Bariste(Employé):

    async def preparer(self):                  # TÂCHE 2 (coroutine)
        while True:
            postit = self.pic.liberer()
            if postit is None:                 # pic vide AU MOMENT où on regarde => on s'arrête
                break
            self.log(f"je commence la fabrication de '{postit}'")
            for conso in postit:
                self.log(f"je prépare '{conso}'")
            self.bar.recevoir(postit)
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
        if len(self.commandes) > 0:
            while True:
                if time.time() >= self.commandes[-1][0]:
                    return self.commandes.pop()[1]
        return None


async def main():
    # gather() lance les coroutines dans l'ordre : bob d'abord.
    # Bob trouve le pic VIDE (Alice n'a encore rien embroché) -> preparer() s'arrête aussitôt.
    # Alice prend ensuite les commandes, puis servir() trouve le bar VIDE -> s'arrête.
    # Résultat : les commandes sont prises mais jamais préparées ni servies.
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
