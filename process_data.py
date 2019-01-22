import numpy as np
import pandas as pd

# Load the data
yr_ls = [2007 + i for i in range(9)]
nfl_dict = {}
for yr in year_ls:
    nfl_dict[yr] = pd.read_csv("NFL_data/"+str(yr)+".csv")
    nfl_dict[yr].columns = ['win', 'loser', 'PtsW', 'PtsL', 'YdsW', 'TOW', 'YdsL',
       'TOL']

# Obtain the team index
ls1 = [i for i in nfl_dict[2007]["win"]]
ls2 = [i for i in nfl_dict[2007]["loser"]]

teams = list(set(ls1 + ls2))
teams.sort()

# Create correct format matrix
ymat_dict = {}
nmat_dict = {}
for yr in yr_ls:
    ymat_dict[yr] = pd.DataFrame(np.zeros((32,32)), columns=teams, index=teams)
    nmat_dict[yr] = pd.DataFrame(np.zeros((32,32)), columns=teams, index=teams)
    for row in range(nfl_dict[yr].shape[0]):
        i = nfl_dict[yr].loc[row, "win"]
        j = nfl_dict[yr].loc[row, "loser"]
        ymat_dict[yr].loc[i, j] += 1
    nmat_dict[yr] = ymat_dict[yr] + ymat_dict[yr].T
    nmat_dict[yr] = pd.DataFrame(np.tril(nmat_dict[yr]), index=teams, columns=teams)
    ymat_dict[yr] = pd.DataFrame(np.tril(ymat_dict[yr]), index=teams, columns=teams)

ymat_ls = []
nmat_ls = []
for yr in yr_ls:
    ymat_ls.append(ymat_dict[yr])
    nmat_ls.append(nmat_dict[yr])