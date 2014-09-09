# -*- coding: utf-8 -*-
"""
Created on Sat Aug 30 19:31:07 2014

@author: francesco
"""
import numpy as np
import pandas as pd
from sklearn import preprocessing
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
#from sklearn.ensemble import BaggingRegressor
from sklearn.ensemble import AdaBoostRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestClassifier
from sklearn import neighbors
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.svm import SVR
from sklearn.svm import SVC
import operator


def loadDatasets(path_directory): 
    """
    import into dataframe all datasets saved in path_directory
    """
    
    name = path_directory + '/sp.csv'
    sp = pd.read_csv(name, index_col=0, parse_dates=True)
    
    name = path_directory + '/nasdaq.csv'
    nasdaq = pd.read_csv(name, index_col=0, parse_dates=True)
    
    name = path_directory + '/djia.csv'
    djia = pd.read_csv(name, index_col=0, parse_dates=True)
    
    name = path_directory + '/treasury.csv'
    treasury = pd.read_csv(name, index_col=0, parse_dates=True)
    
    name = path_directory + '/hkong.csv'
    hkong = pd.read_csv(name, index_col=0, parse_dates=True)
    
    name = path_directory + '/frankfurt.csv'
    frankfurt = pd.read_csv(name, index_col=0, parse_dates=True)
    
    name = path_directory + '/paris.csv'
    paris = pd.read_csv(name, index_col=0, parse_dates=True)
    
    name = path_directory + '/nikkei.csv'
    nikkei = pd.read_csv(name, index_col=0, parse_dates=True)
    
    name = path_directory + '/london.csv'
    london = pd.read_csv(name, index_col=0, parse_dates=True)
    
    name = path_directory + '/australia.csv'
    australia = pd.read_csv(name, index_col=0, parse_dates=True)
    
    return [sp, nasdaq, djia, treasury, hkong, frankfurt, paris, nikkei, london, australia]


def count_missing(dataframe):
    """
    count number of NaN in dataframe
    """
    return (dataframe.shape[0] * dataframe.shape[1]) - dataframe.count().sum()

    
def addFeatures(dataframe, adjclose, returns, n):
    """
    operates on two columns of dataframe:
    - n >= 2
    - given Return_* computes the return of day i respect to day i-n. 
    - given AdjClose_* computes its moving average on n days

    """
    
    return_n = adjclose[9:] + "Time" + str(n)
    dataframe[return_n] = dataframe[adjclose].pct_change(n)
    
    roll_n = returns[7:] + "RolMean" + str(n)
    dataframe[roll_n] = pd.rolling_mean(dataframe[returns], n)
    
def mergeDataframes(datasets, index, target):
    """
    merges datasets in the list 
    """
    subset = []
    subset = [dataset.iloc[:, index:] for dataset in datasets[1:]]
    
    if target == 'CLASSIFICATION':    
        return datasets[0].iloc[:, index:].join(subset, how = 'outer')
    elif target == 'REGRESSION':
        return datasets[0].iloc[:, index:].join(subset, how = 'outer')          
        
    
def applyTimeLag(dataset, lags, delta, back, target):
    """
    apply time lag to return columns selected according  to delta.
    Days to lag are contained in the lads list passed as argument.
    Returns a NaN free dataset obtained cutting the lagged dataset
    at head and tail
    """
    
    if target == 'CLASSIFICATION':
        maxLag = max(lags)

        columns = dataset.columns[::(2*max(delta)-1)]
        for column in columns:
            for lag in lags:
                newcolumn = column + str(lag)
                dataset[newcolumn] = dataset[column].shift(lag)

        return dataset.iloc[maxLag:-1,:]
    elif target == 'REGRESSION':
        maxLag = max(lags)
        
        columns = dataset.columns[::(2*max(delta)-1)]
        for column in columns:
            for lag in lags:
                newcolumn = column + str(lag)
                dataset[newcolumn] = dataset[column].shift(lag)

        return dataset.iloc[maxLag:-1,:]       


def performCV(dataset, folds, split, features, method, parameters):
    """
    given complete dataframe, number of folds, the % split to generate 
    train and test set and features to perform prediction --> splits
    dataframein test and train set. Takes train set and splits in k folds.
    - Train on fold 1, test on 2
    - Train on fold 1-2, test on 3
    - Train on fold 1-2-3, test on 4
    ....
    returns mean of test accuracies
    """
    index = int(np.floor(dataset.shape[0]*split))
    tobetested = dataset[:index]
    print ''
    print 'Parameters --------------------------------> ', parameters
    print 'Size train set: ', tobetested.shape
    k = int(np.floor(float(tobetested.shape[0])/folds))
    print 'Size of each fold: ', k
    acc = np.zeros(folds-1)
    for i in range(2, folds+1):
        split = float(i-1)/i
        print 'Splitting the first ' + str(i) + ' chuncks at ' + str(i-1) + '/' + str(i) 
        data = tobetested[:(k*i)]
        print 'Size of train+test: ', data.shape
        acc[i-2] = performClassification(data, features, split, method, parameters)
        print 'Accuracy on fold ' + str(i) + ': ', acc[i-2]
    return acc.mean()   

def performTimeSeriesSearchGrid(dataset, folds, split, features, method, grid):
    """
    parameters is a dictionary with: keys --> parameter , values --> list of values of parameter
    """
    print ''
    print 'Performing Search Grid CV...'
    print 'Algorithm: ', method
    param = grid.keys()
    finalGrid = {}
    if len(param) == 1:
        for value_0 in grid[param[0]]:
            parameters = [value_0]
            accuracy = performCV(dataset, folds, split, features, method, parameters)
            finalGrid[accuracy] = parameters
        final = sorted(finalGrid.iteritems(), key=operator.itemgetter(0), reverse=True)  
        print ''
        print 'Final CV Results: ', final        
        return final[0]
        
    elif len(param) == 2:
        for value_0 in grid[param[0]]:
            for value_1 in grid[param[1]]:
                parameters = [value_0, value_1]
                accuracy = performCV(dataset, folds, split, features, method, parameters)
                finalGrid[accuracy] = parameters
        final = sorted(finalGrid.iteritems(), key=operator.itemgetter(0), reverse=True)
        print ''
        print 'Final CV Results: ', final
        return final[0]
        
        
###############################################################################    
###############################################################################    
###############################################################################
######## CLASSIFICATION    
    
def prepareDataForClassification(dataset):
    """
    generates categorical to be predicted column, attach to dataframe 
    and label the categories
    """
    le = preprocessing.LabelEncoder()
        
    dataset['UpDown'] = dataset['Return_SP500']
    dataset.UpDown[dataset.UpDown >= 0] = 'Up'
    dataset.UpDown[dataset.UpDown < 0] = 'Down'
    dataset.UpDown = le.fit(dataset.UpDown).transform(dataset.UpDown)
    features = dataset.columns[1:-1]

    return dataset, features    


  
def performClassification(dataset, features, split, method, parameters):
    """
    performs classification on returns using serveral algorithms
    """
    index = int(np.floor(dataset.shape[0]*split))
    train, test = dataset[:index], dataset[index:]
    print ''
    print 'Performing Classification...'    
    print 'Size of train set: ', train.shape
    print 'Size of test set: ', test.shape
   
    if method == 'RF':   
        return performRFClass(train, test, features)
    elif method == 'KNN':
        return performKNNClass(train, test, features)
    elif method == 'SVM':   
        return performSVMClass(train, test, features)
    elif method == 'ADA':
        return performAdaBoostClass(train, test, features, parameters)
    elif method == 'GTB': 
        return performGTBClass(train, test, features)

    
def performRFClass(train, test, features):
    """
    Random Forest Binary Classification
    """
    forest = RandomForestClassifier(n_estimators=100, n_jobs=-1)
    forest = forest.fit(train[features], train['UpDown'])
    accuracy = forest.score(test[features],test['UpDown'])
    return accuracy
        
def performKNNClass(train, test, features):
    """
    KNN binary Classification
    """
    model = neighbors.KNeighborsClassifier()
    model.fit(train[features], train['UpDown']) 
    accuracy = model.score(test[features],test['UpDown'])
    return accuracy

def performSVMClass(train, test, features):
    """
    SVM binary Classification
    """
    mod = svm.SVC()
    mod.fit(train[features], train['UpDown'])  
    accuracy = mod.score(test[features], test['UpDown'])
    return accuracy    
    
def performAdaBoostClass(train, test, features, parameters):
    """
    Ada Boosting binary Classification
    """
    n = parameters[0]
    l =  parameters[1]
    mod = AdaBoostClassifier(n_estimators = n, learning_rate = l)
    mod.fit(train[features], train['UpDown'])  
    accuracy = mod.score(test[features], test['UpDown'])
    return accuracy
    
def performGTBClass(train, test, features):
    """
    Gradient Tree Boosting binary Classification
    """
    mod = GradientBoostingClassifier(n_estimators=100)
    mod.fit(train[features], train['UpDown'])  
    accuracy = mod.score(test[features], test['UpDown'])  
    return accuracy


##############################################################################
##############################################################################
##############################################################################   
##############################################################################
####### REGRESSION
    
def performRegression(dataset, split):
    """
    performs regression on returns using serveral algorithms
    """

    features = dataset.columns[1:]
    index = int(np.floor(dataset.shape[0]*split))
    train, test = dataset[:index], dataset[index:]
    print 'Size of train set: ', train.shape
    print 'Size of test set: ', test.shape
    
    output = 'Return_SP500'

    #print 'Accuracy RFC: ', performRFReg(train, test, features, output)
   
    #print 'Accuracy SVM: ', performSVMReg(train, test, features, output)
   
    #print 'Accuracy BAG: ', performBaggingReg(train, test, features, output)
   
    #print 'Accuracy ADA: ', performAdaBoostReg(train, test, features, output)
   
    #print 'Accuracy BOO: ', performGradBoostReg(train, test, features, output)

    print 'Accuracy KNN: ', performKNNReg(train, test, features, output)


def performRFReg(train, test, features, output):
    """
    Random Forest Regression
    """

    forest = RandomForestRegressor(n_estimators=100, n_jobs=-1)
    forest = forest.fit(train[features], train[output])
    Predicted = forest.predict(test[features])
    

    plt.plot(test[output])
    plt.plot(Predicted, color='red')
    plt.show()        
    
    return mean_squared_error(test[output], Predicted), r2_score(test[output], Predicted)

def performSVMReg(train, test, features, output):
    """
    SVM Regression
    """

    clf = SVR()
    clf.fit(train[features], train[output])
    Predicted = clf.predict(test[features])
    
    plt.plot(test[output])
    plt.plot(Predicted, color='red')
    plt.show()        
    
    return mean_squared_error(test[output],Predicted), r2_score(test[output], Predicted)
    
def performBaggingReg(train, test, features, output):
    """
    Bagging Regression
    """
  
    clf = BaggingRegressor()
    clf.fit(train[features], train[output])
    Predicted = clf.predict(test[features])
    
    plt.plot(test[output])
    plt.plot(Predicted, color='red')
    plt.show()        
    
    return mean_squared_error(test[output],Predicted), r2_score(test[output], Predicted)  

def performAdaBoostReg(train, test, features, output):
    """
    Ada Boost Regression
    """

    clf = AdaBoostRegressor()
    clf.fit(train[features], train[output])
    Predicted = clf.predict(test[features])
    
    plt.plot(test[output])
    plt.plot(Predicted, color='red')
    plt.show()        
    
    return mean_squared_error(test[output],Predicted), r2_score(test[output], Predicted)

def performGradBoostReg(train, test, features, output):
    """
    Gradient Boosting Regression
    """
    
    clf = GradientBoostingRegressor()
    clf.fit(test[features], train[output])
    Predicted = clf.predict(test[features])
    
    plt.plot(test[output])
    plt.plot(Predicted, color='red')
    plt.show()    
    
    return mean_squared_error(test[output],Predicted), r2_score(test[output], Predicted)

def performKNNReg(train, test, features, output):
    """
    KNN Regression
    """

    clf = KNeighborsRegressor()
    clf.fit(train[features], train[output])
    Predicted = clf.predict(test[features])
    
    plt.plot(test[output])
    plt.plot(Predicted, color='red')
    plt.show()        
    
    return mean_squared_error(test[output],Predicted), r2_score(test[output], Predicted)

