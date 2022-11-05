import pandas as pd
import numpy as np
import plotly.graph_objs as go
from statsmodels.tsa.stattools import adfuller, kpss, acf, pacf
from sklearn.model_selection import learning_curve
from sklearn.metrics import make_scorer, mean_squared_error

# анализ стационарности
# Dickey-Fuller Test
def adf_test(timeseries):
    dftest = adfuller(timeseries, autolag="AIC")
    dfoutput = pd.Series(
        dftest[0:4],
        index=[
            "Статистика теста",
            "p-value",
            "Используемые теги",
            "Количество использованных наблюдений",
        ],
    )
    for key, value in dftest[4].items():
        dfoutput["Критическое значение (%s)" % key] = value
    return dfoutput
# KPSS test
def kpss_test(timeseries):
    kpsstest = kpss(timeseries, regression="ct", nlags="auto")
    kpss_output = pd.Series(
        kpsstest[0:3], index=["Статистика теста", "p-value", "Используемые теги"]
    )
    for key, value in kpsstest[3].items():
        kpss_output["Критическое значение (%s)" % key] = value
    return kpss_output

# вычисление автокорреляции ACF, PACF
def create_corr_plot(series, plot_pacf=False):
    corr_array = pacf(series.dropna(), alpha=0.05) if plot_pacf else acf(series.dropna(), alpha=0.05)
    lower_y = corr_array[1][:, 0] - corr_array[0]
    upper_y = corr_array[1][:, 1] - corr_array[0]

    fig = go.Figure(layout=go.Layout(template='plotly_dark'))
    [fig.add_scatter(x=(x, x), y=(0, corr_array[0][x]), mode='lines', line_color='#3f3f3f')
     for x in range(len(corr_array[0]))]
    fig.add_scatter(x=np.arange(len(corr_array[0])), y=corr_array[0], mode='markers', marker_color='#1f77b4',
                    marker_size=12)
    fig.add_scatter(x=np.arange(len(corr_array[0])), y=upper_y, mode='lines', line_color='rgba(255,255,255,0)')
    fig.add_scatter(x=np.arange(len(corr_array[0])), y=lower_y, mode='lines', fillcolor='rgba(32, 146, 230,0.3)',
                    fill='tonexty', line_color='rgba(255,255,255,0)')
    fig.update_traces(showlegend=False)
    fig.update_xaxes(range=[-1, 40])
    fig.update_yaxes(zerolinecolor='#000000')

    title = 'Частичная автокорреляция (PACF)' if plot_pacf else 'Автокорреляция (ACF)'
    fig.update_layout(title=title)
    return fig
# построение графика кривой обучения
# график кривой обучения из scikit-learn
# def plot_learning_curve(estimator, title, X, y, ylim=None, cv=None,
#                         n_jobs=1, train_sizes=np.linspace(.1, 1.0, 5)):
#     '''
#     Функция рисует график кривой обучения модели
#     :param estimator:
#     :param title:
#     :param X:
#     :param y:
#     :param ylim:
#     :param cv:
#     :param n_jobs:
#     :param train_sizes:
#     :return:
#     '''
#     plt.figure()
#     plt.title(title)
#     if ylim is not None:
#         plt.ylim(*ylim)
#     plt.xlabel("Тренировочные данные")
#     plt.ylabel("Оценка")
#     train_sizes, train_scores, test_scores = learning_curve(
#         estimator, X, y, cv=cv, n_jobs=n_jobs, train_sizes=train_sizes, scoring=make_scorer(mean_squared_error))
#     train_scores_mean = np.mean(train_scores, axis=1)
#     train_scores_std = np.std(train_scores, axis=1)
#     test_scores_mean = np.mean(test_scores, axis=1)
#     test_scores_std = np.std(test_scores, axis=1)
#     plt.grid()
#
#     plt.fill_between(train_sizes, train_scores_mean - train_scores_std,
#                      train_scores_mean + train_scores_std, alpha=0.1,
#                      color="r")
#     plt.fill_between(train_sizes, test_scores_mean - test_scores_std,
#                      test_scores_mean + test_scores_std, alpha=0.1, color="g")
#     plt.plot(train_sizes, train_scores_mean, 'o-', color="r",
#              label="Train score")
#     plt.plot(train_sizes, test_scores_mean, 'o-', color="g",
#              label="C-V score")
#
#     plt.legend(loc="best")
#     return plt
def plot_learning_curves(estimator, X, y, cv):
    """
    Не забудьте изменить метки подсчета очков и сюжета
    на основе используемой вами метрики.
    """

    train_sizes, train_scores, test_scores = learning_curve(
        estimator=estimator,
        X=X,
        y=y,
        train_sizes=np.linspace(0.1, 1.0, 10),
        cv=cv,
        scoring=make_scorer(mean_squared_error),
        random_state=42
    )
    train_mean = np.mean(train_scores, axis=1)
    test_mean = np.mean(test_scores, axis=1)

    fig = go.Figure(layout=go.Layout(template='plotly_dark'))

    fig.add_trace(
        go.Scatter(
            x=train_sizes,
            y=train_mean,
            name="Оценка обучения",
            mode="lines",
            line=dict(color="blue"),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=train_sizes,
            y=test_mean,
            name="Оценка теста",
            mode="lines",
            line=dict(color="green"),
        )
    )

    fig.update_layout(
        title="График кривой обучения модели",
        xaxis_title="Количество обучающих примеров",
        yaxis_title="Mean_squared_error",
    )

    return fig