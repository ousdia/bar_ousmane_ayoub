#!/usr/bin/env python3
"""
Borabora - Partie 1, étape 3 : journalisation dans /tmp/borabora.log via la classe Logable.
Usage : python3 partie1_etape3.py lundi      (et dans un 2e terminal : tail -f /tmp/borabora.log)
"""
import re
import sys
import time


class Logable:
    """Classe de base pour disposer d'une méthode log (code fourni)."""

    def __init__(self, name, verbose):
        self.name = name
        self.verbose = verbose

    def log(self, msg):
        if self.verbose:
            # logf est une variable GLOBALE, créée dans le bloc __main__
            print(f"[{self.name}] {msg}", file=logf, flush=True)


class Accessoire(list, Logable):
    """
    Héritage multiple : un accessoire EST une liste ET sait se loguer.
    On appelle explicitement les deux constructeurs parents.
    """

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
    """Code fourni par l'énoncé."""

    def __init__(self, pic, bar, clients, name, verbose):
        Logable.__init__(self, name, verbose)
        self.pic = pic
        self.bar = bar
        self.clients = clients
        self.step = 0
        self.log("prêt pour le service")


class Serveur(Employé):

    def prendre_commande(self):
        self.log("prêt pour prendre une nouvelle commande...")
        commande = self.clients.commande()
        if commande is None:
            return False
        self.log(f"j'ai la commande '{commande}'")
        self.log(f"j'écris sur le post-it '{commande}'")
        self.pic.embrocher(commande)
        return True

    def servir(self):
        commande = self.bar.evacuer()
        if commande is None:
            return False
        self.log(f"j'apporte la commande '{commande}'")
        for conso in commande:
            self.log(f"je sers '{conso}'")
        return True

    def run(self):
        if self.step == 0:
            while self.prendre_commande():
                pass
        else:
            while self.servir():
                pass
        self.step += 1


class Bariste(Employé):

    def preparer(self):
        postit = self.pic.liberer()
        if postit is None:
            return False
        self.log(f"je commence la fabrication de '{postit}'")
        for conso in postit:
            self.log(f"je prépare '{conso}'")
        self.bar.recevoir(postit)
        self.log(f"la commande {postit} est prête")
        return True

    def run(self):
        while self.preparer():
            pass


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


def main():
    alice.run()
    bob.run()
    alice.run()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()
    fcommandes = sys.argv[1]

    logfile = "/tmp/borabora.log"
    print(f"logging in {logfile}...")
    logf = open(logfile, "w", encoding="utf-8")   # global : visible dans Logable.log
    print("\n---", file=logf, flush=True)

    les_clients = Clients(fcommandes)
    le_pic = Pic(name="le_pic", verbose=False)
    le_bar = Bar(name="le_bar", verbose=False)
    bob = Bariste(le_pic, le_bar, les_clients, name="bob", verbose=False)
    alice = Serveur(le_pic, le_bar, les_clients, name="alice", verbose=True)
    main()
