---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.4
  kernelspec:
    display_name: drawdowns
    language: python
    name: drawdowns
---

# Drawdown

```python
from Drawdown import Drawdown, cum_dist
#help(Drawdown)
```

```python
from Drawdown import Drawdown, cum_dist
file = 'calhounS.csv'
drawdown = Drawdown(filename=file, find_drawdowns=True, debug=False)
```

## Drawdown Plot

```python
drawdown.plot(
    threshold=1,
    show_up_locs=False,show_down_locs=False,
    offset=20)
```

```python
this = drawdown.find_drawdown(4)
print(this)
```

```python

import numpy as np
#idx_peak = this['peak_loc']
#print(idx_peak + np.min(np.where(drawdown.S[idx_peak:] <= this['end_val'])))
#drawdown.S[18:25]

len([10, 2, 3, 4])


```

## Drawdown Distribution

```python
from matplotlib import pyplot as plot
x, y = cum_dist(drawdown.df['magnitude'])
plot.plot(x,y)
plot.xlabel('Drawdown Size, d (cm)')
plot.ylabel('Cumulative Distribution, F(d)')
plot.title('CDF of Drawdown Sizes, F(d)')
```

## Drawdown Stats

```python
drawdown.df[['magnitude','duration','filling','draining']].describe()
```

```python
drawdown.S[30:]
```

```python
drawdown.S

```

```python

```
