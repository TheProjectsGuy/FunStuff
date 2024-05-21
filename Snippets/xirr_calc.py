# Calculate XIRR from a given set of (Date, Cashflow) values
"""
    A program to calculate the interest rate of return (XIRR) so that
    the resultant time value of money (total transactions) is zero.
    The program also allows calculating the present value of 
    investments given an interest rate ('present' mode).
    The dates corresponding to the cashflows can be specified in one 
    of the following ways:
    1. Only `values` are specified: The dates are considered years 
        (with value[0] being year 0, [1] being 1, and so on)
    2. Specifying `years` to specify the corresponding year for the
        `values`
    3. Explicitly specifying a list of dates (with `dates`) in a 
        format given by `date_fmt`
    
    Example calls:
    ```bash
    # XIRR of cash flows (withdrawls/outflows in -ve)
    python ./xirr_calc.py --date-fmt '%d-%m-%Y' --values 1000 1000 -2500 --dates 1-1-2000 1-1-2001 1-2-2004
    python ./xirr_calc.py --values 1000 1000 -2200 --years 2000 2001 2006
    python ./xirr_calc.py --date-fmt '%d-%b-%Y' --data-file ./Transactions.csv
    
    # Present value of cash flows (deposit in +ve, withdraw in -ve)
    python ./xirr_calc.py --mode present --date-fmt '%d-%m-%Y' --values 1000 1000 0 --dates 1-1-2020 1-6-2020 1-1-2021 --irr 6
    python ./xirr_calc.py --date-fmt '%d-%b-%Y' --data-file ./Transactions.csv --mode present --irr 10
    ```
"""

# %%
import sys
import tyro
import scipy
import pandas as pd
import scipy.optimize
from datetime import datetime
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Optional, Union, Literal


# %%
@dataclass
class LocalArgs:
    # List of values to use (cashflows)
    values: Optional[list[float]] = None
    # List of year to use (relative and corresponding to values)
    """
        List of zero-indexed years to use (relative and corresponding 
        to the values). If not specified, the years are assumed to be
        the index of `values` like [0, 1, 2, ...].
        However, they can also be actual years (corresponding to the
        transactions), like [2000, 2001, ...].
    """
    years: Optional[list[float]] = None
    # List of dates of investment (instead of mere years)
    dates: Optional[list[str]] = None
    """
        Similar to `years`, but the dates are given in the format
        specified by `date_fmt` (see format codes [1]). If explicitly
        specifying the dates, either `years` or `dates` should be
        given (but not both). This is set to None after validation
        (it internally converts this to fractional years).
        
        [1]: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
    """
    # Format for input dates
    date_fmt: str = r"%Y-%m-%d"
    # Data file (for CSV data)
    data_file: Optional[str] = None
    """
        If using data through a CSV file (and not the `values` and
        duration through command line), specify the file here. Else
        keep this None. The program reads the file and extracts the
        dates (in the `date_fmt`) from the first column and the values
        from the second column. Everything else (including the
        headings) is ignored.
    """
    # Mode of functioning
    mode: Literal["xirr", "present"] = "xirr"
    """
        Program has two modes of functioning:
        1. `xirr`: Calculate the XIRR from the cashflows.
        2. `present`: Calculate the present value of the cashflows
                given an IRR value (interest rate). Need to specify
                the `years` (or `dates`) of cashflows and `irr` to
                use. The present value is calculated at the last value
                in `dates` or `years` (whichever is specified).
    """
    # IRR (for 'present' mode)
    irr: Optional[float] = None

    # Validate the function
    def validate(self):
        if self.data_file is not None:
            assert self.values is None and self.years is None \
                and self.dates is None, \
                    "When data file is specified, do not use " \
                    "--values, --dates, or --years (they're read " \
                    "from the file)."
            dframe = pd.read_csv(self.data_file)
            self.dates = dframe.iloc[:, 0].tolist()
            self.values = dframe.iloc[:, 1].tolist()
        # Verify the dates or years arrangement (in command line)
        if self.dates is not None and self.years is not None:
            raise ValueError("Either --dates or --years should be "\
                    "specified, but not both")
        if self.years is None and self.dates is None:
            self.years = list(range(len(self.values)))
        elif self.dates is not None:
            self.years = []
            for date in self.dates:
                yr = datetime.strptime(date, self.date_fmt).year
                n = int(datetime.strptime(date, self.date_fmt)\
                        .strftime(r"%j"))
                d = int(datetime.strptime(f"{yr}-12-31", 
                        r"%Y-%m-%d").strftime(r"%j"))
                yr = yr + n / d
                self.years.append(yr)
            self.dates = None   # Just as backup
        # Mode
        if self.mode == "present":
            assert self.irr is not None, "IRR value is required for "\
                    "present value calculation"


# %%
# Return a function that takes in interest rate and gives present val
def year_value_opt_func_generator(vals, years):
    rev_vals = list(reversed(vals))   # [present, ..., past]
    rev_years = list(reversed(years))
    # Function to generate current value given interest
    def curr_value(x):
        pv = 0
        for i, v in enumerate(rev_vals):
            pv += v * (1 + x) ** (rev_years[0] - rev_years[i])
        return pv
    return curr_value


# %%
if __name__ == "__main__" and "ipykernel" not in sys.argv[0]:
    args = tyro.cli(LocalArgs, description=__doc__)
    print(f"Arguments: {args}")
    args.validate()
    opt_func = year_value_opt_func_generator(args.values, args.years)
    if args.mode == "xirr":
        irr = scipy.optimize.fsolve(opt_func, 0.1)[0]
        print(f"IRR: {round(irr * 100, 3)} %")
    elif args.mode == "present":
        pv = opt_func(args.irr / 100)
        print(f"Present value: {round(pv, 4)}")
    exit(0)


# %%
# Experimental section
import pandas as pd

# %%
data_file = "./Transactions.csv"

# %%
data = pd.read_csv(data_file)

# %%
