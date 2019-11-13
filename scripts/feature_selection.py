#!/usr/bin/env python3
from root_pandas import read_root
import matplotlib.pyplot as plt
import matplotlib
import glob
import pandas as pd
from PyFastBDT import FastBDT
from sklearn.metrics import roc_auc_score, roc_curve, average_precision_score, precision_recall_curve, recall_score
import argparse
import multiprocessing

# Otherwise there would be an error if you are running in the background
matplotlib.use('Agg')

pd.set_option('display.max_columns', None)
plt.rc('figure', figsize = (8, 6))
plt.rc('font', size = 14)
plt.rc('hist', bins = 200)

def plot_auc_chart(baseline, table):
    """Plot 1 - AUC versus removed features
    
    baseline:
        A dictionary containing initial metrics.
        E.g. baseline = {'train_auc': xxx, 'test_auc': 'yyy'}
    table:
        Results from the backward selection
        E.g.
        table = {'feature': [...], 'train_auc':[...], ...}
    """
    fig = plt.figure()
    table = table.sort_values(by = 'test_auc')
    
    plt.bar(table.feature, 1 - table['train_auc'], label = 'train', alpha = 0.5)
    plt.bar(table.feature, 1 - table['test_auc'], label = 'test', alpha = 0.5)
    
    plt.xticks(rotation = 90)
    
    plt.axhline(y = 1 - baseline['train_auc'], color = 'red', label = 'Full model (train)')
    plt.axhline(y = 1 - baseline['test_auc'], color = 'blue', label = 'Full model (test)')
    plt.legend()
    plt.title('1 - AUC')
    return fig

def worker(reduced, data, test = None, workerID = None):
    """Worker process
    
    reduced:
        Feature subset
    data:
        Data
    """
    # Make a copy of data
    #data = data.copy()
    bdt = FastBDT.Classifier()
    bdt.fit(data[reduced], data.isSignal)
    data['mva'] = bdt.predict(data[reduced])
    train_auc = roc_auc_score(data.isSignal, data.mva)
    ret = {'train_auc': train_auc}
    if test is not None:
        bdt.fit(test[reduced], test.isSignal)
        test['mva'] = bdt.predict(test[reduced])
        test_auc = roc_auc_score(test.isSignal, test.mva)
        ret = {**ret, 'test_auc': test_auc}
    if workerID is not None:
        print("Worker %d finished the job!" % workerID)
    return ret


def backward_selection(features, data, test = None, min_auc = 0.9975):
    # Make a copy of features so we do not accidentally modify them
    features = features.copy()
    
    print('Fitting the model with all the features...')
    bdt = FastBDT.Classifier()
    bdt.fit(data[features], data.isSignal)
    data['mva'] = bdt.predict(data[features])
    test['mva'] = bdt.predict(test[features])
    init_train_auc = roc_auc_score(data.isSignal, data.mva)
    init_test_auc = roc_auc_score(test.isSignal, test.mva)
    print('Initial training AUC:', init_train_auc)
    print('Initial test AUC:', init_test_auc)
    print('Minimum test AUC to continue the search: %.4f' % min_auc)
    
    current_auc = init_test_auc
    
    best = pd.DataFrame()
    best = best.append({'n_features':len(features), 
                        'train_auc':init_train_auc,
                        'test_auc': init_test_auc}, ignore_index = True)
    # Only proceed feature selection if test auc is above threshold
    while current_auc >= min_auc:
        print("Trying to remove one feature...")
        result = pd.DataFrame()
        n_workers = 8
        pool = multiprocessing.Pool(n_workers)
        worker_results = []
        for i, _ in enumerate(features):
            reduced = [features[j] for j in range(len(features)) if j != i]
            worker_results.append(pool.apply_async(worker, [reduced, data, test]))
            print('Worker[%d]: Trying to remove %s' % (i, features[i]))
        pool.close()
        print("Waiting for the workers to finish...")
        for i, res in enumerate(worker_results):
            print(f"Return value from worker {i} is", res.get())
            result = result.append({'feature': features[i], **res.get()}, ignore_index = True)
            #print(f"Worker {i} => DONE")
        print(result)
        result = result.sort_values(by = 'test_auc', ascending = False)
        current_metrics = result.iloc[0]
        best = best.append({'n_features':len(features) - 1, 
                            **current_metrics}, ignore_index = True)
        current_auc = current_metrics['test_auc']
        features = result.iloc[1:].feature.values
        
        print("Highest test AUC = %.4f" % current_auc)
        print("%s will be removed" % result.iloc[0].feature)
        print('Features left (%d):' % (len(features)))
        for f in features:
            print(f)
        print("AUC table begins".center(40, '='))
        print(result)
        print("AUC table ends".center(40, '='))
        
        fig = plot_auc_chart({'train_auc': init_train_auc,
                              'test_auc': init_test_auc}, result)
        fig.savefig('../models/test/auc_%d.png' % (len(features)), bbox_inches = "tight")
        
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
        train = train.sample(4000000)
        test = test.sample(1000000)
    
    features = ['dr', 'dz', 'cosaXY', 'min_dr', 'min_dz', 'pt', 'pz', 'chiProb', 
            'proton_PIDppi', 'proton_PIDpk', 'proton_PIDkpi', 'proton_p',
            'pi_PIDppi', 'pi_PIDpk', 'pi_PIDkpi', 'pi_p']
    print('Starting off with %d features' % len(features))
    
    best = backward_selection(features, train, test)
    print("Best AUC for each number of features")
    print(best)
    
    # Make a plot
    fig = plt.figure()
    plt.plot(best.n_features, 1 - best.train_auc, label = 'Train')
    plt.plot(best.n_features, 1 - best.test_auc, label = 'Test')
    plt.xlabel('Number of features')
    plt.ylabel('1 - AUC')
    plt.legend()
    fig.savefig('../models/test/best.png', bbox_inches = "tight")
    
