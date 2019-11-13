#!/usr/bin/env python3
from root_pandas import read_root
import matplotlib.pyplot as plt
import matplotlib
import glob
import pandas as pd
from PyFastBDT import FastBDT
from sklearn.metrics import roc_auc_score, roc_curve, average_precision_score, precision_recall_curve, recall_score
import argparse

matplotlib.use('Agg')
pd.set_option('display.max_columns', None)
plt.rc('figure', figsize = (8, 6))
plt.rc('font', size = 14)
plt.rc('hist', bins = 200)

def plot_auc_chart(baseline, df):
    """Plot 1 - AUC versus removed features"""
    fig = plt.figure()
    df = df.sort_values(by = 'auc')
    plt.bar(df.feature, 1 - df.auc)
    plt.xticks(rotation = 90)
#     plt.ylim([0.997, 0.998])
    plt.axhline(y = 1 - baseline, color = 'red')
    plt.title('1 - AUC')
    return fig

def backward_selection(features, data, min_auc = 0.9975):
    # Make a copy of features so we do not accidentally modify them
    features = features.copy()
    
    print('Fitting the model with all the features...')
    bdt = FastBDT.Classifier()
    bdt.fit(data[features], data.isSignal)
    data['mva'] = bdt.predict(data[features])
    init_auc = roc_auc_score(data.isSignal, data.mva)
    print('Initial AUC:', init_auc)
    print('Minimum AUC to continue the search: %.4f' % min_auc)
    
    current_auc = init_auc
    best = pd.DataFrame()
    best = best.append({'n_features':len(features), 'best_auc':current_auc}, ignore_index = True)
    while current_auc >= min_auc:
        print("Trying to remove one feature...")
        result = pd.DataFrame()
        for i, _ in enumerate(features):
            reduced = [features[j] for j in range(len(features)) if j != i]
            bdt = FastBDT.Classifier()
            bdt.fit(data[reduced], data.isSignal)
            data['mva'] = bdt.predict(data[reduced])
            auc = roc_auc_score(data.isSignal, data.mva)
            result = result.append({'feature': features[i], 'auc': auc}, ignore_index = True)
        result = result.sort_values(by = 'auc', ascending = False)
        current_auc = result.iloc[0].auc
        best = best.append({'n_features':len(features) - 1, 'best_auc':current_auc}, ignore_index = True)
        features = result.iloc[1:].feature.values
        
        print("Highest AUC = %.4f" % current_auc)
        print("%s will be removed" % result.iloc[0].feature)
        print('Features left (%d):' % (len(features)))
        for f in features:
            print(f)
        print("AUC table")
        print(result)
        
        fig = plot_auc_chart(init_auc, result)
        fig.savefig('../models/auc_%d.png' % (len(features) - 1), bbox_inches = "tight")
        
    return best

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--small', action = 'store_true', help = 'Will use a small data set')
    args = parser.parse_args()
    
    print("Reading data...")
    train = read_root('../data/train_balanced.root', 'lambda')
    test = read_root('../data/test_balanced.root', 'lambda')
    
    if args.small == True:
        print("DEBUG MODE: use a small subset")
        train = train.sample(10000)
    
    features = ['dr', 'dz', 'cosaXY', 'min_dr', 'min_dz', 'pt', 'pz', 'chiProb', 
            'proton_PIDppi', 'proton_PIDpk', 'proton_PIDkpi', 'proton_p',
            'pi_PIDppi', 'pi_PIDpk', 'pi_PIDkpi', 'pi_p']
    print('Starting off with %d features' % len(features))
    
    best = backward_selection(features, train)
    print("Best AUC for each number of features")
    print(best)
    
