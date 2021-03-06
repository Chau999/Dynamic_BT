

# # Dynamic Bradley Terry

from .sstools import simulate
from pypolyagamma import PyPolyaGamma
import numpy as np
import pandas as pd
from scipy.stats import binom, norm, multivariate_normal

def win_prob(i,j, betas, covariates=None):
    if covariates is None:
        covariates = identity_matrix(len(betas))
        
    return 1/ (1 + np.exp((covariates[j] - covariates[i]).dot(betas)))

def diff_matrix(n):
    D = np.matrix([[0]*n]*int((n-1)*n/2))
    row = 0
    for i in range(n):
        for j in range(n):
            if j >= i+1:
                D[row,i] = 1
                D[row,j] = -1
                row += 1
    return D

def identity_matrix(n):
    return np.diag(np.repeat(1,n))

def simulate_data(beta_0, num_players, num_matches, time_range, rho, sig, covariates):
    # ---------------------------------------
    # pre loop init
    betas = [None] * len(time_range)
    y = [np.matrix([[None]*num_players]* num_players) for t in time_range]  
    beta= beta_0

    # Generate results through time
    for t in time_range:
        # init point in time results matrix
        y_t = np.matrix([[0 for j in range(num_players) ] for i in range(num_players)])
        n_t = num_matches[t]

        # loop through player combinations and simulate wins
        for i in range(num_players):
            for j in range(num_players):
                if j > i:
                    y_t[i,j] = binom.rvs(n_t[i,j], win_prob(i,j, beta, covariates), size=1)
        y[t] = y_t

        # store used abilities
        betas[t] = beta
        # propogate abilities through time for next iteration
        beta = rho*beta + sig* np.sqrt(1-rho**2) * norm.rvs(size = len(beta), loc=0, scale=1)
        
    return y, betas

# ## MCMC Augmented Gibbs- Simulation Smoother Methods

# Helpers

# PG update for aux vars
# ----------------------------------------------------------------
def sample_aux_vars(betas, num_matches, time_range, covariates=None):
    pg = PyPolyaGamma()
    if covariates is None:
        covariates = identity_matrix(len(betas))

    if covariates.ndim == 2:
        num_players = len(covariates)
        aux_vars = [np.matrix(
                          [[pg.pgdraw(num_matches[t][i,j], (covariates[i]- covariates[j]).dot(betas[t]))
                            #entries
                  for j in range(num_players) # columns
                          ] 
                 for i in range(num_players) # rows
                          ]
                      ) for t in time_range # index of matrix-list
                      ]
    else:
        num_players = len(covariates[0])
        aux_vars = [np.matrix(
                          [[pg.pgdraw(num_matches[t][i,j], (covariates[t][i]- covariates[t][j]).dot(betas[t]))
                            #entries
                  for j in range(num_players) # columns
                          ] 
                 for i in range(num_players) # rows
                          ]
                      ) for t in time_range # index of matrix-list
                      ]
                

    return aux_vars

# Omega (covariance of normal response)
# ----------------------------------------------------------------
def get_response_covariance_t(aux_vars, t, num_players):
    reduced_avars = [[1/aux_vars[t][i,j] for j in range(num_players) if j>i] for i in range(num_players)]
    list_reduced_avars = np.concatenate(reduced_avars)
    response_cov = np.diag(list_reduced_avars)
    return response_cov

def get_response_covariance(aux_vars,num_players):
    time_range = range(len(aux_vars))
    return np.array([get_response_covariance_t(aux_vars, t, num_players)
                     for t in time_range])

# Normal response
# ----------------------------------------------------------------
def get_response_t(y, t, num_matches, aux_vars, num_players):
    reduced_obs = [[(y[t][i,j] - num_matches[t][i,j]/2)/aux_vars[t][i,j]
                 for j in range(num_players) if j>i] for i in range(num_players)]
                
    reduced_obs_list = np.concatenate(reduced_obs)
    return reduced_obs_list


def get_response(y, num_matches, aux_vars, num_players):
    time_range = range(len(y))
    return np.array([get_response_t(y, t, num_matches, aux_vars, num_players) 
                     for t in time_range])
                     
#simulate data
# init state
# betas = [norm.rvs(loc=2, scale = 1, size = len(beta_0)) for t in time_range]
# simulate data
# y_obs, beta_true = simulate_data(beta_0, num_players, num_matches, time_range, rho, sig, covariates)


def mcmc_dbt(covariates, y_obs, beta_0, init_betas,num_matches,time_range,num_players, rho, sig, nsim=1000):
    # Gibbs iterations
    #  betas init above
    
    betas = init_betas
    beta_res = [None] * nsim

    for i in range(nsim):
         # simulate polya gamma aux variables
        aux_vars = sample_aux_vars(betas, num_matches, time_range ,covariates)

        if i % 100 == 0:
            print("Simulation {0} of {1}".format(i, nsim))
        if covariates.ndim == 2:
            Z = diff_matrix(num_players).dot(covariates)
        else:
            Z = np.array([diff_matrix(num_players).dot(covariates[t]) for t in time_range])
                         
            # simulation smoother for state, beta
        betas = simulate( 
            a_init = beta_0, 
            P_init = identity_matrix(len(beta_0)), 
            Z = Z , # put covariates into here
            y = get_response(y_obs, num_matches, aux_vars, num_players),
            H = get_response_covariance(aux_vars, num_players), 
            T = identity_matrix(len(beta_0))*rho, 
            R = identity_matrix(len(beta_0)) * sig * np.sqrt(1-rho**2), 
            Q = identity_matrix(len(beta_0)))
        # store state    	
        beta_res[i] = betas

    # return 
    return beta_res




