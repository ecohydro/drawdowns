import numpy as np
import pandas as pd
import sys
import logging
from tqdm.notebook import trange, tqdm
import matplotlib.pyplot as plot

# Set up the Logger for debugging.
FORMAT = "[%(asctime)s %(filename)s->%(funcName)s():%(lineno)s]%(levelname)s: %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)
L = logging.getLogger(__name__)

def cum_dist(data):
    x = np.sort(data)
    y = np.arange(len(data))/float(len(data))
    return x, y

class Drawdown:
    
    def __init__(self, 
                 data=None, 
                 filename=None, 
                 find_drawdowns=False,
                 debug=False):
        """Initializes a Drawdown object.

        Parameters
        ----------
        data : np_array, optional
            np_array of Plant Available Water Storage (PAWS) data, by default None
        filename : string, optional
            .csv file containing a timeseries of PAWS, by default None
        find_drawdowns : bool, optional
            determines if drawdown analysis should be done during initialization, by default False
        debug : bool, optional
            determines if debugging messages will be logged, by default False
        
        Usage
        -----
        
        At the command line:
        
        > Drawdown.py <filename>.csv
        
        where <filename>.csv is a .csv file containing plant available water storage (PAWS) in column format.
        
        This will generate a <filename>_output.csv file containing a row for each drawdown with the following columns:
        i,peak_loc,peak_val,start_loc,start_val,end_loc,end_val,filling,draining,duration,magnitude,data,type
        
        """
        if debug == True:
            L.setLevel(logging.DEBUG)
        if data:
            self.S = data
        elif filename:
            self.S = np.array(pd.read_csv(filename)).T.squeeze()
        # Insert a leading non-zero value to force a up_val at the start of the
        # Storage timeseries.
        if self.S[0] != 9.99:
            self.S = np.insert(self.S, 0, 9.99)
        self._down_locs = self.down_locs()
        self._down_vals = self.down_vals()
        self._up_locs = self.up_locs()
        self._up_vals = self.up_vals()
        L.info("There are {n} total downvals".format(n=len(self._down_vals)))
        L.info("There are {n} total upvals".format(n=len(self._up_vals)))
        if find_drawdowns:
            L.info("Cacluating drawdowns...")
            self.make_drawdowns()
            
    def make_drawdowns(self):
        """
        Constructs drawdowns based on PAWS data.
        
        """
        n = min(len(self._down_vals), len(self._up_vals))
        self.drawdowns = []
        # Start at the 2nd down_loc (we put a dummy down_loc at the start)
        for i in trange(1, n):
                self.drawdowns.append(self.find_drawdown(i))
        self.df = pd.DataFrame(self.drawdowns)

    def find_drawdown(self, i, debug=False):
        """_summary_

        Parameters
        ----------
        i : int
            Drawdown number to find
        debug : bool, optional
            determines if debugging messages will be logged, by default False

        Returns
        -------
        dict
            dictionary of drawdown attributes
        """
        if debug:
            L.setLevel(logging.DEBUG)
        L.debug(f"Finding Drawdown {i}")
        this = {}
        this['i'] = i
        this['peak_loc'] = self._down_locs[i]
        this['peak_val'] = self._down_vals[i]
        #################################################
        # FINDING START AND END TO DRAWDOWNS            #
        #                                               #
        #################################################
        this['start_loc'], this['start_val'] = self.find_start(i)
        this['end_loc'], this['end_val'] = self.find_end(i)
        
        # filling is the difference between the peak value and the starting value (ascending limb)
        this['filling'] = this['peak_val'] - this['start_val']
        # draining is the difference between the peak value and the ending value (descending limb)
        this['draining'] = this['peak_val'] - this['end_val']
        # The magnitude of this drawdown is the minimum of the desending and ascending limbs
        this['magnitude'] = min(this['filling'], this['draining'])
        idx_peak = this['peak_loc']
        #################################################
        # FILLING AND DRAINING DRAWDOWNS                #
        #                                               #
        #################################################
        # If the filling limb was smaller, then we have a filling drawdown.
        # In that case, assign the end_val to be the same as the start_val
        if this['magnitude'] == this['filling']:
            L.debug(f"Drawdown {i} is `filling` type.")
            this['type'] = 'filling'
            L.debug("\tUpdating `end_val` to {val} from {old}".format(
                val=this['start_val'],
                old=this['end_val']
            ))
            this['end_val'] = this['start_val']
            # We need to update the end_loc find the nearest location to the right of this peak
            # that is less than or equal to the end_val.
            L.debug(
                f"Searching for nearest value to the right that is smaller than {this['end_val']}"
            )
            this['end_loc'] = idx_peak + np.min(np.where(self.S[idx_peak:] <= this['end_val']))
            L.debug(f"Found new end_loc at {this['end_loc']}, which is equal to {self.S[this['end_loc']]}")
        else:
        # If the draining limb was smaller, then we have a draining drawdown.
        # In that case, assign the start_val to be the same as the end_val
            L.debug(f"Drawdown {i} is `draining` type.")
            this['type'] = 'draining'
            L.debug("\tUpdating `start_val` to {val} from {old}".format(
                val=this['end_val'],
                old=this['start_val']
            ))
            this['start_val'] = this['end_val']
            L.debug(
                f"Searching for nearest value to the left that is smaller than {this['start_val']}"
            )
            this['start_loc'] = np.max(
                np.where(self.S[:idx_peak] <= this['start_val']))
            L.debug(
                f"Found new start_loc at {this['start_loc']}, which is equal to {self.S[this['start_loc']]}")
        # Save all the drawdown data
        this['data'] = self.S[this['start_loc']:this['end_loc']+1]
        # Set the final duration based on the updated start_loc and end_locs
        this['duration'] = this['end_loc'] - this['start_loc']
        return this
        
    def up_vals(self):
        """ Returns a list of the values of storage associated with each location
        where storage shifted from increasing to decreasing
        
        These values represent downward inflection points.
        Downward inflection points are usually times the indicate a peak 
        marking the mid-point of a drawdown.
        
        Drawdown structure:
        
        down_val -> up_val -> down_val
        
        """
        return self.S[self.up_locs()]
    
    def down_vals(self):
        """ Returns a list of the values of storage associated with each location
        where storage shifted from decreasing to increasing.
        
        These values represent upward inflection points in the dataset.
        Upward inflection points are usually times when a new drawdown begins.
        
        """
        return self.S[self.down_locs()]
     
    def slope(self):
        """Returns fist derivative of the Storage timeseries
        
        positive values are where S is increasing
        
        negative values are where S is decreasing
        """
        return np.diff(self.S)

    def rev(self):
        """Returns locations where the time series reverses direction
        
        1. First determines all locations where S is increasing
        2. Assigns these locations to value 1
        3. Takes differences between each value. This will return:
            0 where slope is increasing [1 1 1] -> [0 0]
            0 where slope is decreasing [0 0 0] -> [0 0]
            -1 where shifting from decreasing to increasing [0 1 1] -> [-1 0]
            +1 where shifting from increasing to decreasing [1 0 0] -> [+1 0]
        
        4. Returns an array of {-1, +1, 0} for each location in time series.
        """
        return np.diff((self.slope() > 0).astype(int))

    def down_locs(self):
        """ Return the location of all places where storage switched from
            decreasing to increasing (a local "valley" in storage amount) 
        
            These locations represent upward inflection points in the dataset.
            Upward inflection points are usually times when a new drawdown begins.
        
            NOTE: Do we need to add a "dummy" data point to the end of the data?
            
        """
        # Add 0 to the list of down_locs, since we have started the data with a 
        # dummy data point.
        down_locs = np.hstack([0, np.where(self.rev() < 0)[0]])
        return down_locs + 1
    
    def up_locs(self):
        """ Return the location of all places where storage switched from 
            increasing to decreasing (a local "peak" in storage amount)
        
            These values represent downward inflection points in the dataset.
            Downward inflection points are usually times when a peak occurs.
        
        """
        up_locs, = np.where(self.rev() > 0)
        return up_locs + 1
    
    def find_start(self, i):
        """
        
        1. Search to the left of peak_loc.      
        2. Look for the nearest downval (peak) to the left that is greater than this peak.
            2a. If a peak to the left is larger than this one:
                2aa: Find the smallest valley between the nearest higher peak and this peak
                THE LOCATION OF THIS VALLEY OR THE NEAREST ZERO - WHICHEVER IS CLOSER - 
                IS THE PROVISIONAL START OF THIS DRAWDOWN.
            2b. If no peaks to the left are larger than this one:
                2bb. Look for the nearest filling drawdown between the provisional start and this peak
                THE END OF THAT DRAWDOWN OR THE NEAREST ZERO - WHICHEVER IS CLOSER IS THE START OF THIS DRAWDOWN   
        """
        start_loc = 0
        L.debug("Looking for initial start position...")
        L.debug("Drawdown {i} peak is {peak} at location {loc}".format(
            i=i,
            peak=self._down_vals[i],
            loc=self._down_locs[i],
        ))
        # Step 2: Look for the nearest downval (peak) to the left that is greater than this peak.
        if (self._down_vals[0: i] >= self._down_vals[i]).any():
            idx_peak = np.max(np.where(self._down_vals[0: i] >= self._down_vals[i])[0])
            nearest_peak_loc = self._down_locs[idx_peak]
            L.debug("\tFound a higher previous peak ({value}) at location {loc}".format(
                value=self._down_vals[idx_peak],
                loc=nearest_peak_loc
            ))
            L.debug("\tSearching for smallest valley between loc {p1} & loc {p2}".format(
                p1=nearest_peak_loc,
                p2=self._down_locs[i]
            ))
            idx_up = idx_peak + np.argmin(self._up_vals[idx_peak:i])
            L.debug("\t\tFound valley {val} at {loc}".format(
                val=self._up_vals[idx_up],
                loc=self._up_locs[idx_up]
            ))
            L.debug("\tSetting initial start_loc to {loc}".format(
                loc=self._up_locs[idx_up],
            ))
            start_loc = self._up_locs[idx_up]
        L.debug("\tChecking for a closer zero between {loc} and {loc2}".format(
            loc=start_loc,
            loc2=self._down_locs[i]
        ))
        if (self.S[start_loc+1:self._down_locs[i]]==0).any():
            nearest_zero = start_loc + np.max(
                np.where(self.S[start_loc:self._down_locs[i]]==0)[0]
            )
            L.debug("\t\tFound a closer zero at location {loc}".format(
                loc=nearest_zero
            ))
            L.debug("\tUpdating start_loc to {zero} from {start_loc}".format(
                    zero=nearest_zero,
                    start_loc=start_loc
                ))
            start_loc = nearest_zero
        return start_loc, self.S[start_loc]
    
    def find_end(self, i):
        """
        1. Search to the right of peak_loc.
        2. Look for the nearest downval (peak) to the right that is greater than this peak.
            2a. If a peak to the right is larger than this one:
                2aa: Find the smallest valley between the nearest higher peak and this peak
                THE LOCATION OF THIS VALLEY OR THE NEAREST ZERO - WHICHEVER IS CLOSER - IS THE START OF THIS DRAWDOWN.
            2b. If no peaks to the right are larger than this one:
                THE END OF THE DATA OR THE NEAREST ZERO - WHICHEVER IS CLOSER IS THE START OF THIS DRAWDOWN   
        """
        end_loc = len(self.S)-1
        L.debug("Looking for initial end position...")
        L.debug("Drawdown {i} peak is {peak} at location {loc}".format(
            i=i,
            peak=self._down_vals[i],
            loc=self._down_locs[i],
        ))
        if (self._down_vals[i+1:] >= self._down_vals[i]).any():
            idx_peak = (i + 1) + np.min(np.where(self._down_vals[i+1:] >= self._down_vals[i])[0])
            nearest_peak_loc = self._down_locs[idx_peak]
            L.debug("\tFound a higher subsequent peak ({value}) at location {loc}".format(
                value=self._down_vals[idx_peak],
                loc=nearest_peak_loc
            ))
            L.debug("\tSearching for smallest valley between loc {p1} & loc {p2}".format(
                    p1=self._down_locs[i],
                    p2=nearest_peak_loc
                ))
            idx_up = i + np.argmin(self._up_vals[i:idx_peak])
            L.debug("\t\tFound valley {val} at {loc}".format(
                val=self._up_vals[idx_up],
                loc=self._up_locs[idx_up]
            ))
            L.debug("\tSetting initial end_loc to {loc}".format(
                loc=self._up_locs[idx_up],
            ))
            end_loc = self._up_locs[idx_up]
            L.debug("\tChecking for a closer zero between {loc} and {loc2}".format(
                loc=self._down_locs[i],
                loc2=end_loc
            ))
        # Check to see if any of the values between this down_loc and the end_loc are zero
        # (do not use the current down_loc in the check)
        if (self.S[self._down_locs[i]+1:end_loc]==0).any():
            # If there is a zero closer than the nearest down_loc, then use that value instead.
            nearest_zero_idx = self._down_locs[i]+1 + np.min(
                np.where(self.S[self._down_locs[i]+1:end_loc]==0)[0])
            nearest_zero_loc = self._down_locs[nearest_zero_idx]
            if nearest_zero_loc > len(self.S)-1:
                nearest_zero_loc = len(self.S)-1
            L.debug("\t\tFound a zero at location {loc}".format(
                loc=nearest_zero_loc
            ))
            if nearest_zero_loc < end_loc:
                L.debug("\tUpdating end_loc to {zero} from {end_loc}".format(
                    zero=nearest_zero_loc,
                    end_loc=end_loc
                ))
                end_loc = nearest_zero_loc
        # If there are no future down_vals (peaks) that are larger than the current one,
        # and there are no future zeros in the timeseries, then we are going to
        # _assume_ that the end_val and end_loc are at the minimum of all future values.
        # essentially we set the end_val and end_loc to the smallest future up_loc.
        else:
            L.debug(
               f"\tNo larger peak found than {self._down_vals[i]} and no zero found.")
            L.debug("\tSetting end_val and end_loc to smallest future up_loc")
            # Find the smallest future up_val:
            minimum_up_val = np.min(self._up_vals[i:end_loc])
            # Set nearest_minimum to the location of the minimum_up_val 
            # in the list of up_vals
            nearest_minimum_idx = i + np.where(
                self._up_vals[i:end_loc]==np.min(self._up_vals[i:end_loc]))[0][0]
            nearest_minimum_loc = self._up_locs[nearest_minimum_idx]
            if nearest_minimum_loc > len(self.S)-1:
                nearest_minimum_loc = len(self.S)-1
            L.debug("\t\tFound a minimum at location {loc}".format(
                loc=nearest_minimum_loc
            ))
            if nearest_minimum_loc < end_loc:
                L.debug("\tUpdating end_loc to {minimum} from {end_loc}".format(
                    minimum=nearest_minimum_loc,
                    end_loc=end_loc
                ))
                end_loc = nearest_minimum_loc        
        return end_loc, self.S[end_loc]

    def to_csv(self, filename):
        L.info(f"Writing drawdown data to {filename}")
        if filename:
            self.df.to_csv(filename)
        else:
            return self.df.to_csv()

    def plot(self,
        min_loc=None, max_loc=None, threshold=0,
        show_up_locs=True, show_down_locs=True, offset=10):
        
        if not min_loc:
            min_loc = 0
        if not max_loc:
            max_loc = len(self.S)
        data = self.S[min_loc:max_loc]
        slope = np.diff(data)
        rev = np.diff((slope > 0).astype(int))
        down_locs,  = np.where(rev < 0)
        up_locs,  = np.where(rev > 0)
        up_vals = data[up_locs + 1]
        down_vals = data[down_locs + 1]
        valid = pd.DataFrame()
        if not self.drawdowns is None:
            valid = self.df[(self.df['start_loc']>=min_loc) 
                            & (self.df['end_loc']<=max_loc)
                            & (self.df['magnitude']>=threshold)]
        if len(valid) > 0:
            show_drawdowns = True
        else:
            show_drawdowns = False 
        plot.plot(data)
        
        # plot.plot(down_locs,down_vals,'r')
        if show_down_locs:
            for loc, val in zip(down_locs, down_vals):
                plot.annotate("",xy=(loc+1,val), xytext=(loc+1,val+offset),
                            arrowprops=dict(arrowstyle="->",color="red"))
        if show_up_locs:
            for loc, val in zip(up_locs, up_vals):
                plot.annotate("",xy=(loc+1,val), xytext=(loc+1,val-offset),
                            arrowprops=dict(arrowstyle="->",color="green"))
        if show_drawdowns:
            for index, row in valid.iterrows():
                x = [row['start_loc']-min_loc,
                    row['start_loc']-min_loc+row['duration']
                    ]
                y = [row['peak_val']+offset, row['peak_val']+offset]
                plot.plot(x,y,'k')
                plot.plot(x,y,'yellow',linewidth=7,alpha=0.5)
                vx1 = [row['start_loc']-min_loc,
                    row['start_loc']-min_loc]
                vy1 = [row['peak_val']+offset,
                    row['start_val']]
                plot.plot(vx1,vy1,'k--', linewidth=0.5)
                vx2 = [row['end_loc']-min_loc,
                    row['end_loc']-min_loc]
                vy2 = [row['peak_val']+offset,
                    row['end_val']]
                plot.plot(vx2,vy2,'k--', linewidth=0.5)
                xt = row['start_loc']-min_loc+row['duration']/2
                yt = row['peak_val']+offset*1.1
                plot.text(xt,yt,"{m:.1f}".format(m=row['magnitude']))
                plot.ylim(min(data)-1.2*offset,max(data)+1.4*offset)

if __name__ == "__main__":
    try:
        file = sys.argv[1]
    except:
        print(help(Drawdown))    
    name, ext = file.split('.')
    drawdown = Drawdown(filename=file, find_drawdowns=True)
    drawdown.to_csv(name+'_output.csv')
