from dash import Dash, dcc, html, Input, Output, dcc, dash_table
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import pandas as pd

df = pd.read_csv('data.csv')

app = Dash(__name__)

# Filter the data by removing rows with 'PRIM_CONTRIBUTORY_CAUSE' equal to 'UNABLE TO DETERMINE'
# and group by 'PRIM_CONTRIBUTORY_CAUSE'
df_filtered = df[(df['PRIM_CONTRIBUTORY_CAUSE'] != 'UNABLE TO DETERMINE') & 
                 (df['PRIM_CONTRIBUTORY_CAUSE'] != 'NOT APPLICABLE') & 
                 (df['LIGHTING_CONDITION'] != 'UNKNOWN') & 
                 (df['WEATHER_CONDITION'] != 'UNKNOWN') & 
                 (df['WEATHER_CONDITION'] != 'OTHER')]
injury_cols = ['INJURIES_NO_INDICATION','INJURIES_NON_INCAPACITATING', 'INJURIES_INCAPACITATING','INJURIES_FATAL']
df_grouped_by_cause = df_filtered.groupby('PRIM_CONTRIBUTORY_CAUSE')[injury_cols].sum().sort_values(by=injury_cols, ascending=False)

df_grouped_by_sec_cause = df_filtered[(df_filtered['SEC_CONTRIBUTORY_CAUSE'] != 'UNABLE TO DETERMINE') & 
                 (df_filtered['SEC_CONTRIBUTORY_CAUSE'] != 'NOT APPLICABLE')].groupby(['PRIM_CONTRIBUTORY_CAUSE','SEC_CONTRIBUTORY_CAUSE'])['INJURIES_FATAL'].sum()

df_grouped_by_weather_count = df[(df['WEATHER_CONDITION'] == 'CLEAR') | 
                               (df['WEATHER_CONDITION'] == 'RAIN') | 
                               (df['WEATHER_CONDITION'] == 'SNOW')].groupby('WEATHER_CONDITION').size().sort_values()
df_grouped_by_weather_count['CLEAR'] = df_grouped_by_weather_count['CLEAR'] / 218
df_grouped_by_weather_count['RAIN'] = df_grouped_by_weather_count['RAIN'] / 119
df_grouped_by_weather_count['SNOW'] = df_grouped_by_weather_count['SNOW'] / 27.8

df_grouped_by_damage = df.groupby(['FIRST_CRASH_TYPE','DAMAGE']).size()

app.layout = html.Div([
    dash_table.DataTable(
        df.head(500).to_dict('records'), 
        [{"name": i, "id": i} for i in df.columns],
        page_size=10
    ),
    html.H1('Analyze the types of injuries that are most common in crashes and identify factors that contribute to more severe injuries.'),
    html.Table(
            children=[
                html.Tr([html.Th('Column'), html.Th('Sum')]),
                html.Tr([html.Td('INJURIES_FATAL'), html.Td(df['INJURIES_FATAL'].sum())]),
                html.Tr([html.Td('INJURIES_INCAPACITATING'), html.Td(df['INJURIES_INCAPACITATING'].sum())]),
                html.Tr([html.Td('INJURIES_NON_INCAPACITATING'), html.Td(df['INJURIES_NON_INCAPACITATING'].sum())]),
                html.Tr([html.Td('INJURIES_NO_INDICATION'), html.Td(df['INJURIES_NO_INDICATION'].sum())]),
            ]
        ),
    html.H2('By cause'),
    dcc.Graph(figure=px.bar(df_grouped_by_cause, text_auto=True, height=1000)),
    html.H1('Analyze whether crashes are more likely to occur at certain times of day / day of the week / month.'),
    dcc.Dropdown(
        id='time-model-select',
        options=[
            {'label': 'Month', 'value': 'CRASH_MONTH'},
            {'label': 'Day of week', 'value': 'CRASH_DAY_OF_WEEK'},
            {'label': 'Hour', 'value': 'CRASH_HOUR'}
        ],
        value='CRASH_MONTH'
    ),
    dcc.Graph(id='time-output'),
    html.H1('Find common root cause leading to fatal'),
    html.H2('For PHYSICAL CONDITION OF DRIVER'),
    dcc.Graph(figure=px.bar(df_grouped_by_sec_cause['PHYSICAL CONDITION OF DRIVER'], text_auto=True, height=1000)),
    html.H2('For PHYSICAL FAILING TO YIELD RIGHT-OF-WAY'),
    dcc.Graph(figure=px.bar(df_grouped_by_sec_cause['FAILING TO YIELD RIGHT-OF-WAY'], text_auto=True, height=1000)),

    html.H1('Correlation between weather conditions and number of incidents'),
    html.P('Sunny days: aprox 218'),
    html.P('Rainy days: aprox 119'),
    html.P('Snowy days: aprox 27.8'), 
    dcc.Graph(figure=px.bar(df_grouped_by_weather_count, labels={
                "value": "Incidents / day"
            })),
    html.H1('Damage depending on collision type'),
    dcc.Dropdown(
        id='colission-select',
        options=[
             {'label': col, 'value': col} for col in df['FIRST_CRASH_TYPE'].unique()
        ],
        value=df['FIRST_CRASH_TYPE'].unique()[0]
    ),
    dcc.Graph(id='damage-output'),
])

@app.callback(
    Output('time-output', 'figure'),
    [Input('time-model-select', 'value')]
)
def update_time_plot(variable):
    grouped = df.groupby(variable).size()
    fig = px.scatter(x=grouped.index, y=grouped.values, trendline="ols")
                    
    fig.update_layout(transition_duration=500)

    return fig

@app.callback(
    Output('damage-output', 'figure'),
    [Input('colission-select', 'value')]
)
def update_damage_plot(variable):
    fig = px.pie(df_grouped_by_damage[variable], names=df_grouped_by_damage[variable].index, values=df_grouped_by_damage[variable].values)
                    
    fig.update_layout(transition_duration=500)

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)