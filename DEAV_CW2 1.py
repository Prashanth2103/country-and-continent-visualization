# (i).
import pandas as pd
# Loading both the datasets i.e., reading both the csv files and assigning them to a new variable
oxcgrt_df = pd.read_csv(r"C:\Users\Sneha\Downloads\OxCGRT_summary20200520.csv")
country_continent_df = pd.read_csv(r"C:\Users\Sneha\Downloads\country-and-continent.csv")
# Merging the read datasets together on Countrycode
merged_df = pd.merge(oxcgrt_df, country_continent_df, on='CountryCode', how='left')
# silling the missing values after merging
merged_df['Continent_Name'].fillna('Europe', inplace=True)


# ---------------------------------------------------------------------------------------------------------------------------

# (ii).

# Fill missing values of ConfirmedCases and ConfirmedDeaths with the value from the previous row by filling backward
merged_df['ConfirmedCases'] = merged_df['ConfirmedCases'].fillna(method='bfill')
merged_df['ConfirmedDeaths'] = merged_df['ConfirmedDeaths'].fillna(method='bfill')


merged_df['Date'] = pd.to_datetime(merged_df['Date'], format='%Y%m%d', errors='coerce', cache=True).dt.date
# checking for any remaining missing values
print(merged_df.isnull().sum())

# ---------------------------------------------------------------------------------------------------------------------------

# (iii).
import plotly.express as px
merged_df = merged_df.sort_values(by='Date')
fig = px.scatter_geo(merged_df, locations="CountryCode", color="Continent_Name",
 hover_name="CountryName",size="ConfirmedCases", size_max=80,  #size_max is used to view the size of the bubble
 animation_frame=merged_df['Date'],     
 projection="natural earth",
 opacity=0.6) 
fig.update_layout(title_text = 'World population',title_x=0.5)
fig.write_html('./bubble1.html', auto_open=True) 


# ---------------------------------------------------------------------------------------------------------------------------

# (v).
import plotly.graph_objects as go

# Defining  token
token = 'pk.eyJ1IjoiZGF0YXZpczIwMjAiLCJhIjoiY2thM25hemdjMDBuODNlbWJ0NDFwNzlsdiJ9.hCZMoKtMjkURkO2_6u7eQw'

# Defining locations and their coordinates
locations = {
    "London": [51.5074, -0.1278],
    "Dover": [51.1256, 1.3111],
    "Calais": [50.9513, 1.8587],
    "Charles de Gaulle Airport": [49.0097, 2.5479],
    "Istanbul Airport": [41.2753, 28.7519]
}

# Creating a new DataFrame for the locations
journey_df = pd.DataFrame(locations).T.reset_index()
journey_df.columns = ['Location', 'Lat', 'Lon']

# Plotting the journey on a map by assigning the lon and lat
fig = go.Figure(go.Scattermapbox(
    mode = "markers+lines",
    lon = journey_df['Lon'],
    lat = journey_df['Lat'],
    marker = {'size': 15, 'symbol': ['car','harbor','car','airport','airport']}, 
    text = ['car','harbor','car','airport','airport']
))

fig.update_layout(
    mapbox = {
        'accesstoken': token,
        'style': "mapbox://styles/mapbox/streets-v11",
        'center': {'lon': 13, 'lat': 48},
        'zoom': 4.5},
    showlegend = False)

fig.write_html('./ Landmarks.html', auto_open=True) 

# ----------------------------------------------------------------------------------------------------------------------

# (iv).
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

merged_df['CountryName'] = merged_df['CountryName'].astype(str)

app = Dash(__name__)

# Layout of the dashboard
app.layout = html.Div([
    html.Div([
        html.Label("Scope"),
        dcc.Dropdown(id='scope-dropdown',
                     options=[
                         {'label': 'World', 'value': 'World'},
                         {'label': 'Asia', 'value': 'Asia'},
                         {'label': 'Africa', 'value': 'Africa'},
                         {'label': 'Europe', 'value': 'Europe'},
                         {'label': 'North America', 'value': 'North America'},
                         {'label': 'South America', 'value': 'South America'}
                     ],
                     value='World'),
        html.Label("Input Data"),
        dcc.RadioItems(id='data-input',
                       options=[{'label': 'Confirmed Cases', 'value': 'ConfirmedCases'},
                                {'label': 'Confirmed Deaths', 'value': 'ConfirmedDeaths'},
                                {'label': 'Stringency Index', 'value': 'StringencyIndex'}],
                       value='ConfirmedCases', className='radio-group'),
        html.Label("Policy"),
        dcc.RadioItems(id='policy',
                       options=[{'label': 'Not selected', 'value': 'NotSelected'},
                                {'label': 'School closing', 'value': 'School closing'},
                                {'label': 'Staying at home', 'value': 'Stay at home requirements'}],
                       value='NotSelected', className='radio-group'),
    ], className='control-panel', style={'display': 'inline-block', 'width': '20%', 'vertical-align': 'top'}),
    html.Div([
        dcc.Graph(id='line-graph')
    ], className='graph-container', style={'display': 'inline-block', 'width': '79%', 'vertical-align': 'top'}),
    html.Div([
        dcc.Graph(id='bubble-map')
    ], className='map-container', style={'display': 'inline-block', 'width': '100%', 'vertical-align': 'top'})
])

# Function to format data for the map
def format_map_data(df, scope, data_input, policy):
    filtered_df = df if scope == 'World' else df[df['Continent_Name'] == scope]

    if policy == 'NotSelected':
        return px.scatter_geo(filtered_df,
                              locations="CountryName",
                              locationmode="country names",
                              color="Continent_Name",
                              size=data_input,
                              hover_name="CountryName", animation_frame="Date",
                              title=f"{data_input} Over Time in {scope}")
    else:
        return px.choropleth(filtered_df,
                             locations="CountryName",
                             locationmode="country names",
                             color=policy,
                             hover_name="CountryName", animation_frame="Date",
                             title=f"{policy} Over Time in {scope}")

# Callbacks to update the map and line graph
@app.callback(
    Output('bubble-map', 'figure'),
    [Input('scope-dropdown', 'value'),
     Input('data-input', 'value'),
     Input('policy', 'value')]
)
def update_map(scope, data_input, policy):
    fig = format_map_data(merged_df, scope, data_input, policy)
    return fig

@app.callback(
    Output('line-graph', 'figure'),
    [Input('data-input', 'value'),
     Input('policy', 'value')]
)
def update_line_graph(data_input, policy):
    top5_countries = merged_df.groupby('CountryName')[data_input].max().nlargest(5).index
    filtered_df = merged_df[merged_df['CountryName'].isin(top5_countries)]

    fig = px.line(filtered_df, x='Date', y=data_input, color='CountryName',
                  title=f'Top 5 Countries by {data_input}')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
    


