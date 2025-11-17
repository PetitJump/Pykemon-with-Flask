# Pokemon Flask
Projet coder avec l'IA a partir de mon code sur le terminal coder par PetitJump: [Code GitHub](https://github.com/PetitJump/Pykemon-1v1)
Ce projet est une petite application web construite avec Flask, simulant un combat Pokémon en tour par tour.
Chaque joueur reçoit 3 Pokémon tirés aléatoirement depuis data.json, et peut attaquer, soigner ou changer de Pokémon pendant la partie.

🚀 Fonctionnement du jeu
Au lancement, chaque joueur saisit son pseudo.
Le jeu pioche 3 Pokémon aléatoires par joueur.

Chaque Pokémon possède :
- des PV
- un type
- une attaque
- un soin
- une faiblesse

Les joueurs jouent à tour de rôle :
- Attaquer : dégâts basés sur la puissance + bonus si avantage de type
- Soigner : restaure un montant fixe de PV
- Changer : sélection du Pokémon actif
- Un Pokémon K.O. force son joueur à le remplacer immédiatement.

La partie se termine quand un joueur n’a plus aucun Pokémon vivant.