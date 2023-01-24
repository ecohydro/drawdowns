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

Find the locations, magnitude, and duration of drawdown events in a time series of Plant Available Water Storage.


```python
from Drawdown import Drawdown, cum_dist
file = 'BoulderS.csv'
drawdown = Drawdown(filename=file, find_drawdowns=True, debug=False)
```

## Drawdown Plot

```python
drawdown.plot(
    threshold=100,
    show_up_locs=False,show_down_locs=False,
    offset=20)
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
