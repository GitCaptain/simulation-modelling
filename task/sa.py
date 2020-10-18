from SALib.sample import saltelli
from SALib.analyze import sobol
import numpy as np
import random
import math


def Model(x1, x2, x3):
    return x1+x2+x3


def Evaluate(param_values):
    Y = []
    for params in param_values:
        x1, x2, x3 = params
        res = Model(x1, x2, x3)
        Y.append(res)
    return np.array(Y)
    
# Define the model inputs
problem = {
    'num_vars': 3,
    'names': ['x1', 'x2', 'x3'],
    'bounds': [[-1, 1],
               [-1, 1],
               [-1, 1]]
}

# Generate samples
param_values = saltelli.sample(problem, 1000)

# Run model (example)
Y = Evaluate(param_values)

# Perform analysis
Si = sobol.analyze(problem, Y, print_to_console=False)

# Print the first-order sensitivity indices
print("__________________")
print(Si['S1'])
