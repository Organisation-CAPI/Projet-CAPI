# Point d'entrée de l'application Flask
'''
@file
@brief Fichier principal de l'application Flask.

@details
Ce fichier initialise l'application Flask, configure les routes et importe les autres modules nécessaires.
L'objet session de Flask est utilisé pour stocker les données globales nécessaires à ce projet.
'''

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, Response
import numpy as np
import json

from models.app_manager import AppManager
import os
import uuid
from constantes import *

# Chemin vers le fichier backlog.json
BACKLOG_FILE = os.path.join(os.path.dirname(__file__), 'data', 'backlog.json')

# créer l'application Flask
app = Flask(__name__)

# Secret key pour le développement local
app.secret_key = CLE_SECRETE

# Configurer le nom du serveur
app.config['SERVER_NAME'] = NOM_SERVEUR

# création de l'objet AppManager avec chargement du backlog
app_manager = AppManager(backlog_file=BACKLOG_FILE)

# supprimer le cache du navigateur
@app.after_request
def add_header(response):
    """
    @brief Désactive le cache du navigateur.

    @param response La réponse HTTP générée par Flask.
    
    @return La réponse modifiée avec les en-têtes pour désactiver le cache.
    """
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# injecter les variables globales dans les templates 
@app.context_processor
def inject_globals():
    """
    @brief Injecte des variables globales dans les templates.

    @return Dictionnaire contenant les variables globales (is_sm et is_po).
    """
    # Récupérer le pseudo actif depuis la session
    pseudo_actif = session.get('pseudo_actif')
    participant_actif = None

    # Si un pseudo actif est défini, récupérer ses données
    if pseudo_actif:
        participant_actif = next((p for p in app_manager.state["participants"] if p["pseudo"] == pseudo_actif), None)

    # Injecter les données dans les templates
    return {
        "pseudo_actif": pseudo_actif,
        "participant_actif": participant_actif,
        "state": app_manager.state,
    }

# Route par défaut
@app.route('/')
def home():
    """
    @brief Point d'entrée de l'application.

    @details Redirige les utilisateurs vers la page de connexion

    @return Redirection vers la page de connexion.
    """
    return redirect(url_for('login'))

# Page de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    @brief Gestion de la connexion des participants.

    @details Cette route permet de se connecter avec un pseudo valide.
    Si le pseudo est valide, un ID de session unique est généré,
    et l'utilisateur est redirigé vers la salle de vote.

    @return Page de connexion ou redirection vers la salle 
    de vote après authentification.
    """
    if request.method == 'POST':
        pseudo = request.form['pseudo'].strip().lower()
        
        # Générer un ID de session unique
        session_id = str(uuid.uuid4())  
        print("session_id login ", session_id)

         # Vérifier si le pseudo est valide
        fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
        participants_backlog = fonctionnalite_prioritaire.participants if fonctionnalite_prioritaire else []
        print("participants_backlog : ",participants_backlog)

       # Autoriser uniquement PO, SM ou participants du backlog
        if pseudo not in ["po","PO","sm", "SM"] and pseudo not in participants_backlog:
            flash(f"Le pseudo '{pseudo}' n'est pas autorisé à se connecter pour cette session.", "danger")
            return redirect(url_for('login'))
        
        try:
            app_manager.ajouter_participant(pseudo, session_id)
            # Stocker la session et rediriger vers la salle de vote
            session['session_id'] = session_id
            session.modified = True

            reponse = redirect(url_for('salle_de_vote'))
            reponse.set_cookie('session_id', session_id)
            return reponse
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

# Route de déconnexion
@app.route('/logout')
def logout():
    """
    @brief Déconnecte un utilisateur.

    @return Redirection vers la page de connexion.
    """
    session_id = request.cookies.get('session_id')

    if session_id:
        # Supprimer l'utilisateur de state["participants"] basé sur session_id
        app_manager.logout_participant(session_id)

    # Effacer la session Flask
    session.clear()
    
    # Rediriger vers la page de connexion
    return redirect(url_for('login'))

# Route pour la salle de vote
@app.route('/salle_de_vote')
def salle_de_vote():
    """
    @brief Affiche la salle de vote pour les participants connectés.

    @details Cette route vérifie si un utilisateur est authentifié.
    Si l'utilisateur n'est pas connecté ou la session est invalide, il est redirigé.

    @return La page HTML de la salle de vote.
    """
    print("Session actuelle :", session)
    if 'session_id' not in session:
        flash("Vous devez être connecté pour accéder à cette page.", "danger")
        return redirect(url_for('login'))

    # Vérifier si le participant existe dans les données d'AppManager
    participant = next((p for p in app_manager.state["participants"] if p["session_id"] == session['session_id']), None)
    if not participant:
        flash("Session invalide ou expirée.", "danger")
        return redirect(url_for('login'))

    fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
    if not fonctionnalite_prioritaire:
        flash("Aucune fonctionnalité prioritaire.", "warning")
        return redirect(url_for('backlog'))
    
    # Vérifier si l'équipe est complète
    equipe_complete = app_manager.is_team_complete(fonctionnalite_prioritaire)
    
    # Récupérer les participants connectés
    participants = app_manager.state["participants"]
 
    # Récupérer le pseudo actif
    pseudo_actif = session.get('pseudo_actif', None)

    vote_commence = app_manager.state["indicateurs"]["vote_commence"] 
    
    return render_template(
        'salle_de_vote.html',
        participants=participants,
        cartes=CARTES_VOTE,
        fonctionnalite=fonctionnalite_prioritaire,
        equipe_complete=equipe_complete,
        pseudo_actif=pseudo_actif,
        vote_commence=vote_commence
    )

# activation si on clique sur l'avatar
@app.route('/set_pseudo_actif', methods=['POST'])
def set_pseudo_actif():
    """
    @brief Définit le participant actif basé sur le pseudo sélectionné.

    @details Cette route est appelée lorsqu'un utilisateur 
    clique sur l'avatar d'un participant.Elle met à jour le 
    pseudo actif dans la session Flask.

    @return Redirection vers la salle de vote.
    """
    pseudo = request.form.get("pseudo")  # Obtenu depuis le clic sur l'avatar
    if not pseudo:
        flash("Aucun pseudo sélectionné.", "danger")
        return redirect(url_for('salle_de_vote'))

    # Vérifier que le pseudo existe dans `state`
    participant = next((p for p in app_manager.state["participants"] if p["pseudo"] == pseudo), None)
  
    if not participant:
        flash(f"Le participant '{pseudo}' n'existe pas.", "danger")
        return redirect(url_for('salle_de_vote'))

    # Stocker le pseudo actif dans la session
    session['pseudo_actif'] = pseudo
    session.modified = True
    flash(f"{pseudo} est maintenant actif.", "success")
    return redirect(url_for('salle_de_vote'))



@app.route('/afficher_ajout_fonctionnalite')
def afficher_ajout_fonctionnalite():
    """
    @brief Affiche la page pour ajouter une nouvelle fonctionnalité.

    @details Accessible uniquement pour le Product Owner.
    Si aucun participant actif n'est sélectionné ou si le 
    participant actif n'est pas un Product Owner, un message 
    d'erreur est affiché et l'utilisateur est redirigé.

    @return La page HTML pour ajouter une fonctionnalité ou une redirection vers la salle de vote.
    """
    pseudo_actif = session.get('pseudo_actif')
    if not pseudo_actif:
        flash("Aucun participant actif sélectionné.", "danger")
        return redirect(url_for('salle_de_vote'))
    

    participant_actif = next((p for p in app_manager.state["participants"] if p["pseudo"] == pseudo_actif), None)
    
    if not participant_actif or participant_actif["fonction"] != "Product Owner":
        flash("Accès réservé au Product Owner.", "danger")
        return redirect(url_for('salle_de_vote'))

    # Récupérer les données temporaires depuis la session
    participants_temp = session.get('participants_temp', [])  # Récupérer les participants temporaires ou liste vide
    form_data = session.get('form_data', {})

    return render_template(
        'ajout_fonctionnalite.html',
        form_data=form_data,
        participants_temp=participants_temp
    )



@app.route('/ajouter_fonctionnalite', methods=['POST'])
def ajouter_fonctionnalite():
    """
    @brief Ajoute une nouvelle fonctionnalité au backlog.

    @details Valide les données soumises via le formulaire d'ajout de fonctionnalité.
    Si les données sont valides, la fonctionnalité est ajoutée via AppManager.
    Sinon, des erreurs sont affichées et l'utilisateur reste sur la page d'ajout.

    @return Redirection vers le backlog ou la page d'ajout en cas d'erreur.
    """
    erreurs = {}
    pseudo_actif = session.get('pseudo_actif')
    if not pseudo_actif or pseudo_actif.lower() != "po":
        flash("Acces reserve au Product Owner", "danger")
        return redirect(url_for('salle_de_vote'))
    try:
        nom = request.form.get('nom', '').strip()
        description = request.form.get('description', '').strip()
        priorite = request.form.get('priorite', '').strip()
        difficulte = request.form.get('difficulte', '').strip()
        mode_de_vote = request.form.get('mode_de_vote', 'unanimite').strip()
        statut = request.form.get('statut', 'A faire').strip()
        participants = session.get('participants_temp', [])

        # Valider les données
        if not priorite.isdigit() or not (PRIORITE_MIN <= int(priorite) <= PRIORITE_MAX):
            erreurs['priorite'] = f"La priorité doit être comprise entre {PRIORITE_MIN} et {PRIORITE_MAX}."
        if not difficulte.isdigit() or not (DIFFICULTE_MIN <= int(difficulte) <= DIFFICULTE_MAX):
            erreurs['difficulte'] = f"La difficulté doit être comprise entre {DIFFICULTE_MIN} et {DIFFICULTE_MAX}."

        if erreurs:
            return render_template('ajout_fonctionnalite.html', errors=erreurs, form_data=request.form)

        print(f"nom {nom} description {description} int(priorite) {int(priorite)} int(difficulte) {int(difficulte)} mode_de_vote {mode_de_vote} statut {statut} participants {participants} ")
        
        # Ajouter la fonctionnalité via AppManager
        app_manager.ajout_fonctionnalite(nom, description, int(priorite), int(difficulte),statut, mode_de_vote,  participants)

        # Nettoyer les données temporaires
        session.pop('participants_temp', None)
        session.pop('form_data', None)

        flash("La fonctionnalité a été ajoutée avec succès.", "success")
        return redirect(url_for('backlog'))
    
    except Exception as e:
        flash("Une erreur est survenue lors de l'ajout de la fonctionnalité.", "danger")
        return redirect(url_for('afficher_ajout_fonctionnalite'))

@app.route('/ajouter_participant_route', methods=['POST'])
def ajouter_participant_route():
    """
    @brief Ajoute un participant temporaire à une fonctionnalité.

    @details Cette route permet d'ajouter un participant temporaire via le formulaire 
    d'ajout de fonctionnalité. Les données temporaires sont stockées dans la session.

    @return Redirection vers la page d'ajout de fonctionnalité.
    """
    pseudo = request.form.get('participant_pseudo', '').strip()
    print("participant ajouté dans fonctionnalité :", pseudo)

    # Initialiser la liste si elle n'existe pas
    if 'participants_temp' not in session:
        session['participants_temp'] = []
    
    if pseudo and pseudo not in session['participants_temp']:
        session['participants_temp'].append(pseudo)
        session.modified = True  # Marquer la session comme modifiée
        flash(f"Participant '{pseudo}' ajouté avec succès.", "success")
    else:
        flash("Le participant existe déjà ou aucun pseudo n'a été saisi.", "warning")
    
    # Conserver les autres données du formulaire
    session['form_data'] = {
        "nom": request.form.get('nom', '').strip(),
        "description": request.form.get('description', '').strip(),
        "priorite": request.form.get('priorite', '').strip(),
        "difficulte": request.form.get('difficulte', '').strip()
    }
    return redirect(url_for('afficher_ajout_fonctionnalite'))

@app.route('/edit_fonctionnalite_route/<int:fonctionnalite_id>', methods=['GET', 'POST'])
def edit_fonctionnalite_route(fonctionnalite_id):
    """
    @brief Modifie une fonctionnalité existante.

    @details Cette route affiche la page d'édition d'une fonctionnalité
    ou applique les modifications soumises via le formulaire.

    @param fonctionnalite_id L'identifiant de la fonctionnalité à modifier.

    @return Redirection vers le backlog ou la page d'édition.
    """
    # Récupérer la fonctionnalité à modifier via AppManager
    fonctionnalite = app_manager.get_fonctionnalite(fonctionnalite_id)
    if not fonctionnalite:
        flash("Fonctionnalité non trouvée.", "danger")
        return redirect(url_for('backlog'))
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            updated_data = {
                'nom': request.form['nom'].strip(),
                'description': request.form['description'].strip(),
                'priorite': request.form['priorite'].strip(),
                'difficulte': request.form['difficulte'].strip(),
                'mode_de_vote': request.form.get('mode_de_vote', fonctionnalite.mode_de_vote).strip(),
                'statut': request.form.get('statut', fonctionnalite.statut).strip(),
                'participants': request.form.getlist('participants[]')  # Liste des participants
            }

            # Déléguer la mise à jour à AppManager
            app_manager.modifier_fonctionnalite(fonctionnalite_id, **updated_data)

            flash("La fonctionnalité a été mise à jour avec succès.", "success")
            return redirect(url_for('backlog'))

        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash("Une erreur est survenue lors de la mise à jour de la fonctionnalité.", "danger")
            print(f"Erreur dans edit_fonctionnalite : {e}")

    # Charger la page avec les données actuelles de la fonctionnalité
    return render_template('edit_fonctionnalite.html', fonctionnalite=fonctionnalite)

@app.route('/supprimer_fonctionnalite_route/<int:fonctionnalite_id>', methods=['GET','POST'])
def supprimer_fonctionnalite_route(fonctionnalite_id):
    """
    @brief Supprime une fonctionnalité existante.

    @details Cette route permet de supprimer une fonctionnalité du backlog 
    en fonction de son identifiant.

    @param fonctionnalite_id L'identifiant de la fonctionnalité à supprimer.

    @return Redirection vers le backlog après suppression.
    """

    try:
        # Déléguer la suppression à AppManager
        app_manager.supprimer_fonctionnalite(fonctionnalite_id)
        flash("La fonctionnalité a été supprimée avec succès.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash("Une erreur est survenue lors de la suppression de la fonctionnalité.", "danger")
        print(f"Erreur dans supprimer_fonctionnalite : {e}")

    # Redirection vers le backlog
    return redirect(url_for('backlog'))

@app.route('/soumettre_vote', methods=['POST'])
def soumettre_vote():
    """Permet aux participants de soumettre leur vote."""
    pseudo_actif = session.get('pseudo_actif').strip()
    print("pseudo actif dans acces sm ",pseudo_actif )
    if not pseudo_actif:
        flash("Aucun participant actif sélectionné.", "danger")
        return redirect(url_for('salle_de_vote'))
    
    if not app_manager.state["indicateurs"]["vote_commence"] :
        flash("Le vote n'a pas encore commencé. Attendez l'invitation du Scrum Master.", "warning")
        return redirect(url_for('salle_de_vote'))
    
    pseudo = request.form.get("pseudo")
    vote = request.form.get("vote")
    #session_id = session[pseudo]
    
    # Vérifier si le pseudo et le vote sont valides
    if not pseudo or not vote:
        flash("Pseudo ou vote manquant.", "danger")
        return redirect(url_for('salle_de_vote'))
    
    try:
        app_manager.ajouter_vote(pseudo, vote)
        flash(f"Vote de {pseudo} enregistré : {vote}", "success")
    except ValueError as e:
        flash(str(e), "danger")
    
    # Réinitialiser le pseudo actif pour forcer une nouvelle sélection
    session.pop('pseudo_actif', None)
    
    return redirect(url_for('salle_de_vote'))

@app.route('/acces_sm')
def acces_sm():
    """Accès pour le Scrum Master à la gestion des votes."""
    # Vérifier le pseudo actif dans la session
    pseudo_actif = session.get('pseudo_actif')
    print("pseudo actif dans acces sm ",pseudo_actif )
    if not pseudo_actif:
        flash("Aucun participant actif sélectionné.", "danger")
        return redirect(url_for('salle_de_vote'))

    # Récupérer le participant actif
    participant_actif = next((p for p in app_manager.state["participants"] if p["pseudo"] == pseudo_actif), None)
    print("participant actif dans acces sm ", participant_actif)
    
    if pseudo_actif  != "sm":
        flash("Accès réservé au Scrum Master.", "danger")
        return redirect(url_for('salle_de_vote'))

    # Récupérer la fonctionnalité prioritaire
    fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
    if not fonctionnalite_prioritaire:
        flash("Aucune fonctionnalité prioritaire n'est disponible.", "warning")
        return redirect(url_for('backlog'))

    # Récupérer les participants attendus
    participants_attendus = app_manager.participants_backlog(fonctionnalite_prioritaire.id)

    # Récupérer les participants connectés
    participants_connectes = [
        participant["pseudo"]
        for participant in app_manager.state["participants"]
        if participant["fonction"] == "Votant"
    ]

    # Calculer les participants manquants
    difference = set(participants_attendus) - set(participants_connectes)
    bouton_actif = len(difference) == 0  # Activer le bouton si tous les participants sont connectés

    # Vérifier si tout le monde a voté
    tout_le_monde_a_vote = app_manager.tout_le_monde_a_vote()
    votes_reveles = app_manager.state["indicateurs"]["votes_reveles"]
    if votes_reveles:
        votes = app_manager.reveler_votes()
    else:
        votes = {}

    return render_template(
        'acces_sm.html',
        fonctionnalite=fonctionnalite_prioritaire,
        votes=votes,
        pseudo_actif=pseudo_actif,
        participant_actif=participant_actif,
        participants_attendus=participants_attendus,
        participants_connectes=participants_connectes,
        difference=list(difference),
        bouton_actif=bouton_actif,
        tout_le_monde_a_vote=tout_le_monde_a_vote,
        votes_reveles=votes_reveles
        
    )

@app.route('/faciliter_discussion', methods=['POST'])
def faciliter_discussion():
    """Permet au Scrum Master de faciliter une discussion."""
    pseudo_actif = session.get('pseudo_actif').strip()
    print("pseudo actif dans acces sm ",pseudo_actif )
    if not pseudo_actif:
        flash("Aucun participant actif sélectionné.", "danger")
        return redirect(url_for('salle_de_vote'))

    if pseudo_actif != 'sm':
        flash(ACCES_RESERVE_SM, "danger")
        return redirect(url_for('acces_sm'))


    # Vérification d'une fonctionnalité prioritaire
    fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
    if not fonctionnalite_prioritaire:
        flash("Aucune fonctionnalité prioritaire disponible pour initier la discussion.", "danger")
        return redirect(url_for('acces_sm'))

    # Marquer la discussion comme active dans l'indicateur global
    app_manager.state["indicateurs"]["discussion_active"] = True
    flash("Discussion initiée avec succès. Invitez les participants à échanger.", "info")
    return redirect(url_for('acces_sm'))

@app.route('/valider_vote', methods=['POST'])
def valider_vote():
    """Valide les votes pour la fonctionnalité prioritaire."""
    pseudo_actif = session.get('pseudo_actif').strip()
    print("pseudo actif dans acces sm ",pseudo_actif )
    if not pseudo_actif:
        flash("Aucun participant actif sélectionné.", "danger")
        return redirect(url_for('salle_de_vote'))

    if pseudo_actif != 'sm':
        flash(ACCES_RESERVE_SM, "danger")
        return redirect(url_for('acces_sm'))


    # Récupérer les votes pour la fonctionnalité en cours
    """ votes = app_manager.state.get("votes", {}).get(fonctionnalite_prioritaire.id, {})
    if not votes:
        flash("Aucun vote à valider pour la fonctionnalité prioritaire.", "danger")
        return redirect(url_for('acces_sm')) """

    # Valider les votes via AppManager
    vote_valide = app_manager.valider_vote()
    if vote_valide:
        flash("Vote validé avec succès. La fonctionnalité est adoptée.", "success")
        
    else:
        flash("Vote non approuvé. Les critères n'ont pas été remplis.", "warning")

    return redirect(url_for('acces_sm'))


@app.route('/reveler_votes', methods=['POST'])
def reveler_votes():
    """Révèle les votes pour la fonctionnalité prioritaire."""
    pseudo_actif = session.get('pseudo_actif').strip()
    print("pseudo actif dans acces sm ",pseudo_actif )
    if not pseudo_actif:
        flash("Aucun participant actif sélectionné.", "danger")
        return redirect(url_for('salle_de_vote'))

    if pseudo_actif != 'sm':
        flash(ACCES_RESERVE_SM, "danger")
        return redirect(url_for('acces_sm'))

    fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
    if not fonctionnalite_prioritaire:
        flash("Aucune fonctionnalité prioritaire trouvée pour révéler les votes.", "danger")
        return redirect(url_for('acces_sm'))

    # Récupérer les votes pour la fonctionnalité en cours
    """  votes = app_manager.state.get("votes", {}).get(fonctionnalite_prioritaire.id, {})
    if not votes:
        flash("Aucun vote à révéler pour la fonctionnalité prioritaire.", "warning")
        return redirect(url_for('acces_sm')) """

    # Révéler les votes via AppManager
    votes_reveles = app_manager.reveler_votes()
    if votes_reveles:
        flash("Votes révélés avec succès.", "success")
    else:
        flash("Problème lors de la révélation des votes.", "danger")

    return redirect(url_for('acces_sm'))

@app.route('/initier_vote', methods=['POST'])
def initier_vote():
    """Démarre le vote pour la fonctionnalité prioritaire."""
    pseudo_actif = session.get('pseudo_actif').strip()
    print("pseudo actif dans acces sm ",pseudo_actif )
    if not pseudo_actif:
        flash("Aucun participant actif sélectionné.", "danger")
        return redirect(url_for('salle_de_vote'))

    # Vérification d'une fonctionnalité prioritaire
    fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
    if not fonctionnalite_prioritaire:
        flash("Aucune fonctionnalité prioritaire trouvée pour initier le vote.", "danger")
        return redirect(url_for('acces_sm'))

    # Vérification de l'équipe complète
    if not app_manager.is_team_complete(fonctionnalite_prioritaire):
        flash("Tous les participants nécessaires ne sont pas encore connectés.", "warning")
        return redirect(url_for('acces_sm'))

    # Initialisation du vote via AppManager
    try:
        app_manager.initier_vote(fonctionnalite_prioritaire.id)
        app_manager.state["indicateurs"]["vote_commence"] = True
        flash("Le vote a été initié avec succès.", "success")
    except Exception as e:
        flash(f"Erreur lors de l'initiation du vote : {e}", "danger")

    return redirect(url_for('acces_sm'))

@app.route('/reinitialiser_vote', methods=['POST'])
def reinitialiser_vote():   

    # Vérification d'une fonctionnalité prioritaire
    fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
    if not fonctionnalite_prioritaire:
        flash("Aucune fonctionnalité prioritaire trouvée pour réinitialiser les votes.", "danger")
        return redirect(url_for('acces_sm'))

    # Réinitialisation des votes via AppManager
    try:
        app_manager.reinitialiser_votes()
        flash("Les votes ont été réinitialisés avec succès.", "info")
    except Exception as e:
        flash(f"Erreur lors de la réinitialisation des votes : {e}", "danger")

    return redirect(url_for('acces_sm'))


@app.route('/backlog')
def backlog():
    """
    @brief Affiche le backlog des fonctionnalités.

    @details Cette route retourne une vue contenant 
    toutes les fonctionnalités du backlog.

    @return La page HTML du backlog.
    """
    backlog = app_manager.lister_backlog()
    return render_template('backlog.html', backlog=backlog)

# Démarrer l'application Flask (le serveur en mode debbugage)
if __name__ == '__main__':
    app.run(debug=True)