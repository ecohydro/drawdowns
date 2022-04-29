
import numpy as np
import pandas as pd
#import bisect
import sys


# def find_left(a, x):
#     'Find rightmost value less than or equal to x'
#     loc = bisect.bisect_right(a, x)
#     if loc:
#         return a[loc-1]
#     # If index is in first position, return -1 to force initial
#     # value of drawdowns to be selected as the left limit.
#     elif loc == 0:
#         return -1
#     # At this point, if we are still here, then we need to return the
#     # next to last index location because we are at the end of the list.
#     else:
#         return len(a)-1
#
#
# def find_right(a, x):
#     'Find leftmost value greater than x'
#     loc = bisect.bisect_left(a, x)
#     if loc != len(a):
#         return a[loc]
#     else:
#         return a[0]
#
#
# def find_drawdown_old(i, down_vals, up_vals):
#     thresholds = np.where(down_vals > down_vals[i])[0]
#     if len(thresholds) > 0:
#         left_val = up_vals[find_left(thresholds, i)+1]
#         right_val = up_vals[find_right(thresholds, i)]
#     else:
#         left_val = up_vals[0]
#         right_val = up_vals[-1]
#     if right_val > left_val:
#         return down_vals[i] - right_val
#     else:
#         return down_vals[i] - left_val
#

def find_drawdown(i, down_vals, down_locs, up_vals, up_locs):
    this = {}
    this['i'] = i
    this['peak_loc'] = down_locs[i]
    (left, right) = nearest_downvals(i, down_vals)
    start = lowest_upval(i, up_vals, idx=left, side='left')
    end = lowest_upval(i, up_vals, idx=right, side='right')
    this['start_loc'] = up_locs[start]
    this['end_loc'] = up_locs[end]
    this['peak_val'] = down_vals[i]
    this['start_val'] = up_vals[start]
    this['end_val'] = up_vals[end]
    this['filling'] = down_vals[i] - this['start_val']
    this['draining'] = down_vals[i] - this['end_val']
    this['duration'] = this['end_loc'] - this['start_loc']
    this['magnitude'] = min(this['filling'], this['draining'])
    return this


def nearest_downvals(i, down_vals):
    """
    Finds the location of the most recent down value
    that is larger in magnitude than down value i

    """
    if (down_vals[0: i] > down_vals[i]).any():
        left = np.max(np.where(down_vals[0: i] > down_vals[i])[0])
    else:
        left = None
    if (down_vals[i:] > down_vals[i]).any():
        right = np.min(np.where(down_vals[i:] > down_vals[i])[0]) + i
    else:
        right = None
    return (left, right)


def lowest_upval(i, up_vals, idx=None, side=None):
    if (idx is None) and (side == 'left'):
        idx = 0
    elif (idx is None) and (side == 'right'):
        idx = len(up_vals)
    if side == 'left':
        return np.argmin(up_vals[idx: i]) + idx
    elif side == 'right':
        return np.argmin(up_vals[i: idx]) + i
    else:
        raise(ValueError)

#
# def filling(down_vals, up_vals, i):
#     (l_idx, r_idx) = nearest_downvals(i, down_vals)
#     u_id = lowest_upval(i, up_vals, l_idx, side='left')
#     return down_vals[i] - up_vals[u_id]
#
#
# def draining(down_vals, up_vals, i):
#     (l_idx, r_idx) = nearest_downvals(i, down_vals)
#     u_id = lowest_upval(i, up_vals, r_idx, side='right')
#     return down_vals[i] - up_vals[u_id]


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
    # Insert a down_loc at the start of the data (9.99 value)
    down_locs = np.hstack([0, np.where(rev < 0)[0]])
    up_locs, = np.where(rev > 0)
    up_vals = data[up_locs + 1]
    down_vals = data[down_locs + 1]
    print("There are {n} total downvals".format(n=len(down_vals)))
    print("There are {n} total upvals".format(n=len(up_vals)))
    n = min(len(down_vals), len(up_vals))
    drawdowns = []
    # Start at the 2nd down_loc (we put a dummy down_loc at the start)
    [drawdowns.append(
        find_drawdown(i, down_vals, down_locs, up_vals, up_locs))
     for i in np.arange(1, n-1)]
    # Remove zero values of drawdowns.
    return drawdowns


if __name__ == "__main__":
    file = sys.argv[1]
    data = np.array(pd.read_csv(file)).T.squeeze()
    drawdowns = find_drawdowns(data)
    # print(drawdowns)
