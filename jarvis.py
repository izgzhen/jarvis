import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
def ignore_warn(*args, **kwargs):
    pass
warnings.warn = ignore_warn #ignore annoying warning (from sklearn and seaborn)
warnings.filterwarnings('ignore')


from scipy import stats
from scipy.stats import norm, skew #for some statistics


pd.set_option('display.float_format', lambda x: '{:.3f}'.format(x))

def read(path: str):
    if path.endswith(".csv"):
        return pd.read_csv(path)

from IPython import get_ipython
from IPython.display import display, Markdown
ipy = get_ipython()
ipy.magic('matplotlib inline')

from sklearn.preprocessing import LabelEncoder

## EDA

def peek(df):
    display(Markdown('## Shape: {}'.format(df.shape)))
    display(Markdown('## First 10 rows:'))
    display(df.head(10))
    display(Markdown('## Description of columns'))
    display(df.describe())

def scatter(df, x: str, y: str):
    fig, ax = plt.subplots()
    ax.scatter(x = df[x], y = df[y])
    plt.ylabel(x, fontsize=13)
    plt.xlabel(y, fontsize=13)
    plt.show()

def dist(df, col_name):
    df_col = df[col_name]
    sns.distplot(df_col, fit=norm);
    (mu, sigma) = norm.fit(df_col)
    display(Markdown('### mu = {:.2f} and sigma = {:.2f}'.format(mu, sigma)))
    plt.legend(['Normal dist. ($\mu=$ {:.2f} and $\sigma=$ {:.2f} )'.format(mu, sigma)],
               loc='best')
    plt.ylabel('Frequency')
    plt.title('{} distribution'.format(col_name))
    fig = plt.figure()
    stats.probplot(df_col, plot=plt)
    plt.show()

def log_transform(df, target):
    df[target] = np.log1p(df[target])

## Feature engineering

def concat(df_train, df_test, target):
    all_data = pd.concat((df_train, df_test))
    all_data.drop(target, axis=1, inplace=True)
    display(Markdown("### all_data size is : {}".format(all_data.shape)))
    return all_data

def check_missing(all_data, n = 20):
    all_data_na = (all_data.isnull().sum() / len(all_data)) * 100
    all_data_na = all_data_na.drop(all_data_na[all_data_na == 0].index)
    all_data_na = all_data_na.sort_values(ascending=False)[:n]
    if all_data_na.size == 0:
        display(Markdown('### No missing data'))
        return
    missing_data = pd.DataFrame({'Missing Ratio' : all_data_na})
    display(missing_data.head(n))
    f, ax = plt.subplots(figsize=(15, 12))
    plt.xticks(rotation='90')
    sns.barplot(x=all_data_na.index, y=all_data_na)
    plt.xlabel('Features', fontsize=15)
    plt.ylabel('Percent of missing values', fontsize=15)
    plt.title('Percent missing data by feature', fontsize=15)

def corr(df):
    corrmat = df.corr()
    plt.subplots(figsize=(12,9))
    sns.heatmap(corrmat, vmax=0.9, square=True)

def fillna_group_mean(all_data, group: str, name: str):
    all_data[name] = all_data.groupby(group)[name].transform(lambda x: x.fillna(x.median()))

def label_encode(all_data, name):
    lbl = LabelEncoder()
    lbl.fit(list(all_data[name].values))
    all_data[name] = lbl.transform(list(all_data[name].values))

def get_skewness(all_data):
    numeric_feats = all_data.dtypes[all_data.dtypes != "object"].index
    skewed_feats = all_data[numeric_feats].apply(lambda x: skew(x.dropna())).sort_values(ascending=False)
    display(Markdown("### Skew in numerical features:"))
    skewness = pd.DataFrame({'Skew' :skewed_feats})
    display(skewness.head(10))
    return skewness

def remove_skew_coxbox(all_data, skewness, lmbda=0.15, threshold=0.75):
    from scipy.special import boxcox1p
    skewness = skewness[abs(skewness) > threshold]
    skewed_features = skewness.index
    for feat in skewed_features:
        all_data[feat] = boxcox1p(all_data[feat], lmbda)

## Models

from sklearn.linear_model import ElasticNet, Lasso,  BayesianRidge, LassoLarsIC
from sklearn.ensemble import RandomForestRegressor,  GradientBoostingRegressor
from sklearn.kernel_ridge import KernelRidge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler
from sklearn.base import BaseEstimator, TransformerMixin, RegressorMixin, clone
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error
import xgboost as xgb
import lightgbm as lgb


def rmsle_cv(model, df_train, y_train, n_folds=5):
    kf = KFold(n_folds, shuffle=True, random_state=42).get_n_splits(df_train.values)
    rmse = np.sqrt(-cross_val_score(model, df_train.values, y_train,
                   scoring="neg_mean_squared_error", cv = kf, n_jobs=-1))
    return rmse

lasso = make_pipeline(RobustScaler(), Lasso(alpha =0.0005, random_state=1))
ENet = make_pipeline(RobustScaler(), ElasticNet(alpha=0.0005, l1_ratio=.9, random_state=3))
KRR = KernelRidge(alpha=0.6, kernel='polynomial', degree=2, coef0=2.5)
GBoost = GradientBoostingRegressor(n_estimators=3000, learning_rate=0.05,
                                   max_depth=4, max_features='sqrt',
                                   min_samples_leaf=15, min_samples_split=10,
                                   loss='huber', random_state =5)
model_xgb = xgb.XGBRegressor(colsample_bytree=0.4603, gamma=0.0468,
                             learning_rate=0.05, max_depth=3,
                             min_child_weight=1.7817, n_estimators=2200,
                             reg_alpha=0.4640, reg_lambda=0.8571,
                             subsample=0.5213, silent=1,
                             random_state =7, nthread = -1)
model_lgb = lgb.LGBMRegressor(objective='regression',num_leaves=5,
                              learning_rate=0.05, n_estimators=720,
                              max_bin = 55, bagging_fraction = 0.8,
                              bagging_freq = 5, feature_fraction = 0.2319,
                              feature_fraction_seed=9, bagging_seed=9,
                              min_data_in_leaf =6, min_sum_hessian_in_leaf = 11)


class AveragingModels(BaseEstimator, RegressorMixin, TransformerMixin):
    def __init__(self, models):
        self.models = models

    # we define clones of the original models to fit the data in
    def fit(self, X, y):
        self.models_ = [clone(x) for x in self.models]

        # Train cloned base models
        for model in self.models_:
            model.fit(X, y)

        return self

    #Now we do the predictions for cloned models and average them
    def predict(self, X):
        predictions = np.column_stack([
            model.predict(X) for model in self.models_
        ])
        return np.mean(predictions, axis=1)

class StackingAveragedModels(BaseEstimator, RegressorMixin, TransformerMixin):
    def __init__(self, base_models, meta_model, n_folds=5):
        self.base_models = base_models
        self.meta_model = meta_model
        self.n_folds = n_folds

    # We again fit the data on clones of the original models
    def fit(self, X, y):
        self.base_models_ = [list() for x in self.base_models]
        self.meta_model_ = clone(self.meta_model)
        kfold = KFold(n_splits=self.n_folds, shuffle=True, random_state=156)

        # Train cloned base models then create out-of-fold predictions
        # that are needed to train the cloned meta-model
        out_of_fold_predictions = np.zeros((X.shape[0], len(self.base_models)))
        for i, model in enumerate(self.base_models):
            for train_index, holdout_index in kfold.split(X, y):
                instance = clone(model)
                self.base_models_[i].append(instance)
                instance.fit(X[train_index], y[train_index])
                y_pred = instance.predict(X[holdout_index])
                out_of_fold_predictions[holdout_index, i] = y_pred

        # Now train the cloned  meta-model using the out-of-fold predictions as new feature
        self.meta_model_.fit(out_of_fold_predictions, y)
        return self

    #Do the predictions of all base models on the test data and use the averaged predictions as
    #meta-features for the final prediction which is done by the meta-model
    def predict(self, X):
        meta_features = np.column_stack([
            np.column_stack([model.predict(X) for model in base_models]).mean(axis=1)
            for base_models in self.base_models_ ])
        return self.meta_model_.predict(meta_features)

def rmsle(y, y_pred):
    return np.sqrt(mean_squared_error(y, y_pred))