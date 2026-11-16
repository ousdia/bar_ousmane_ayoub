#!/usr/bin/env python3
"""
Borabora - Partie 1, étape 2 : commandes lues dans un fichier (plus d'input).
Usage : python3 partie1_etape2.py lundi
"""
import re
import sys
import time


class Accessoire(list):
    pass


class Pic(Accessoire):
    def embrocher(self, postit):
        self.append(postit)

    def liberer(self):
        return self.pop() if len(self) > 0 else None     # LIFO, comme la trace attendue


class Bar(Accessoire):
    def recevoir(self, commande):
        self.append(commande)

    def evacuer(self):
        return self.pop() if len(self) > 0 else None


class Employé:
    def __init__(self, pic, bar, clients):
        self.pic = pic
        self.bar = bar
        self.clients = clients         # nouveau : l'employé connaît la source des commandes
        self.step = 0
        print(f"{type(self).__name__}: prêt pour le service")


class Serveur(Employé):

    def prendre_commande(self):
        # Le message est affiché AVANT d'attendre le client : il apparaît donc
        # 3 fois pour lundi (2 commandes + la tentative qui renvoie None).
        print("Serveur: prêt pour prendre une nouvelle commande...")
        commande = self.clients.commande()   # déjà une liste : Clients fait le split(",")
        if commande is None:
            return False
        print(f"Serveur: j'ai la commande '{commande}'")
        print(f"Serveur: j'écris sur le post-it '{commande}'")
        self.pic.embrocher(commande)
        return True

    def servir(self):
        commande = self.bar.evacuer()
        if commande is None:
            return False
        print(f"Serveur: j'apporte la commande '{commande}'")
        for conso in commande:
            print(f"Serveur: je sers '{conso}'")
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
        print(f"Bariste: je commence la fabrication de '{postit}'")
        for conso in postit:
            print(f"Bariste: je prépare '{conso}'")
        self.bar.recevoir(postit)
        print(f"Bariste: la commande {postit} est prête")
        return True

    def run(self):
        while self.preparer():
            pass


# ---------------------------------------------------------------- code fourni
def usage():
    print(f"usage: {sys.argv[0]} fichier")
    exit(1)


class Clients:
    def __init__(self, fname):
        commandes = []
        start = time.time()
        fmt = re.compile(r"(\d+)\s+(.*)")      # "<entier> <reste de la ligne>"
        with open(fname, "r", encoding="utf-8") as f:
            for line in f:
                found = fmt.search(line)
                if found:
                    when = int(found.group(1))
                    what = found.group(2)
                    # NB : instant ABSOLU start+when (voir la remarque sur "mardi")
                    commandes.append((start + when, what.split(",")))
        self.commandes = commandes[::-1]       # inversée : pop() rend la 1re ligne du fichier

    def commande(self):
        if len(self.commandes) > 0:
            while True:                        # attente active jusqu'à l'heure de la commande
                if time.time() >= self.commandes[-1][0]:   # >= : sinon délai 0 peut boucler un peu
                    return self.commandes.pop()[1]
        else:
            return None
# ----------------------------------------------------------------------------


def main():
    alice.run()
    bob.run()
    alice.run()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()
    fcommandes = sys.argv[1]

    le_pic = Pic()
    le_bar = Bar()
    les_clients = Clients(fcommandes)
    bob = Bariste(le_pic, le_bar, les_clients)
    alice = Serveur(le_pic, le_bar, les_clients)
    main()
