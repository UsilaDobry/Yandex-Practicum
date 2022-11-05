# Local resources
import functions
# Data Preprocessing
import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
# Data Visualisation
import plotly.express as px
import plotly.graph_objs as go
# Available templates: ['ggplot2', 'seaborn', 'simple_white', 'plotly', 'plotly_white', 'plotly_dark', 'presentation',
# 'xgridoff', 'ygridoff', 'gridon', 'none']
px.defaults.template = "plotly_dark"
# Statistical tools for time series analysis
from statsmodels.tsa.stattools import adfuller, kpss, acf, pacf
from statsmodels.tsa.seasonal import seasonal_decompose
# Algorithms ML
from sklearn.linear_model import RidgeCV, ElasticNetCV, LassoCV
from sklearn.ensemble import RandomForestRegressor
from lightgbm import LGBMRegressor
from statsmodels.tsa.statespace.sarimax import SARIMAX

#------------------------------------------------- ПОДГОТОВКА ДАННЫХ---------------------------------------------------

data = pd.read_csv('./datasets/taxi.csv')
# приведение данных к DateTimeIndex
df = pd.read_csv('./datasets/taxi.csv', parse_dates=[0], index_col=[0])
# понижение частоты временного ряда
df.sort_index()
df_resample = df.resample('1H').sum()
fig_freq_1h = px.line(df_resample, x=df_resample.index, y=df_resample['num_orders'], title='Частота ряда 1 час')
# декомпозиция временного ряда
decomposed = seasonal_decompose(df_resample, model='additive')
trend = decomposed.trend
trend = trend.dropna()
seasonal = decomposed.seasonal
observed = decomposed.observed
resid = decomposed.resid
# переводим серию в датафрейм
df_trend = trend.to_frame(name='trend')
df_seasonal = seasonal.to_frame(name='seasonal')
df_resid = resid.to_frame(name='resid')
df_observed = observed.to_frame(name='observed')
# графики декомпозиции
fig_trend = px.line(trend, x=trend.index, y=trend)
fig_seasonal = px.line(seasonal, x=seasonal.index, y=seasonal)
fig_resid = px.line(resid, x=resid.index, y=resid)
fig_observed = px.line(observed, x=observed.index, y=observed)
# проверка на стационарность
adf_test_series = functions.adf_test(df_resample)
adf_test = adf_test_series.reset_index()
adf_test = adf_test.rename(columns={'index':'поле', 0:'значение'})
# KPSS test
kpss_test_series = functions.kpss_test(df_resample)
kpss_test = kpss_test_series.reset_index()
kpss_test = kpss_test.rename(columns={'index':'поле', 0:'значение'})
# детрендированный временной ряд
non_trend = resid + observed + seasonal
df_non_trend = non_trend.to_frame(name='num_orders')
# дифференцированный временной ряд
df_diff = df_resample.copy()
df_diff['num_orders_diff'] = df_diff['num_orders'] - df_diff['num_orders'].shift(1)
df_diff['num_orders_diff'] = df_diff['num_orders_diff'].dropna()
df_diff = df_diff.drop('num_orders', axis=1)
# конструирование признаков
df_resample['month'] = df_resample.index.month
df_resample['hour'] = df_resample.index.hour
df_resample['dayofweek'] = df_resample.index.dayofweek
df_resample['rolling_mean_D'] = df_trend['trend'].rolling(24).mean()
df_resample['rolling_mean_W'] = df_trend['trend'].rolling(168).mean()
data_months = [df_resample['2018-03-01':'2018-03-31'], df_resample['2018-04-01':'2018-04-30'], df_resample['2018-05-01':'2018-05-31'],
               df_resample['2018-06-01':'2018-06-30'], df_resample['2018-07-01':'2018-07-31'], df_resample['2018-08-01':'2018-08-31']]
months = ['Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август']

#----------------------------------------------------АНАЛИЗ------------------------------------------------------------

fig_total_trand = px.line(df_resample, x=df_resample.index, y=df_resample.rolling_mean_D, title='Общая тенденция')
fig_total_trand.add_scatter(x=df_resample.index, y=df_resample.rolling_mean_W, mode='lines', name='weekly')
# заказы по времени
hour_group = df_resample.groupby('hour').agg(func=sum).sort_values(by='num_orders', ascending=False)
fig_hour = px.bar(hour_group, x=hour_group.index, y='num_orders', hover_data=['num_orders'], color='num_orders',
                  labels={'num_orders': 'Заказы такси', 'hour': 'часы'}, height=400, title='Распределение заказов по времени суток')
# заказы по дням недели
weekday_group = df_resample.groupby('dayofweek').agg(func=sum)
fig_week = px.bar(weekday_group, x=weekday_group.index, y='num_orders', hover_data=['num_orders'], color='num_orders',
                  labels={'num_orders': 'Заказы такси', 'dayofweek': 'дни недели'},
                  height=400, title='Распределение заказов по дням недели')
# заказы по месяцам
fig_month = go.Figure(layout=go.Layout(template='plotly_dark'))
fig_month.add_trace(go.Box(x=data_months[0].num_orders, name='март'))
fig_month.add_trace(go.Box(x=data_months[1].num_orders, name='апрель'))
fig_month.add_trace(go.Box(x=data_months[2].num_orders, name='май'))
fig_month.add_trace(go.Box(x=data_months[3].num_orders, name='июнь'))
fig_month.add_trace(go.Box(x=data_months[4].num_orders, name='июль'))
fig_month.add_trace(go.Box(x=data_months[5].num_orders, name='август'))
fig_month.update_layout(title='Сравнение количества заказов по месяцам', xaxis_title='Количество заказов')
# вычисление автокорреляции до дифференцирования
fig_acf = functions.create_corr_plot(df_resample.num_orders, plot_pacf=False)
fig_pacf = functions.create_corr_plot(df_resample.num_orders, plot_pacf=True)

#-------------------------------------------------ОБУЧЕНИЕ и ТЕСТИРОВАНИЕ----------------------------------------------
df_resample = df_resample.dropna()
df_dammies = pd.get_dummies(df_resample, columns=['month', 'hour', 'dayofweek'], drop_first=False)
# разделение данных на обучающую и тестовую выборки
train, test = train_test_split(df_dammies, test_size=0.2, shuffle=False, random_state=12345)
#train = train.dropna()
X_train = train.drop('num_orders', axis=1)
y_train = train['num_orders']
X_test = test.drop('num_orders', axis=1)
y_test = test['num_orders']
# масштабирование данных
sc = StandardScaler()
sc.fit(X_train)
X_train_std = sc.transform(X_train)
X_test_std = sc.transform(X_test)
# моделирование и обучение
tscv = TimeSeriesSplit(n_splits=11)
models = [RidgeCV(cv=tscv),
          LassoCV(cv=tscv),
          ElasticNetCV(cv=tscv),
          RandomForestRegressor(),
          LGBMRegressor()]
pred_train = []
pred_test = []
rmse_train = []
rmse_test = []
train_graphs = []
params = []

for m in models:
    # обучение
    m.fit(X_train_std, y_train)
    # прогноз на тренировочной выборке
    prediction_train = m.predict(X_train_std)
    # прогноз на тестовой выборке
    prediction_test = m.predict(X_test_std)
    # сохранение результатов прогнозирования
    pred_train.append(prediction_train)
    pred_test.append(prediction_test)
    # оценка прогнозирование
    rmse_train.append(round(np.sqrt(mean_squared_error(y_train, prediction_train))))
    rmse_test.append(round(np.sqrt(mean_squared_error(y_test, prediction_test))))
    # параметры модели
    params.append(pd.DataFrame.from_dict(m.get_params(), orient='index').reset_index().rename \
                        (columns={'index': 'параметр', 0: 'значение'}))
    # график обучения модели
    train_graphs.append(functions.plot_learning_curves(m, X_train_std, y_train, cv=tscv))

# сравнительная таблица
comparison_table = pd.DataFrame({
    'Model': ['RidgeCV', 'LassoCV', 'ElasticNetCV', 'RandomForestRegressor',
              'LGBMRegressor'],
    'RMSE train': [rmse_train[0], rmse_train[1], rmse_train[2], rmse_train[3], rmse_train[4]],
    'RMSE test': [rmse_test[0], rmse_test[1], rmse_test[2], rmse_test[3], rmse_test[4]]})
# удалим параметр 'cv' из таблиц параметров
for i in range(len(params)):
    params[i] = params[i][params[i]['параметр'] != 'cv']

# графики предсказаний
result_dfs = []
pred_graphs = []
for i in range(len(models)):
    result_dfs.append(pd.DataFrame(pred_test[i], index=y_test.index, columns=['pred_test']).merge(y_test, on='datetime'))
    fig = px.line(result_dfs[i], x=result_dfs[i].index, y=result_dfs[i].num_orders,
                  title='Предсказания на тестовой выборке ' + type(models[i]).__name__)
    fig.add_scatter(x=result_dfs[i].index, y=result_dfs[i].pred_test, mode='lines', name='pred_test')
    pred_graphs.append(fig)

