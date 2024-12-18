# Fonctionnalite.py
import statistics
from constantes import *

# models/fonctionnalite.py
class Fonctionnalite:
    """
    @class Fonctionnalite

    @brief Représente une fonctionnalité dans le backlog.
    
    @details
    Une fonctionnalité contient des informations telles que son identifiant, 
    son nom, sa description, sa priorité, sa difficulté, son statut, le mode 
    de vote, ainsi que la liste des participants associés.
    
    @param id Identifiant unique de la fonctionnalité.
    @param nom Nom de la fonctionnalité.
    @param description Description détaillée de la fonctionnalité.
    @param priorite Priorité de la fonctionnalité.
    @param difficulte Niveau de difficulté (faible, moyenne, élevée).
    @param statut Statut de la fonctionnalité (valeur par défaut : STATUT_A_FAIRE, en cours, terminé, etc.).
    @param mode_de_vote Mode de vote pour valider la fonctionnalité (valeur par défaut : VOTE_UNANIMITE, moyenne).
    @param participants Liste des participants associés à la fonctionnalité.
    """
    def __init__(
        self, 
        id, 
        nom, 
        description, 
        priorite, 
        difficulte=None, 
        statut=STATUT_A_FAIRE, 
        mode_de_vote=VOTE_UNANIMITE, 
        participants=[]):
        """
        @brief Initialise une nouvelle instance de la classe Fonctionnalite.
        Les paramètres passés à cette méthode sont utilisés pour initialiser les attributs 
        décrits dans le docstring de la classe.
        """
        self.id = id
        self.nom = nom  # Nom de la fonctionnalité
        self.description = description  # Description détaillée
        self.priorite = priorite
        self.difficulte = difficulte # Difficulté (faible, moyenne, élevée)
        self.statut = statut  # En attente, termine, en cours, ...
        self.mode_de_vote = mode_de_vote # unanimite, moyenne, médiane...
        self.participants = participants or [] # liste des developpeurs
        
    # méthode pour convertir en dictionnaire
    def to_dict(self):
        """
        @brief Convertit l'objet Fonctionnalite en dictionnaire.
        
        @return Dictionnaire contenant les attributs de la fonctionnalité.
        """
        return {
            "id": self.id,
            "nom": self.nom,
            "description": self.description,
            "priorite": self.priorite,
            "difficulte": self.difficulte,
            "statut": self.statut,
            "mode_de_vote": self.mode_de_vote,
            "participants" : self.participants or [],
  
        }
        
    def __str__(self):
        """
        @brief Retourne une chaîne de caractères représentant la fonctionnalité.

        @return Chaîne de caractères formatée.
        """
        return f"Fonctionnalité: {self.nom}, priorité: {self.priorite}, Mode de vote: {self.mode_de_vote}"
    
    def __repr__(self):
        """
        @brief Retourne une représentation de l'objet pour le débogage.

        @return Chaîne de caractères contenant l'identifiant et le nom de la fonctionnalité.
        """
        return f"<Fonctionnalite id={self.id}, nom='{self.nom}', priorite={self.priorite}>"
