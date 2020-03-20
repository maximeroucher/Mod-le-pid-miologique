#from affichage import afficher_sim


class SIR:

    def __init__(self, N, N0, trans, tp, nb_iterations):
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
        self.transmission = trans
        self.temps_maladie = tp
        self.nb_iterations = nb_iterations
        self.pct_malade = 1 / self.temps_maladie
        self.i = []
        self.r = []
        self.s = []


    def update(self):
        """ Avance d'un jour la simulation
        ---
        """
        dS = -self.transmission * self.I * self.S
        dI = (self.transmission * self.S - self.pct_malade) * self.I
        dR = self.pct_malade * self.I
        self.S += dS
        self.I += dI
        self.R += dR


    def simuler(self):
        """ Lance la simulation complète
        """
        self.s.append(self.S)
        self.i.append(self.I)
        self.r.append(self.R)
        for x in range(self.nb_iterations):
            self.update()
            self.s.append(self.S)
            self.i.append(self.I)
            self.r.append(self.R)


    def format_sim(self):
        """ Formmatte les données de la simulation pour l'affichage
        """
        return {'Sains': self.s, "Infectés": self.i, "Morts / Guéris": self.r}


    def __str__(self):
        d = self.format_sim()
        a = "\n\t- ".join([f"{x} : {d[x]}" for x in list(d.keys())])
        return f"Population de {self.N} personnes.\nRésultat :\n\t- {a}"


class SIRM:

    def __init__(self, N, N0, transm, tp, l, nb_iterations):
        """ Simulation selon le modèle S / I / R avec l'ajout de la léthalité de la maladie
        ---
        param :

            - N (int) le nombre de personne dans la simulation
            - N0 (int) le nombre de personne infectées au début de la simulation
            - t (float, 0 <= t <= 1) la transmissibilité de la maladie
            - tp (int) le nombre de jour de maladie une fois infecté
            - l (float, 0 <= l <= 1) la léthalité de la maladie
            - nb_iterations (int) le nombre de jour de la simulation
        """
        self.N = N
        self.S = (N - N0) / N
        self.I = N0 / N
        self.R = 0
        self.M = 0
        self.transmission = transm
        self.lethalite = l
        self.temps_maladie = tp
        self.nb_iterations = nb_iterations
        self.pct_malade = 1 / self.temps_maladie
        self.i = []
        self.r = []
        self.s = []
        self.m = []


    def update(self):
        """ Avance d'un jour la simulation
        ---
        """
        dS = -self.transmission * self.I * self.S
        dI = (self.transmission * self.S - self.pct_malade) * self.I
        dR = self.pct_malade * self.I * (1 - self.lethalite)
        dM = self.pct_malade * self.I * self.lethalite
        self.S += dS
        self.I += dI
        self.R += dR
        self.M += dM


    def simuler(self):
        """ Lance la simulation complète
        """
        self.s.append(self.S)
        self.i.append(self.I)
        self.r.append(self.R)
        self.m.append(self.M)
        for x in range(self.nb_iterations):
            self.update()
            self.s.append(self.S)
            self.i.append(self.I)
            self.r.append(self.R)
            self.m.append(self.M)


    def format_sim(self):
        """ Formmatte les données de la simulation pour l'affichage
        """
        return {'Sains': self.s, "Infectés": self.i, "Réscapés": self.r, "Morts": self.m}


    def __str__(self):
        d = self.format_sim()
        a = "\n- " + "\n- ".join([f"{x} : {int(d[x][-1] * self.N)}" for x in list(d.keys())])
        return f"Population de {self.N} personnes.\nRésultat :{a}"

