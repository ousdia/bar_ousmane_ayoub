#!/usr/bin/env python3
"""
Borabora - Partie 1, étape 1 : version séquentielle, commandes saisies au clavier.
"""


class Accessoire(list):
    """Un accessoire n'est rien d'autre qu'une liste (énoncé : "qui n'est autre que list")."""
    pass


class Pic(Accessoire):
    """Contient les post-it (commandes à fabriquer)."""

    def embrocher(self, postit):
        self.append(postit)            # on ajoute à la fin de la liste

    def liberer(self):
        if len(self) > 0:
            # pop() SANS argument retire le DERNIER élément (comportement de pile, LIFO).
            # C'est ce que donne la trace attendue : Bob prépare d'abord la dernière
            # commande embrochée (tequila sunrise avant planteur).
            return self.pop()
        return None


class Bar(Accessoire):
    """Contient les plateaux préparés, en attente d'être servis. Calquée sur Pic."""

    def recevoir(self, commande):
        self.append(commande)

    def evacuer(self):
        if len(self) > 0:
            return self.pop()
        return None


class Employé:
    """Initialisations communes à Serveur et Bariste."""

    def __init__(self, pic, bar):
        self.pic = pic
        self.bar = bar
        self.step = 0                  # sert au serveur pour alterner ses deux activités
        # type(self).__name__ vaut "Serveur" ou "Bariste" selon l'objet réellement créé
        print(f"{type(self).__name__}: prêt pour le service")


class Serveur(Employé):

    def prendre_commande(self):
        """Prend UNE commande et embroche un post-it. Renvoie False s'il n'y a plus de commande."""
        commande = input("Serveur: prêt pour prendre une commande : ")
        if not commande:               # ligne vide => fin de la prise de commandes
            return False
        print(f"Serveur: j'ai la commande '{commande}'")
        postit = commande.split(",")   # "planteur,piña colada" -> ['planteur', 'piña colada']
        print(f"Serveur: j'écris sur le post-it '{postit}'")
        self.pic.embrocher(postit)
        return True

    def servir(self):
        """Prend UN plateau sur le bar et le sert. Renvoie False si le bar est vide."""
        commande = self.bar.evacuer()
        if commande is None:
            return False
        print(f"Serveur: j'apporte la commande '{commande}'")
        for conso in commande:
            print(f"Serveur: je sers '{conso}'")
        return True

    def run(self):
        """1er appel : prendre toutes les commandes ; 2e appel : tout servir."""
        if self.step == 0:
            while self.prendre_commande():
                pass
        else:
            while self.servir():
                pass
        self.step += 1


class Bariste(Employé):

    def preparer(self):
        """Prend UN post-it, prépare la commande et la dépose sur le bar."""
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


def main():
    # Enchaînement séquentiel : prise de commandes -> préparation -> service
    alice.run()
    bob.run()
    alice.run()


if __name__ == "__main__":
    le_pic = Pic()
    le_bar = Bar()
    bob = Bariste(le_pic, le_bar)      # Bob créé en premier : "Bariste: prêt..." s'affiche d'abord
    alice = Serveur(le_pic, le_bar)
    main()
