
import numpy as np
import pandas as pd
import bisect
import sys


def find_left(a, x):
    'Find rightmost value less than or equal to x'
    loc = bisect.bisect_right(a, x)
    if loc:
        return a[loc-1]
    # If index is in first position, return -1 to force initial
    # value of drawdowns to be selected as the left limit.
    elif loc == 0:
        return -1
    # At this point, if we are still here, then we need to return the
    # next to last index location because we are at the end of the list.
    else:
        return len(a)-1


def find_right(a, x):
    'Find leftmost value greater than x'
    loc = bisect.bisect_left(a, x)
    if loc != len(a):
        return a[loc]
    else:
        return a[0]


def find_drawdown(i, down_vals, up_vals):
    thresholds = np.where(down_vals > down_vals[i])[0]
    if len(thresholds) > 0:
        left_val = up_vals[find_left(thresholds, i)+1]
        right_val = up_vals[find_right(thresholds, i)]
    else:
        left_val = up_vals[0]
        right_val = up_vals[-1]
    if right_val > left_val:
        return down_vals[i] - right_val
    else:
        return down_vals[i] - left_val


def find_drawdowns(data):
    # Insert a leading non-zero value to force a up_val at the start of the
    # data record.
    if data[0] != 9.99:
        data = np.insert(data, 0, 9.99)
    # First derivative of the data:
    slope = np.diff(data)
    # 2nd derivative of the data:
    rev = np.diff((slope > 0).astype(int))
    # rev = np.diff(slope)
    down_locs,  = np.where(rev < 0)
    up_locs,  = np.where(rev > 0)
    up_vals = data[up_locs + 1]
    down_vals = data[down_locs + 1]
    print("There are {n} total downvals".format(n=len(down_vals)))
    print("There are {n} total upvals".format(n=len(up_vals)))
    n = min(len(down_vals), len(up_vals))
    drawdowns = np.array([find_drawdown(i, down_vals, up_vals)
                          for i in np.arange(0, n-1)])
    # Remove zero values of drawdowns.
    drawdowns = drawdowns[drawdowns > 0]
    return drawdowns


if __name__ == "__main__":
    file = sys.argv[1]
    data = np.array(pd.read_csv(file)).T.squeeze()
    drawdowns = find_drawdowns(data)
    # print(drawdowns)
