# constants.py


# Clé secrète pour Flask
CLE_SECRETE = "dev_mdp_123" 
NOM_SERVEUR = '127.0.0.1:5000'

# Autres configurations
DEBUG = True
TESTING = False

# Rôles des utilisateurs
PO = 'PO'  # Product Owner
SM = 'SM'  # Scrum Master
PARTICIPANTS_AUTORISES = ["PO", "SM", "lina", "hugo"]
VOTANT = 'VOTANT'  # Votant régulier

# Modes de vote
VOTE_UNANIMITE = 'unanimite'  # Unanimité
VOTE_MOYENNE = 'moyenne'  # Moyenne des votes

# Statuts des fonctionnalités
STATUT_A_FAIRE = 'A faire'
STATUT_EN_COURS = 'En cours'
STATUT_TERMINE = 'Terminé'

# Messages Flash
FLASH_LOGIN_REQUIS = "Vous devez être connecté pour accéder à cette page."
FLASH_ACCES_REFUSE = "Accès refusé."
FLASH_SESSION_INVALIDE = "Session invalide. Veuillez vous reconnecter."
FLASH_VOTE_AVEC_SUCCESS = "Votre vote a été soumis avec succès."
FLASH_VOTE_DEJA_SOUMIS = "Vous avez déjà voté pour cette fonctionnalité."
FLASH_AUCUN_VOTE_SOUMIS = "Aucun vote n'a encore été soumis."
FLASH_TOUS_PARTICIPANTS_ONT_VOTES = "Tous les participants ont voté."
FLASH_PAGE_RESERVEE_SM = "Cette page est réservée au Scrum Master."
ACCES_RESERVE_SM = "Accès réservé au Scrum Master."
VOTES_INITIALISES = "Les votes ont été réinitialisés."
DISCUSSION_INITIEE = "La discussion a été initiée pour résoudre les divergences."
AUCUN_VOTE_A_VALIDER = "Aucun vote à valider."
AUCUNE_FONCTIONNALITE_TROUVEE = "Aucune fonctionnalité prioritaire n'a été trouvée."
FONCTIONNALITE_AJOUTEE = "La fonctionnalité a été ajoutée et triée avec succès."
ERREUR_DONNEES_FORMULAIRE = "Erreur dans les données du formulaire."
MISE_A_JOUR_FONCTIONNALITE = "Fonctionnalité mise à jour et triée avec succès."
FONCTIONNALITE_SUPPRIMEE = "Fonctionnalité supprimée avec succès."
FLASH_VOTES_REVELES = "le vote est révélé"


# Cartes de vote
CARTES_VOTE = ["1", "2", "3", "5", "8", "13", "20", "40", "80", "100", "?", "café"]



# Limites diverses
PRIORITE_MIN = 1
PRIORITE_MAX = 10
DIFFICULTE_MIN = 1
DIFFICULTE_MAX = 100
