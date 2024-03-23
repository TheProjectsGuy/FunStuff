# Reads a table from a PDF file
"""
    Input is a PDF file that has three columns (space separated) and
    they're as follows:
    - Data in the first column has no space
    - Second in the second column can have spaces
    - Data in the third column is a number with commas (no spaces). 
        Remove the commas and save number as int.
    
    Output is a CSV file with the given name.
    
    The first 'n' rows of the first page are ignored and the header is
    pre-programmed.
"""

# %%
import os
import sys
import tyro
import time
import PyPDF2
import traceback
import pandas as pd
from tqdm.auto import tqdm
from PyPDF2 import PdfReader
from dataclasses import dataclass, field
from typing import Optional, List
from joblib import Parallel, delayed


# %%
@dataclass
class Args:
    # The PDF file to read
    file: str
    # Output file name
    out_file: str = "./out.csv"
    # Specification of the row
    """
        Row specification (containing 'w' for words and 's' for space
        separated sentences). There should be only one 's' (column 
        containing space separated words). Entries in other columns 
        cannot have spaces.
        
        Eg: If the rows are in three columns and the second column can 
            contain spaces, then the specification should be 'wsw'.
    """
    spec: str = "wsw"
    # Headings in the output file (should be three columns)
    headings: list[str] = field(default_factory=lambda: 
                                ["a", "b", "c"])
    # Number of rows (from top) to skip on the first page
    skip_first_only: int = 2
    # Number of rows (from top) to skip on the second page onwards
    skip_second_onwards: int = 0
    # Number of rows (from bottom) to skip on every page
    skip_last: int = 0


# %%
def read_page_lines(page: PyPDF2.PageObject, page_no: int, 
            args: Args):
    """
        Reads lines of a page and returns the content parsed (as 
        columns).
        Parameters:
        - page: PyPDF2.PageObject   The page object (to process)
        - page_no: int              Page number (None)
        - args: Args                Arguments (for configurations)
    """
    # Arguments
    spec = args.spec
    skip_first_only = args.skip_first_only
    skip_second_onwards = args.skip_second_onwards
    skip_last = args.skip_last
    # Extract text
    pg_data = page.extract_text().splitlines()
    if page_no == 0:
        pg_data = pg_data[skip_first_only:]
    else:
        pg_data = pg_data[skip_second_onwards:]
    pg_data = pg_data[:-skip_last]
    page_content = []
    for row_data in pg_data:
        rd = row_data.split()
        s = spec
        assert len(s) == s.count("w") + s.count("s") and \
                s.count("s") == 1, "Only 'w's and one 's' allowed"
        s = list(map(lambda x: 1 if x == "w" else x, s))
        s[s.index("s")] = len(rd) - s.count(1)
        d = []  # Final row data as columns
        _i1 = 0 # Track 'rd' read so far
        for v in s:
            if v == 1:
                d.append(rd[_i1])
            elif v > 1:
                d.append(" ".join(rd[_i1 : _i1 + v]))
            _i1 += v
        page_content.append(d)
    return (page_no, page_content)


# %%
def main(args: Args):
    print(f"Arguments: {args}")
    # Validate arguments
    _ex = lambda x: os.path.realpath(os.path.expanduser(x))
    file = _ex(args.file)
    assert os.path.isfile(file) and file.endswith(".pdf"), \
            "Should be a PDF file on disk"
    # Read the file metadata
    reader = PdfReader(file)
    print(f"Reading file: {file}")
    print(reader.metadata)
    # Read contents
    all_page_data = []
    for p, page in enumerate(tqdm(reader.pages)):
        _, res = read_page_lines(page, p, args)
        all_page_data.append((p, res))  # (page number, row content)
    # all_page_data2 = Parallel(n_jobs=-1)(delayed(read_page_lines)\
    #         (page, i) for i, page in enumerate(tqdm(reader.pages)))
    data = []
    header = list(args.headings)
    print(f"Using the headings: {header}")
    for p, page in all_page_data:   # (page number, data)
        data.extend(page)
    df = pd.DataFrame(data, columns=header)
    df.to_csv(args.out_file, index=False)
    print(f"Read {len(data)} rows")
    print(f"Saved to: {args.out_file}")


if __name__ == "__main__" and "ipykernel" not in sys.argv[0]:
    try:
        start_time = time.time()
        args = tyro.cli(Args, description=__doc__)
        main(args)
        end_time = time.time()
        print(f"Total time: {end_time - start_time:.4f}s")
    except SystemExit as exc:
        print(f"System Exit: {exc}")
        exit(0)
    except:
        traceback.print_exc()


# %%
# Experimental section

