from affichage import afficher_sim

class SIR:


    def __init__(self, N, N0, t, tp, nb_iterations):
        """ Simulation selon le modèle S / I / R
        ---
        param :

            - N (int) le nombre de personne dans la simulation
            - N0 (int) le nombre de personne infectées au début de la simulation
            - t (float) la transmissibilité de la maladie
            - tp (int) le nombre de jour de maladie une fois infecté
            - nb_iterations (int) le nombre de jour de la simulation

        """
        self.N = N
        self.S = (N - N0) / N
        self.I = N0 / N
        self.R = 0
        self.transmission = t
        self.temps_maladie = tp
        self.nb_iterations = nb_iterations
        self.i = []
        self.r = []
        self.s = []


    def update(self):
        """ Avance d'un jour la simulation
        ---
        """
        dS = -self.transmission * self.I * self.S
        dI = (self.transmission * self.S - 1 / self.temps_maladie) * self.I
        dR = 1 / self.temps_maladie * self.I
        self.S += dS
        self.I += dI
        self.R += dR


    def simuler(self):
        """ Lance la simulation complète
        """
        for x in range(self.nb_iterations):
            self.update()
            self.s.append(self.S)
            self.i.append(self.I)
            self.r.append(self.R)


    def format_sim(self):
        """ Formmatte les données de la simulation pour l'affichage
        """
        return {'Sains': self.s, "Infectés": self.i, "Morts": self.r}

