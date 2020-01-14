# this is a code cell
# with no plot in the output
# so it should be gone
import numpy as np
import matplotlib.pyplot as plt


# this cell should remain because it has a plot
x = np.linspace(0,10,1000)
y = np.cos(2*x) + np.exp(x)
plt.plot(x,y)

# this code cell should remain, since it has the "include" tag
y = 2*x
print(y[0:5])

# this plot should be excluded, since it's tagged as "ignore"
plt.plot(x,y**2)

def square(x):
	return x**2

def negate(cond):
	return not cond
