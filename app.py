# app.py
from flask import Flask, render_template, request, redirect, url_for
from random import sample
import json, os

app = Flask(__name__)
app.static_folder = 'static'

# ---------- charger data.json (ta liste) ----------
DATA_PATH = os.path.join(os.path.dirname(__file__), "data.json")
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    RAW_POKES = json.load(f)


# ---------- utilitaires pour créer instances indépendantes ----------
def make_pokemon(entry):
    """
    entry: [name, pv, type, [[atkName, atkPower], [healName, healPower]], weakness]
    renvoie dict:
    {
      'name','hp','max_hp','type','moves':[{'name','power'},{...}],'weakness'
    }
    """
    return {
        "name": entry[0],
        "hp": int(entry[1]),
        "max_hp": int(entry[1]),
        "type": entry[2],
        "moves": [
            {"name": entry[3][0][0], "power": int(entry[3][0][1])},
            {"name": entry[3][1][0], "power": int(entry[3][1][1])}
        ],
        "weakness": entry[4]
    }


# ---------- Classes jeu ----------
class Player:
    def __init__(self, name, pokemons):
        self.name = name
        # pokemons is a list of dicts (from make_pokemon)
        self.pokemons = pokemons
        self.current_index = 0  # index in self.pokemons

    def current(self):
        if not self.pokemons:
            return None
        # clamp index
        if self.current_index >= len(self.pokemons):
            self.current_index = max(0, len(self.pokemons) - 1)
        return self.pokemons[self.current_index]

    def alive_indices(self):
        return [i for i, p in enumerate(self.pokemons) if p["hp"] > 0]

    def attack_damage_against(self, other):
        attacker = self.current()
        defender = other.current()
        if not attacker or not defender:
            return 0
        base = attacker["moves"][0]["power"]
        bonus = 20 if attacker["type"] == defender["weakness"] else 0
        return base + bonus

    def heal_amount(self):
        cur = self.current()
        return cur["moves"][1]["power"] if cur else 0

    def apply_damage_to_current(self, dmg):
        cur = self.current()
        if not cur:
            return
        cur["hp"] = max(0, cur["hp"] - int(dmg))

    def apply_heal_to_current(self, amount):
        cur = self.current()
        if not cur:
            return
        cur["hp"] = min(cur["max_hp"], cur["hp"] + int(amount))

    def remove_current(self):
        """Remove current pokemon (by index). Return True if removed."""
        if not self.pokemons:
            return False
        idx = self.current_index
        # pop by index -> avoids list.remove(x) problems
        self.pokemons.pop(idx)
        # adjust index
        if idx >= len(self.pokemons):
            self.current_index = max(0, len(self.pokemons) - 1)
        return True

    def choose(self, index):
        """Choose index in current pokemons list (0-based)."""
        if 0 <= index < len(self.pokemons) and self.pokemons[index]["hp"] > 0:
            self.current_index = index
            return True
        return False

    def has_any(self):
        return len(self.pokemons) > 0

    def to_small(self):
        """Return small dict for template convenience"""
        cur = self.current()
        return {
            "name": self.name,
            "pokemons": self.pokemons,
            "current": cur,
            "current_index": self.current_index,
            "alive_count": len(self.alive_indices())
        }


class Game:
    def __init__(self):
        self.p1 = None
        self.p2 = None
        self.turn = 1  # 1 = p1, 2 = p2
        self.pending_replacement = None  # 'p1' or 'p2' when we need a forced replacement

    def start(self, name1, name2):
        # sample 3 pokemons for each player and instantiate
        sample1 = sample(RAW_POKES, k=3)
        sample2 = sample(RAW_POKES, k=3)
        p1_list = [make_pokemon(e) for e in sample1]
        p2_list = [make_pokemon(e) for e in sample2]
        self.p1 = Player(name1, p1_list)
        self.p2 = Player(name2, p2_list)
        self.turn = 1
        self.pending_replacement = None

    def current_player(self):
        return self.p1 if self.turn == 1 else self.p2

    def opponent_player(self):
        return self.p2 if self.turn == 1 else self.p1

    def label_current(self):
        return "p1" if self.turn == 1 else "p2"

    def label_opponent(self):
        return "p2" if self.turn == 1 else "p1"

    def is_over(self):
        return (not self.p1.has_any()) or (not self.p2.has_any())

    def winner_name(self):
        if not self.p1.has_any():
            return self.p2.name
        if not self.p2.has_any():
            return self.p1.name
        return None

    def do_attack(self):
        actor = self.current_player()
        target = self.opponent_player()
        dmg = actor.attack_damage_against(target)
        target.apply_damage_to_current(dmg)
        return dmg

    def do_heal(self):
        actor = self.current_player()
        heal = actor.heal_amount()
        actor.apply_heal_to_current(heal)
        return heal

    def do_remove_if_dead(self):
        target = self.opponent_player()
        cur = target.current()
        if cur and cur["hp"] <= 0:
            target.remove_current()
            if not target.has_any():
                return "game_over"
            # force replacement by owner of target
            self.pending_replacement = "p1" if target is self.p1 else "p2"
            return "need_replace"
        return "ok"

    def switch_turn(self):
        self.turn = 2 if self.turn == 1 else 1

    def to_state(self):
        # convenience structure for templates
        return {
            "p1": self.p1.to_small(),
            "p2": self.p2.to_small(),
            "turn": self.turn,
            "pending_replacement": self.pending_replacement,
            "winner": self.winner_name()
        }


# ---------- GLOBAL game instance ----------
GAME = Game()


# ---------- ROUTES ----------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    name1 = request.form.get("pseudo1") or "Joueur 1"
    name2 = request.form.get("pseudo2") or "Joueur 2"
    GAME.start(name1, name2)
    # after starting, go to selection of starting pokemon for player 1
    return redirect(url_for("select_start", player="p1"))


@app.route("/select/<player>", methods=["GET", "POST"])
def select_start(player):
    """
    Used for:
     - initial selection at beginning (select_start called in start -> p1 then p2)
     - voluntary change (when ?voluntary=1)
     - forced replacement after K.O. (when ?replacement=1)
    Query params:
        ?voluntary=1   => voluntary change (will switch turn after choose)
        ?replacement=1 => forced replacement (after KO) (after choose, the replaced player plays)
    """
    voluntary = request.args.get("voluntary") == "1"
    replacement = request.args.get("replacement") == "1"

    # pick player obj
    player_obj = GAME.p1 if player == "p1" else GAME.p2
    # If GET: show the list of current pokemons (with indices)
    if request.method == "GET":
        # build list of (index, pokemon) for template
        choices = [(i, p) for i, p in enumerate(player_obj.pokemons)]
        return render_template("select.html", player_label=player, player_name=player_obj.name,
                               choices=choices, voluntary=voluntary, replacement=replacement)

    # POST: user submitted index (1-based value), convert to 0-based
    idx = int(request.form.get("index", 0))
    # ensure valid
    if idx < 0 or idx >= len(player_obj.pokemons):
        return redirect(url_for("select_start", player=player, voluntary=int(voluntary), replacement=int(replacement)))

    # set player's current index
    player_obj.current_index = idx

    # If this selection was a **forced replacement** (replacement==True),
    # the replaced player should **take the next turn** (they play now).
    if replacement:
        GAME.pending_replacement = None
        GAME.turn = 1 if player == "p1" else 2
        return redirect(url_for("game"))

    # If this selection came from initial selection flow:
    # if selecting p1 initially, go to p2 selection; else go to game
    # If voluntary change (player changed willingly), switch turn to opponent after change
    if request.args.get("initial") == "1":
        if player == "p1":
            return redirect(url_for("select_start", player="p2", initial=1))
        else:
            return redirect(url_for("game"))

    if voluntary:
        # voluntary change -> after change, switch turn to opponent
        GAME.switch_turn()
        return redirect(url_for("game"))

    # default -> go to game
    return redirect(url_for("game"))


@app.route("/game")
def game():
    # if no game / not started
    if not GAME.p1 or not GAME.p2:
        return redirect(url_for("index"))

    # if over -> send to end
    winner = GAME.winner_name()
    if winner:
        return render_template("end.html", winner=winner)

    # prepare template values: compute damage/heal numbers
    p1 = GAME.p1
    p2 = GAME.p2

    p1_attack = p1.attack_damage_against(p2)
    p1_heal = p1.heal_amount()
    p2_attack = p2.attack_damage_against(p1)
    p2_heal = p2.heal_amount()

    state = GAME.to_state()
    # add computed numbers to state for template
    state["p1"]["attack_value"] = p1_attack
    state["p1"]["heal_value"] = p1_heal
    state["p2"]["attack_value"] = p2_attack
    state["p2"]["heal_value"] = p2_heal

    return render_template("game.html", state=state)


@app.route("/action", methods=["POST"])
def action():
    # action from current player
    act = request.form.get("action")  # "attack" / "heal" / "change"
    if GAME.pending_replacement:
        # cannot act while replacement is pending
        return redirect(url_for("select_start", player=GAME.pending_replacement, replacement=1))

    if act == "attack":
        dmg = GAME.do_attack()
        after = GAME.do_remove_if_dead()
        if after == "game_over":
            winner = GAME.winner_name()
            return render_template("end.html", winner=winner)
        if after == "need_replace":
            # redirect owner of the player who lost to select replacement
            who = GAME.pending_replacement  # 'p1' or 'p2'
            return redirect(url_for("select_start", player=who, replacement=1))
        # otherwise, turn switches
        GAME.switch_turn()
        return redirect(url_for("game"))

    elif act == "heal":
        GAME.do_heal()
        GAME.switch_turn()
        return redirect(url_for("game"))

    elif act == "change":
        # voluntary change -> go to select page with voluntary flag
        player_label = GAME.label_current()
        return redirect(url_for("select_start", player=player_label, voluntary=1))

    return redirect(url_for("game"))


@app.route("/end")
def end():
    winner = GAME.winner_name()
    return render_template("end.html", winner=winner)


if __name__ == "__main__":
    app.run(debug=True)
