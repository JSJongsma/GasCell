# GasCell
This is a model for gas absorption spectroscopy, using a multi-gass cell. The model tries to find mirror and hole configurations (i.e. positions, angles etc.) for which a certain amount of reflection/pathlength/intensity is found. The model has few dependencies (on NumPy, Matplotlib, etc.). The number of mirrors, holes (in the mirrors), and their dimensions are completely arbitrary, although the writer works with 3 mirrors with 2 holes (exit/entry).

The model simulates light rays entering a gas cell and reflecting on mirrors (flat, for simplicity, although in the future this may be expanded to concave mirrors). The light enters and leaves the gas cell via holes. 
The model includes optimization algorithms (see the Core file or the Jupyter notebook for the application), which try to find geometries (varying positions and rotations of the mirror and entry lightray) that meet the requirements of the user (i.e. the amount of reflections, hole positions inside the mirror, hole diameters, etc.). 

Furthermore, the model also keeps track of beam divergence due to beam propagation. As said earlier, the mirrors are modelled to be flat, for simplicity's sake, which leads to diverging beams. The final amount of intensity (after leaving the model) and the final beam width can be extracted. 
