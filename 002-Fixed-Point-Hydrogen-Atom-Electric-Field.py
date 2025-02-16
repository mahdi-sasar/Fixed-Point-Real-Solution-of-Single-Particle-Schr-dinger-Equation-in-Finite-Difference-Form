import tensorflow as tf
import numpy as np

# Mesh Settings
xMin, xMax, NxGrid = 0.0, 10.0, 352
deltaX = (xMax - xMin) / (NxGrid - 1)

yMin, yMax, NyGrid = 0.0, 10.0, 352
deltaY = (yMax - yMin) / (NyGrid - 1)

zMin, zMax, NzGrid = 0.0, 10.0, 352
deltaZ = (zMax - zMin) / (NzGrid - 1)

X = tf.linspace(xMin, xMax, NxGrid)
Y = tf.linspace(yMin, yMax, NyGrid)
Z = tf.linspace(zMin, zMax, NzGrid)

# Create initial starting point:
# Create a random tensor
guess = tf.random.uniform((NxGrid, NyGrid, NzGrid))

# Set the last two layers in each dimension to zero and convert to NumPy for easier slicing
tensor = guess.numpy()  

tensor[-2:, :, :] = 0  # Last two layers along NxGrid
tensor[:, -2:, :] = 0  # Last two layers along NyGrid
tensor[:, :, -2:] = 0  # Last two layers along NzGrid

# Convert back to TensorFlow tensor
guess = tf.convert_to_tensor(tensor)

# Normalize input guess to better keep track of the computations and prevent overflow risk
normal = tf.norm(guess) ** 2 * deltaX * deltaY * deltaZ
guess = guess / tf.sqrt(normal)

# Function for distance measurement
def d(x, y, z):
    return tf.sqrt(x**2 + y**2 + z**2)

# Coulomb potential in atomic units plus a constant electric field in x direction
def elec_nuc(x, y, z):
  dist = d(x - 0.5 * (xMax + xMin), y - 0.5 * (yMax + yMin), z - 0.5 * (zMax + zMin))
  EField = -0.08*x
  return -2.0 / dist + EField

# Vectorized computation of the potential term V
X_mesh, Y_mesh, Z_mesh = tf.meshgrid(X[1:-1], Y[1:-1], Z[1:-1], indexing='ij')
V = elec_nuc(X_mesh, Y_mesh, Z_mesh)

# Fixed point map
def update_interior(P, V, deltaX, deltaY, deltaZ):
    NxGrid = tf.shape(P)[0]
    NyGrid = tf.shape(P)[1]
    NzGrid = tf.shape(P)[2]

    # Remove boundaries
    P = P[1:-1, 1:-1, 1:-1]

    # Shift operations
    P_shifted_up = tf.concat([tf.zeros((1, NyGrid-2, NzGrid-2)), P[:-1, :, :]], axis=0)
    P_shifted_down = tf.concat([P[1:, :, :], tf.zeros((1, NyGrid-2, NzGrid-2))], axis=0)
    P_shifted_left = tf.concat([tf.zeros((NxGrid-2, 1, NzGrid-2)), P[:, :-1, :]], axis=1)
    P_shifted_right = tf.concat([P[:, 1:, :], tf.zeros((NxGrid-2, 1, NzGrid-2))], axis=1)
    P_shifted_in = tf.concat([tf.zeros((NxGrid-2, NyGrid-2, 1)), P[:, :, :-1]], axis=2)
    P_shifted_out = tf.concat([P[:, :, 1:], tf.zeros((NxGrid-2, NyGrid-2, 1))], axis=2)

    # Compute energy
    sum2 = -tf.reduce_sum(((P_shifted_up + P_shifted_down + P_shifted_left + P_shifted_right + P_shifted_in + P_shifted_out - 6.0 * P) / (deltaX**2) - V * P) * P)
    energy = sum2 * deltaX * deltaY * deltaZ

    # Compute mapped P
    newP = (1.0 / 6.0) * (P_shifted_up + P_shifted_down + P_shifted_left + P_shifted_right + P_shifted_in + P_shifted_out + (energy * P - V * P) * deltaX**2)
    
    # Compute the helper function
    helper = tf.reduce_sum(((P_shifted_up + P_shifted_down + P_shifted_left + P_shifted_right + P_shifted_in + P_shifted_out - 6.0 * P) + (-V * P + energy * P)*deltaX**2)**2)
    
    # Restore boundaries
    newP = tf.concat([tf.zeros((1, NyGrid-2, NzGrid-2)), newP, tf.zeros((1, NyGrid-2, NzGrid-2))], axis=0)
    newP = tf.concat([tf.zeros((NxGrid, 1, NzGrid-2)), newP, tf.zeros((NxGrid, 1, NzGrid-2))], axis=1)
    newP = tf.concat([tf.zeros((NxGrid, NyGrid, 1)), newP, tf.zeros((NxGrid, NyGrid, 1))], axis=2)

    return newP, energy, helper

# Main solver
def solver(guess, tolerance):
    energy = tf.constant(0.0)
    tmp, tmp_energy, helper = update_interior(guess, V, deltaX, deltaY, deltaZ)

    while tf.abs(tmp_energy - energy) > tolerance:
        print(tf.abs(tmp_energy - energy).numpy(), '\t', energy.numpy(), '\t', helper.numpy())
        guess = tmp
        energy = tmp_energy
        tmp, tmp_energy, helper = update_interior(tmp, V, deltaX, deltaY, deltaZ)
    # Return normalized wavefunction:
    normal = tf.norm(tmp) ** 2 * deltaX * deltaY * deltaZ
    P = tmp / tf.sqrt(normal)
    return tmp, tmp_energy

final_solution = solver(guess, 1e-7)
