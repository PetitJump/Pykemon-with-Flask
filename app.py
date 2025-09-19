from flask import Flask, render_template, request, redirect, url_for
from main import Jeu

app = Flask(__name__)
Partie = None
tour_actuel = "J1"

@app.route("/", methods=["GET", "POST"])
def start():
    global Partie, tour_actuel
    if request.method == "POST":
        pseudo1 = request.form["pseudo1"]
        pseudo2 = request.form["pseudo2"]
        Partie = Jeu()
        Partie.initialiser(pseudo1, pseudo2)
        tour_actuel = "J1"
        return redirect(url_for("game"))
    return render_template("start.html")

@app.route("/game")
def game():
    gagnant = Partie.gagnant() if Partie else None
    return render_template("game.html",
                           j1=Partie.J1,
                           j2=Partie.J2,
                           tour=tour_actuel,
                           gagnant=gagnant)

@app.route("/action/<joueur>/<int:choix>")
def action(joueur, choix):
    global tour_actuel
    if Partie.est_fini():
        return redirect(url_for("game"))

    if joueur == "J1" and tour_actuel == "J1":
        Partie.J1.action(choix, Partie.J2)
        if Partie.J2.est_ko():
            Partie.J2.retirer_pokemon()
        tour_actuel = "J2"

    elif joueur == "J2" and tour_actuel == "J2":
        Partie.J2.action(choix, Partie.J1)
        if Partie.J1.est_ko():
            Partie.J1.retirer_pokemon()
        tour_actuel = "J1"

    return redirect(url_for("game"))

@app.route("/choix/<joueur>")
def choix(joueur):
    # Page de sélection de Pokémon
    if joueur == "J1":
        vivants = [poke for poke in Partie.J1.pokemon if poke[1] > 0]
    else:
        vivants = [poke for poke in Partie.J2.pokemon if poke[1] > 0]
    return render_template("choix.html", joueur=joueur, vivants=vivants)

@app.route("/choisir/<joueur>/<int:index>")
def choisir(joueur, index):
    global tour_actuel
    if joueur == "J1" and tour_actuel == "J1":
        Partie.J1.choix_pokemon(index)
        tour_actuel = "J2"
    elif joueur == "J2" and tour_actuel == "J2":
        Partie.J2.choix_pokemon(index)
        tour_actuel = "J1"
    return redirect(url_for("game"))

if __name__ == "__main__":
    app.run(debug=True)
