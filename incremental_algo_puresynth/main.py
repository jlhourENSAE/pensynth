#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 10:51:38 2020

Lalonde dataset

@author: jeremylhour
"""


########## FUNCTIONS AND PACKAGES ##########

import sys
sys.path.append('/Users/jeremylhour/Documents/code/pensynth/incremental_algo_puresynth/')

import numpy as np
import pandas as pd
import time

from functions import *

########## DATA MANAGEMENT ##########

### loading Lalonde's dataset rescaled as in thepaper and unscaled for statistics
X1_full = np.loadtxt('/Users/jeremylhour/Documents/code/pensynth/data/Lalonde_X1.txt',skiprows=1)
Y1_full = np.loadtxt('/Users/jeremylhour/Documents/code/pensynth/data/Lalonde_Y1.txt',skiprows=1)
X0_full = np.loadtxt('/Users/jeremylhour/Documents/code/pensynth/data/Lalonde_X0.txt',skiprows=1)
Y0_full = np.loadtxt('/Users/jeremylhour/Documents/code/pensynth/data/Lalonde_Y0.txt',skiprows=1)
X0_unscaled_full = np.loadtxt('/Users/jeremylhour/Documents/code/pensynth/data/Lalonde_X0_unscaled.txt',skiprows=1)

### Consolidate duplicates in X0
df = pd.DataFrame(X0_full)
df.columns = ['age_rescaled', 'education_rescaled', 'married_rescaled', 'black_rescaled', 'hispanic_rescaled', 're74_rescaled', 're75_rescaled', 'nodegree_rescaled', 'NoIncome74_rescaled', 'NoIncome75_rescaled']

df['outcome'] = Y0_full

X_names = ['age', 'education', 'married', 'black', 'hispanic', 're74', 're75', 'nodegree', 'NoIncome74', 'NoIncome75']
df[X_names] = X0_unscaled_full


### Consolidate dataset
df_consolidated = df.groupby(X_names)[[i+'_rescaled' for i in X_names] + ['outcome'] + X_names].mean()
X0 = df_consolidated[[i+'_rescaled' for i in X_names]].to_numpy()
X0_unscaled = df_consolidated[X_names].to_numpy()
Y0 = df_consolidated['outcome'].to_numpy()


########## APPLYING THE IN-HOUSE ALGORITHM ##########
p = X1_full.shape[1]
all_w = np.zeros((X1_full.shape[0],X0.shape[0]))

start_time = time.time()

for index in range(X1_full.shape[0]):
    sys.stdout.write("\r{0}".format(index))
    sys.stdout.flush()
    
    x = X1_full[index]
    same_as_untreated = np.all(X0==x,axis=1) # True if untreated is same as treated
    
    if any(same_as_untreated): # if same as treated, assign uniform weights to these untreated
        untreated_id = [i for i, x in enumerate(same_as_untreated) if x]
        all_w[index,untreated_id] = 1/len(untreated_id)
    else:
        in_hull_flag = in_hull(x, X0)
        if in_hull_flag:
            X0_tilde, antiranks = incremental_pure_synth(X1_full[index],X0)
            w = pensynth_weights(np.transpose(X0_tilde),X1_full[index], pen=0.000001)
            all_w[index,antiranks] = np.transpose(w)
        else:
            w = pensynth_weights(np.transpose(X0),X1_full[index], pen=0)
            all_w[index,] = np.transpose(w)

print(f"Temps d'exécution total : {(time.time() - start_time):.2f} secondes ---")


########## Save weights ##########
np.savetxt('/Users/jeremylhour/Documents/code/puresynth_solution.csv', all_w, delimiter=',')


########## Compute the necessary statistics ##########
Y0_hat = np.matmul(all_w,Y0)

print('ATT: {:.2f}'.format((Y1_full - Y0_hat).mean()))

balance_check = np.matmul(all_w,X0_unscaled).mean(axis=0)
for b in range(len(balance_check)):
    print(X_names[b] +': {:.2f}'.format(balance_check[b]))

sparsity_index = (all_w > 0).sum(axis=1)
print('Min sparsity: {:.0f}'.format(sparsity_index.min()))
print('Median sparsity: {:.0f}'.format(np.median(sparsity_index)))
print('Max sparsity: {:.0f}'.format(sparsity_index.max()))

activ_index = (all_w > 0).sum(axis=0)>0
print('Active untreated units: {:.0f}'.format(activ_index.sum()))

########## Unit with sparsity > p+1? ##########
high_sparsity = np.where(sparsity_index>11)[0][0]
w_s = all_w[high_sparsity,]

