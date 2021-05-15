class Modele:

    def __init__(self, pays, gbdd):
        """ Simulation selon le modèle SIR avec l'ajout de la léthalité de la maladie
        ---
        paramètres :

            - pays (Pays) le pays
            - gbdd (GestionnaireBDD) un gestionnaire de base de donnée
        """
        self.pays = pays
        self.nom = pays.nom
        self.tag = pays.tag
        self.nb_iterations = gbdd.taille_donnees(self.tag)
        # On enlève le premier élément, id, généré par SQL
        self.liste_param = gbdd.liste_clee()[1:]
        # Les couleurs de chaque courbe du graphique
        couleurs = [(128, 179, 64), (198, 96, 55), (10, 100, 203), (237, 203, 81), (77, 94, 118)]
        # Les données du premier jour
        donnees = gbdd.donnees_depuis_id(1, self.tag)[1:]
        # La population
        self.N = donnees[-2]
        # Le dictionnaire des paramètres
        self.param_dict = {self.liste_param[x]: {"value": donnees[x], "color": couleurs[x]}
                           for x in range(len(self.liste_param))}
        self.date = []


    def mise_a_jour(self, gbdd, jour):
        """ Avance d'un jour la simulation
        ---
        paramètres :

            - gbdd (GestionnaireBDD) un gestionnaire de base de donnée
            - jour (int) l'id du jour dans la base de donnée
        """
        # On récupère les données du jour de la base de donnée
        res = gbdd.donnees_depuis_jour(jour, self.tag)
        # On ajoute le nombre à la liste du nombre de jour écoulé
        self.date.append(res[0])
        # On met à jour les valeurs
        for k, x in enumerate(res[1:]):
            self.param_dict[self.liste_param[k]]["value"] = x


    def jour_depuis_id(self, gbdd, id):
        """ Récupère le jour associé à l'id donné pour ce pays
        ---
        paramètres :

            - gbdd (GestionnaireBDD) le gestionnaire de base de donnée
            - id (int) l'id du jour

        résultat :

            - str
        """
        return gbdd.jour_depuis_id(id, self.tag)
