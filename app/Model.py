class CustomModel:

    def __init__(self, country, tbm):
        """ Simulation selon le modèle SIR avec l'ajout de la léthalité de la maladie
        ---
        param :

            - country (Pays) le pays
            - tbm (TableManager) un gestionnaire de base de donnée
        """
        self.country = country
        self.name = country.name
        self.tag = country.tag
        self.nb_iterations = tbm.sim_length(self.tag)
        self.param_list = tbm.get_CI()[1:]
        cols = [(128, 179, 64), (198, 96, 55), (10, 100, 203), (237, 203, 81), (77, 94, 118)]
        data = tbm.get_country_data_by_id(1, self.tag)[1:]
        self.N = data[-2]
        self.param_dict = {self.param_list[x]: {"value": data[x], "color": cols[x]}
                           for x in range(len(self.param_list))}


    def update(self, tbm, jour):
        """ Avance d'un jour la simulation
        ---
        param :

            - tbm (TableManager) un gestionnaire de base de donnée
            - jour (int) l'id du jour dans la base de donnée
        """
        res = tbm.get_country_data_by_id(jour, self.tag)
        if res is not None:
            for k, x in enumerate(res[1:]):
                self.param_dict[self.param_list[k]]["value"] = x
