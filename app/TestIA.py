import numpy as np

def relu(x):
    return max(x, 0)

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def sigmoid_der(x):
    return x * (1 - x)


class Layer:

    def __init__(self, layer_dim, lr, n):
        self.num = n
        self.nb_inputs, self.nb_neurons = layer_dim[0], layer_dim[1]
        self.weights = np.random.randn(self.nb_inputs, self.nb_neurons)
        self.bias = np.array([0 for _  in range(self.nb_neurons)], dtype='float64')
        self.parent = None
        self.child = None
        self.input = None
        self.activations = None
        self.lr = lr
        if len(layer_dim) > 2:
            self.child = Layer(layer_dim[1:], self.lr, n + 1)
            self.child.parent = self


    def feedforward(self, input):
        self.input = np.array(input, dtype="float64")
        self.activations = (np.dot(input, self.weights) + self.bias).astype("float64")
        if not self.child:
            return sigmoid(self.activations)
        return self.child.feedforward(self.activations)


    def backpropagation(self, E):
        T = self.weights.dot(E)
        E = np.multiply(T, sigmoid_der(self.activations))
        self.weights -= self.lr * E.T.dot(self.input)
        self.bias -= self.lr * E
        if self.parent:
            self.parent.backpropagation(E)


    def __str__(self):
        s = f"Layer n° {self.num}\npoids :\n{self.weights}\nbiais :\n{self.bias}"
        if self.child:
            s += "\n\n" + self.child.__str__()
        return s


class NeuralNetwork:

    def __init__(self, layer_dim, lr):
        self.lr = lr
        self.nn = Layer(layer_dim, self.lr, 0)


    def train(self, x, y):
        o = self.predict(x)
        d_err = (o - y)
        self.nn.backpropagation(d_err)


    def predict(self, x):
        return self.nn.feedforward(x)


    def __str__(self):
        return self.nn.__str__()


NN = NeuralNetwork([1, 1], 1e-3)
print(NN.predict([1]))
for _ in range(10000):
    NN.train([1], [1])
print(NN.predict([1]))

# https://dustinstansbury.github.io/theclevermachine/derivation-backpropagation

