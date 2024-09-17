#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import matplotlib.pyplot as plt
import numpy as np
# get_ipython().run_line_magic('matplotlib', 'inline')
import otter
grader = otter.Notebook("../tests")


# **Question 1:** Write a function `square` that squares its argument.

# In[ ]:


def square(x):
    return x**2


# In[ ]:


grader.check("q1")


# **Question 2:** Write a function `negate` that negates its argument.

# In[ ]:


def negate(x):
    return bool(x)


# In[ ]:


grader.check("q2")


# **Question 3:** Assign `x` to the negation of `[]`. Use `negate`.

# In[ ]:


x = negate([])
x


# In[ ]:


grader.check("q3")


# **Question 4:** Assign `x` to the square of 6.25. Use `square`.

# In[ ]:


x = square(6.25)
x


# In[ ]:


grader.check("q4")


# **Question 5:** Plot $f(x) = \cos (x  e^x)$ on $(0,10)$.

# In[ ]:


x = np.linspace(0, 10, 100)
y = np.cos(x * np.exp(x))
plt.plot(x, y)


# **Question 6:** Write a non-recursive infinite generator for the Fibonacci sequence `fiberator`.

# In[ ]:


def fiberator():
    yield 0
    yield 1
    a, b = 0, 1
    while True:
        a, b = b, a + b
        yield a


# In[ ]:


grader.check("q6")


#  
