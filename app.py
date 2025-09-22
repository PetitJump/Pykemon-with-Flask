# app.py
from flask import Flask, render_template, request, redirect, url_for
from main import Jeu

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

jeu = Jeu()  # instance vide jusqu'au start
started = False

@app.route("/", methods=["GET", "POST"])
def start():
    global jeu, started
    if request.method == "POST":
        p1 = request.form.get("pseudo1") or "J1"
        p2 = request.form.get("pseudo2") or "J2"
        jeu = Jeu()
        jeu.initialiser(p1, p2)
        started = True
        return redirect(url_for("game"))
    return render_template("start.html")

@app.route("/game")
def game():
    if not started:
        return redirect(url_for("start"))
    state = jeu.get_state()
    return render_template("game.html", state=state)

@app.route("/action", methods=["POST"])
def action():
    if not started:
        return redirect(url_for("start"))
    player = request.form.get("player")  # "J1" or "J2"
    action = int(request.form.get("action", 0))
    # if action == 3 (change) we prefer to redirect to choose page for that player
    if action == 3 and 'choix_index' not in request.form:
        # go to choose page
        return redirect(url_for("choose", player=player))
    choix_index = request.form.get("choix_index")
    choix_index = int(choix_index) if choix_index is not None and choix_index != "" else None

    res = jeu.play_action(player, action, choix_index)
    if res.get("status") == "need_choice":
        # redirect owner to choose replacement
        who = res.get("who_needs_choice")
        return redirect(url_for("choose", player=who))
    return redirect(url_for("game"))

@app.route("/choose/<player>", methods=["GET", "POST"])
def choose(player):
    if not started:
        return redirect(url_for("start"))
    # player is 'J1' or 'J2' who must choose a replacement
    if request.method == "POST":
        idx = int(request.form.get("index"))
        res = jeu.submit_replacement(player, idx)
        return redirect(url_for("game"))
    # GET: build list of alive pokemons for that player
    player_obj = jeu.J1 if player == "J1" else jeu.J2
    vivants = [ (i, p) for i, p in enumerate(player_obj.pokemons) if p[1] > 0 ]
    return render_template("choose.html", player_label=player, vivants=vivants, player_name=player_obj.nom)

if __name__ == "__main__":
    app.run(debug=True)
