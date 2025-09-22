# main.py
from random import sample
import json, os

with open('data.json', 'r', encoding='utf-8') as f:
    total_pokemon = json.load(f)

def _copy_poke(src):
    # Reconstruit une entrée pour garder une instance indépendante
    return [
        src[0],
        int(src[1]),
        src[2],
        [(src[3][0][0], int(src[3][0][1])), (src[3][1][0], int(src[3][1][1]))],
        src[4]
    ]

class Joueur:
    def __init__(self, nom, pokemons, current_index=0):
        # pokemons : liste de listes [nom, pv, type, [(atk, dmg),(soin, val)], faiblesse]
        self.nom = nom
        self.pokemons = [ _copy_poke(p) for p in pokemons ]
        self.current = current_index if 0 <= current_index < len(self.pokemons) else 0

    def get_current(self):
        if not self.pokemons:
            return None
        if self.current >= len(self.pokemons):
            self.current = 0
        return self.pokemons[self.current]

    def alive_indices(self):
        return [i for i, p in enumerate(self.pokemons) if p[1] > 0]

    def attack_damage_against(self, other):
        atk = self.get_current()[3][0][1]
        bonus = 20 if self.get_current()[2] == other.get_current()[4] else 0
        return atk + bonus

    def heal_amount(self):
        return self.get_current()[3][1][1]

    def apply_damage_to_current(self, dmg):
        p = self.get_current()
        if p is None:
            return
        p[1] = max(0, p[1] - int(dmg))

    def apply_heal_to_current(self, amount):
        p = self.get_current()
        if p is None:
            return
        p[1] = int(p[1]) + int(amount)

    def remove_current_if_dead(self):
        """Retire le pokémon courant s'il est mort. Retourne True si retiré."""
        p = self.get_current()
        if p is None:
            return False
        if p[1] <= 0:
            # retire l'objet courant
            self.pokemons.pop(self.current)
            # ajuste l'index courant
            if self.current >= len(self.pokemons):
                self.current = max(0, len(self.pokemons) - 1)
            return True
        return False

    def choose_pokemon(self, index):
        """Choisit un pokémon par index (dans la liste actuelle)."""
        if 0 <= index < len(self.pokemons) and self.pokemons[index][1] > 0:
            self.current = index
            return True
        return False

    def has_pokemons(self):
        return len(self.pokemons) > 0

    def to_dict(self):
        """Renvoie un dict pratique pour templates"""
        cur = self.get_current()
        return {
            "nom": self.nom,
            "pokemons": self.pokemons,
            "actuel": cur,
            "vivants": len(self.alive_indices())
        }


class Jeu:
    def __init__(self):
        self.J1 = None
        self.J2 = None
        self.tour = 1  # 1 = J1, 2 = J2
        self.pending_choice_for = None  # 'J1' ou 'J2' si on attend un remplaçant

    def generation_pokedex(self):
        picks = sample(total_pokemon, k=3)
        return [ _copy_poke(p) for p in picks ]

    def initialiser(self, pseudo1, pseudo2):
        l1 = self.generation_pokedex()
        l2 = self.generation_pokedex()
        self.J1 = Joueur(pseudo1, l1, 0)
        self.J2 = Joueur(pseudo2, l2, 0)
        self.tour = 1
        self.pending_choice_for = None

    def get_state(self):
        return {
            "j1": self.J1.to_dict(),
            "j2": self.J2.to_dict(),
            "tour": "J1" if self.tour == 1 else "J2",
            "pending_choice_for": self.pending_choice_for,
            "gagnant": self._gagnant()
        }

    def _gagnant(self):
        if not self.J1.has_pokemons():
            return self.J2.nom
        if not self.J2.has_pokemons():
            return self.J1.nom
        return None

    def play_action(self, player_label, action, choix_index=None):
        """
        player_label: 'J1' or 'J2' (who is performing the action)
        action: 1 attack, 2 heal, 3 change
        choix_index: integer index when changing or when needed
        Retourne dict: {'status': 'ok'|'need_choice'|'game_over'|'error', 'message':..., 'who_needs_choice': 'J1'|'J2'}
        """
        # validate turn
        if self._gagnant():
            return {"status":"game_over", "message":f"Partie terminée. {self._gagnant()} a gagné."}

        if (self.tour == 1 and player_label != "J1") or (self.tour == 2 and player_label != "J2"):
            return {"status":"error", "message":"Ce n'est pas votre tour."}

        actor = self.J1 if player_label == "J1" else self.J2
        target = self.J2 if player_label == "J1" else self.J1

        # ACTIONS
        if action == 1:  # attack
            dmg = actor.attack_damage_against(target)
            target.apply_damage_to_current(dmg)

            # si mort
            if target.get_current() and target.get_current()[1] <= 0:
                # retire le pokémon mort
                target.remove_current_if_dead()
                if not target.has_pokemons():
                    return {"status":"game_over", "message":f"{actor.nom} a gagné !", "winner": actor.nom}
                # on attend le choix du propriétaire du joueur qui a perdu le pokémon
                self.pending_choice_for = "J1" if target is self.J1 else "J2"
                # On NE change PAS le tour : l'ordre après remplacement sera géré dans choose_submit
                return {"status":"need_choice", "who_needs_choice":self.pending_choice_for, "message":"Un pokémon est K.O. Choisissez un remplaçant."}

        elif action == 2:  # heal
            heal = actor.heal_amount()
            actor.apply_heal_to_current(heal)

        elif action == 3:  # change
            # si choix_index est fourni : on change maintenant
            if choix_index is None:
                # caller should redirect to choose page
                return {"status":"need_choose_now", "message":"Choix demandé"}
            ok = actor.choose_pokemon(choix_index)
            if not ok:
                return {"status":"error", "message":"Choix de Pokémon invalide."}
        else:
            return {"status":"error", "message":"Action inconnue."}

        # Si on arrive ici et pas de besoin de remplacement -> passer le tour
        self.tour = 2 if self.tour == 1 else 1
        return {"status":"ok", "message":"Action appliquée, tour changé."}

    def submit_replacement(self, player_label, choix_index):
        """Appelé après que pending_choice_for soit défini. Le joueur concerné choisit son remplaçant."""
        if self.pending_choice_for != player_label:
            return {"status":"error", "message":"Aucune sélection attendue pour ce joueur."}
        player = self.J1 if player_label == "J1" else self.J2
        ok = player.choose_pokemon(choix_index)
        if not ok:
            return {"status":"error", "message":"Choix invalide."}
        # après remplacement, c'est au joueur qui a remplacé de jouer (comme dans la version console)
        self.tour = 1 if player_label == "J1" else 2
        self.pending_choice_for = None
        return {"status":"ok", "message":"Remplacement effectué."}
