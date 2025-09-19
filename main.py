from random import sample
import json, os

class Jeu:
    def __init__(self):
        self.J1 = None
        self.J2 = None

    def generation_pokedex(self):  
        pokedex = sample(total_pokemon, k=3)
        actuel = []
        for poke in pokedex:
            actuel.append([poke[0], poke[1], poke[2],
                          [(poke[3][0][0], poke[3][0][1]), (poke[3][1][0], poke[3][1][1])],
                          poke[4]])
        return actuel

    def initialiser(self, pseudo1, pseudo2):
        list_poke1 = self.generation_pokedex()
        list_poke2 = self.generation_pokedex()
        self.J1 = Joueur(pseudo1, list_poke1, 0)
        self.J2 = Joueur(pseudo2, list_poke2, 0)

    def est_fini(self):
        return len(self.J1.pokemon) == 0 or len(self.J2.pokemon) == 0

    def gagnant(self):
        if len(self.J1.pokemon) == 0:
            return self.J2.nom
        elif len(self.J2.pokemon) == 0:
            return self.J1.nom
        return None

class Joueur:
    def __init__(self, nom, pokemon, poke_en_cour):
        self.nom = nom
        self.pokemon = pokemon
        self.poke_en_cour = self.pokemon[poke_en_cour]
    
    def action(self, action, adv, choix_index=None):
        if action == 1:  # Attaque
            ajout = 0
            if self.poke_en_cour[2] == adv.poke_en_cour[4]:
                ajout = 20
            adv.poke_en_cour[1] -= (self.poke_en_cour[3][0][1] + ajout)
            if adv.poke_en_cour[1] < 0:
                adv.poke_en_cour[1] = 0

        elif action == 2:  # Soin
            self.poke_en_cour[1] += self.poke_en_cour[3][1][1]
        
        elif action == 3 and choix_index is not None:  # Changer Pokémon
            self.choix_pokemon(choix_index)

    def choix_pokemon(self, index):
        vivants = [poke for poke in self.pokemon if poke[1] > 0]
        if vivants:
            self.poke_en_cour = vivants[index]

    def est_ko(self):
        return self.poke_en_cour[1] <= 0

    def retirer_pokemon(self):
        if self.poke_en_cour in self.pokemon:
            self.pokemon.remove(self.poke_en_cour)
            if self.pokemon:
                self.poke_en_cour = self.pokemon[0]

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

with open('data.json', 'r', encoding='utf-8') as f:
    total_pokemon = json.load(f)
