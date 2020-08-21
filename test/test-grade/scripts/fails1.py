#!/usr/bin/env python
# coding: utf-8

# In[1]:


import matplotlib.pyplot as plt
import numpy as np
# get_ipython().run_line_magic('matplotlib', 'inline')
import otter
grader = otter.Notebook("../tests")


# **Question 1:** Write a function `square` that squares its argument.

# In[2]:


def square(x):
    return x**3


# In[3]:


grader.check("q1")


# **Question 2:** Write a function `negate` that negates its argument.

# In[4]:


def negate(x):
    return not x


# In[5]:


grader.check("q2")


# **Question 3:** Assign `x` to the negation of `[]`. Use `negate`.

# In[6]:


x = negate([])
x


# In[7]:


grader.check("q3")


# **Question 4:** Assign `x` to the square of 6.25. Use `square`.

# In[13]:


x = 6.25**2
x


# In[14]:


grader.check("q4")


# **Question 5:** Plot $f(x) = \cos (x  e^x)$ on $(0,10)$.

# In[10]:


x = np.linspace(0, 10, 100)
y = np.cos(x * np.exp(x))
plt.plot(x, y)


# **Question 6:** Write a non-recursive infinite generator for the Fibonacci sequence `fiberator`.

# In[11]:


def fiberator():
    yield 0
    yield 1
    a, b = 0, 1
    while True:
        a, b = b, a + b
        yield b


# In[12]:


grader.check("q6")


#  
