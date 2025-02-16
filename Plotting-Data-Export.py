import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# If using Google colab environment
from google.colab import files

# Extract the wavefunction from the solution:
final_solution_tensor = final_solution[0]

# Convert TensorFlow tensor to NumPy array
final_solution_np = final_solution_tensor.numpy()

# Choose a middle slice along the z-axis
mid_z = final_solution_np.shape[2] // 2
slice_2d = final_solution_np[:, :, mid_z]

# Save as a CSV file (matrix format)
csv_filename = "wavefunction_matrix.csv"
np.savetxt(csv_filename, slice_2d, delimiter=",")  # No index/headers, just the matrix

# Download the CSV file in Google Colab
files.download(csv_filename)

# Plot the 2D slice
plt.figure(figsize=(8, 6))
plt.imshow(slice_2d, extent=[xMin, xMax, yMin, yMax], origin='lower', cmap='afmhot')
plt.colorbar(label='Wavefunction Value')
plt.xlabel('X (Bohr)')
plt.ylabel('Y (Bohr)')
plt.title('Mid-Z slice of the wavefunction solution')
plt.savefig("Wavefunction-Solution.png", dpi=600, bbox_inches='tight')
plt.show()

print(f"CSV file saved as {csv_filename}")
