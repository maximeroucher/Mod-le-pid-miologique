import numpy as np

def relu(x):
    return max(x, 0)

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def sigmoid_der(x):
    return x / (1 + x)


class Layer:

    def __init__(self, nb_inputs, nb_neurons, lr):
        self.weights = np.random.randn(nb_inputs, nb_neurons)
        self.bias = np.zeros((1, nb_neurons))
        self.input = []
        self.parent = []
        self.child = []
        self.activations = []
        self.lr = lr


    def feedforward(self, input):
        self.input = input
        self.activations = sigmoid(np.dot(input, self.weights) + self.bias)
        if len(self.child) == 0:
            return self.activations[0]
        self.child.feedforward(self.activations)


    def backpropagation(self, expected):
        if len(self.parent) != 0:
            d_err = calc_sq_err(self.activations, expected) * sigmoid_der(self.activations)
            der = np.dot(d_err, self.input)
            self.weights -= lr * der
            self.bias = [self.bias[i] - lr * i for i in der]
            self.parent.backpropagation(n_expected)


def calc_sq_err(output, target):
    return 0.5 * sum(np.power(target - output, 2))

