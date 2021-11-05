import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

signal = pd.read_csv("output.csv")

plt.figure()
n = len(signal.columns[5:])
print(n)

c = 1
for channel in signal.columns[5:]:

    plt.subplot(n, 1, c)
    plt.plot((signal[channel]))
    plt.title(channel)
    plt.grid()

    c += 1

plt.show()
