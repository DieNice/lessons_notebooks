import pandas as pd
from datetime import date
import os
import dash
from dash import html
from dash import dcc
import plotly.express as px
from dash.dependencies import Input, Output
from dash import dash_table
from queries import query_1, query_2, query_tab
import os
from dotenv import load_dotenv
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from pandas import DataFrame
import numpy as np
from psycopg2 import OperationalError, connect
from psycopg2.extensions import connection


def create_connection(db_name: str, db_user: str, db_password: str, db_host: str, db_port: int) -> connection:
    """Создание соединения

    Args:
        db_name (str): Название БД
        db_user (str): Пользователь
        db_password (str): Пароль к БД
        db_host (str): Адрес БД
        db_port (int): Порт БД

    Returns:
        connection: Соединение
    """
    connection = None
    try:
        connection = connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection


def get_df_from_sql(query: str, conn: connection) -> DataFrame:
    """Получить DataFrame

    Args:
        query (str): SQL запрос
        conn (connection): Соединение

    Returns:
        DataFrame: DataFrame
    """
    return pd.read_sql(query, conn)


def generate_options() -> np.array:
    """Генерация значений для мультифильтра
    """
    _conn = create_connection(os.getenv("DB_NAME"),
                              os.getenv("DB_USER"),
                              os.getenv("DB_PASSWORD"),
                              os.getenv("DB_HOST"),
                              5432)
    df_pie = get_df_from_sql(query_1, _conn)
    _conn.close()
    options = df_pie["aircraft_code"].unique()
    return options


def generate_options_status() -> np.array:
    """Генерация значений для группы чекбоксов
    """
    _conn = create_connection(os.getenv("DB_NAME"),
                              os.getenv("DB_USER"),
                              os.getenv("DB_PASSWORD"),
                              os.getenv("DB_HOST"),
                              5432)
    df_tab = get_df_from_sql(query_tab, _conn)
    _conn.close()
    options_status = df_tab["status"].unique()
    return options_status


def multi_filter() -> dcc.Dropdown:
    """Компонент мультифильтр
    """
    return dcc.Dropdown(
        id="multi-filter-id",
        options=generate_options(),
        value=generate_options(),
        multi=True)


def group_checkboxes() -> dcc.Checklist:
    """Компонент группа чекбоксов
    """
    return dcc.Checklist(
        id="group-checkboxes-id",
        options=generate_options_status(),
        value=generate_options_status())


def time_selector() -> dcc.DatePickerRange:
    """Компонент выбор диапазона дат
    """
    return dcc.DatePickerRange(
        id="time-selector-id",
        display_format="DD.MM.YYYY",
        min_date_allowed=date(2016, 1, 1),
        max_date_allowed=date.today(),
        start_date=date(2016, 1, 1),
        end_date=date.today())


def tab2_content() -> dbc.Row:
    """Компонент таблица
    """
    return dbc.Row(html.Div(id="data-table-id"))


def main_layout() -> html.Div:
    """Главный компонент
    """
    return html.Div([
        html.Div([
            html.Div([html.Div("Выберите модель самолёта"), html.Div(
                multi_filter(), style={"width": "400px", "margin-bottom": "40px"})]),
            html.Div([html.Div("Выберите статус рейса: "), html.Div(
                group_checkboxes())], style={"margin-left": "40px"}),
            html.Div([html.Div("Выберите даты рейса: "), html.Div(
                time_selector())], style={"margin-left": "40px"})
        ], style={"display": "flex", "justify-content": "center"}),

        html.Div([dcc.Graph(id="hist"), dcc.Graph(id="pie")], style={
            "display": "flex", "justify-content": "center", "height": "40vh"}),
        html.Div([html.Div([html.Div("Количество рейсов:"),
                            html.Div([], id="number_flights")],
                           style={"display": "flex", "flex-direction": "column", "align-items": "center", "justify-content": "center", "margin-right": "50px"}),
                  html.Div(tab2_content(), style={"width": "1200px"})],
                 style={"display": "flex", "justify-content": "center", "padding-right": "150px"})
    ])

load_dotenv("env.txt" )
app = dash.Dash("my_first_app")




app.layout = main_layout()



@app.callback(
    Output(component_id="hist", component_property="figure"),
    Output(component_id="pie", component_property="figure"),
    Output(component_id="number_flights", component_property="children"),
    Output(component_id="data-table-id", component_property="children"),
    [Input(component_id="multi-filter-id", component_property="value"),
     Input(component_id="group-checkboxes-id", component_property="value"),
     Input(component_id="time-selector-id", component_property="start_date"),
     Input(component_id="time-selector-id", component_property="end_date")]
)
def update_dist_temp_chart(model_now, status_now, time_now_f, time_now_l):
    _conn = create_connection(os.getenv("DB_NAME"),
                              os.getenv("DB_USER"),
                              os.getenv("DB_PASSWORD"),
                              os.getenv("DB_HOST"),
                              5432)

    df = get_df_from_sql(query_2, _conn)
    df_pie = get_df_from_sql(query_1, _conn)
    df_tab = get_df_from_sql(query_tab, _conn)
    _conn.close()
    del df_tab["flight_id"]

    aircraft_data_hist = df[df["aircraft_code"].isin(model_now)]

    aircraft_data = df_pie[df_pie["aircraft_code"].isin(model_now)]

    my_data = pd.date_range(time_now_f, time_now_l)

    filter_aircraft = df_tab["aircraft_code"].isin(model_now) & \
        df_tab["status"].isin(status_now) &\
        (pd.to_datetime(df_tab["scheduled_arrival"]).dt.date).isin(
            pd.to_datetime(my_data).date)

    aircraft_data_tab = df_tab[filter_aircraft]

    if not aircraft_data_hist.empty:
        fig = px.histogram(aircraft_data_hist,
                           x=aircraft_data_hist["aircraft_code"],
                           y=aircraft_data_hist["range"],
                           color="aircraft_code",
                           title="Макс. дистанция полёта по модели самолёта",
                           labels={"aircraft_code": "Модель самолёта"}
                           )
        fig.update_layout(yaxis_title="Макс. дистанция полёта, км")
    else:
        fig = px.histogram(aircraft_data_hist,
                           x=[0],
                           y=[0],
                           title="Макс. дистанция полёта по модели самолёта",
                           labels={"aircraft_code": "Модель самолёта"}
                           )

    if not aircraft_data.empty:
        fig_pie = px.pie(aircraft_data,
                         names=aircraft_data["fare_conditions"],
                         values=aircraft_data["count1"])
    else:
        fixture_df = pd.DataFrame({"names": ["empty"],
                                   "values": [1]})
        fig_pie = px.pie(fixture_df,
                         names=fixture_df["names"],
                         values=fixture_df["values"]) 

    status_num = aircraft_data_tab["status"].count()

    table = dash_table.DataTable(data=aircraft_data_tab.to_dict("records"),
                                 columns=[{"name": i, "id": i}
                                          for i in df_tab.columns],
                                 page_size=10,
                                 sort_action='native',
                                 sort_mode='single',
                                 filter_action='native',
                                 style_data={
        "width": "50px",
        "maxWidth": "100px",
        "minWidth": "25px",
    })

    return fig, fig_pie, status_num, table


if __name__ == "__main__":
    app.run_server(debug=True)
