import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import geopandas as gpd
from shapely.wkt import loads
import plotly.express as px
from datetime import datetime
import base64
import pandas as pd
def some_function():
    from app import wsgi
    # Rest of the function

import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
from io import StringIO

# Replace 'YOUR_FILE_ID' with the actual file ID from the shareable link
file_id = '1lTxTyX-4ama5uH5W4d9CQW5D6ss_wmLP'

 # Construct the download link
download_link = f'https://drive.google.com/uc?id={file_id}'

# # Download the file content using requests
response = requests.get(download_link)

# Check if the response is an HTML page indicating a warning
if 'Virus scan warning' in response.text:
    soup = BeautifulSoup(response.text, 'html.parser')
    download_link = soup.find('form', {'id': 'download-form'}).get('action')
    response = requests.get(download_link, params={'id': file_id, 'confirm': 't'})

# Create a Pandas DataFrame directly from the CSV content
csv_content = response.text
df = pd.read_csv(StringIO(csv_content))

# #############################################################################################################
#
#
#

# Assuming df is defined earlier in your code
#df = pd.read_csv("D:\Prediction Work\Dashbaord\pythonProject\Kolkata_Wardwise_2023.csv")

# Convert the 'geometry' column to Shapely geometries
df['geometry'] = df['geometry'].apply(loads)

# Create a GeoDataFrame
gdf = gpd.GeoDataFrame(df, geometry='geometry')

# List of cities in your DataFrame
cities = df['City'].unique()

# Create Dash app
app = dash.Dash(__name__)
server = app.server

# Path to the PNG image
image_path = r'D:\Prediction Work\Data\Variable data from NCAR\New Data\Plots and csv\Kolkata\colorbar.png'


# Function to encode the image to base64
def encode_image(image_path):
    with open(image_path, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    return f'data:image/png;base64,{encoded_image}'


# Layout of the app
app.layout = html.Div([
    # Title and Logo
    html.Div([
        html.Img(src={'src': 'D:/Dashboard_exp_2024/assets/image.png'}, style={'height': '100px', 'width': '100px'}),
        html.H1("Dashbaord for Ward Level PM 2.5 Prediction for Howrah and Kolkata", style={'text-align': 'center'}),
    ], style={'display': 'flex', 'align-items': 'center'}),

    # Text labels and Dropdown for selecting city and Datepicker for selecting date
    html.Div([
        html.Div([
            html.Label("Select a city:"),
            dcc.Dropdown(
                id='city-dropdown',
                options=[{'label': city, 'value': city} for city in cities],
                value=cities[0],  # Default selected value
                style={'width': '50%'}
            ),
        ], style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            html.Label("Select Date:"),
            dcc.DatePickerSingle(
                id='date-picker',
                display_format='YYYY-MM-DD',
                style={'width': '50%'}
            ),
        ], style={'width': '48%', 'display': 'inline-block'}),
    ], style={'margin-bottom': '20px'}),

    # Graph and Image side by side
    html.Div(
        children=[
            dcc.Graph(
                id='pm25-map',
                style={'height': '600px', 'width': '92%', 'display': 'inline-block'}  # Set the height of the Mapbox
            ),
            html.Img(
                src=encode_image(image_path),
                alt='Your Image',
                style={'width': '8%', 'display': 'inline-block'},
            ),
        ],
    ),
])


# Callback to update the available dates based on the selected city and set DatePickerSingle properties
@app.callback(
    [Output('date-picker', 'options'),
     Output('date-picker', 'min_date_allowed'),
     Output('date-picker', 'max_date_allowed'),
     Output('date-picker', 'initial_visible_month')],
    [Input('city-dropdown', 'value')]
)
def update_dates_options(selected_city):
    filtered_dates = df[df['City'] == selected_city]['Date'].unique()
    date_options = [{'label': datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d'), 'value': date} for date in
                    filtered_dates]
    min_date = min(filtered_dates)
    max_date = max(filtered_dates)
    initial_visible_month = min_date

    return date_options, min_date, max_date, initial_visible_month


# Callback to set the default selected date
@app.callback(
    Output('date-picker', 'date'),
    [Input('date-picker', 'options')]
)
def set_default_date(date_options):
    return date_options[0]['value'] if date_options else None


# Callback to update the map based on the selected city and date
@app.callback(
    Output('pm25-map', 'figure'),
    [Input('city-dropdown', 'value'),
     Input('date-picker', 'date')]
)
def update_map(selected_city, selected_date):
    filtered_gdf = gdf[(gdf['City'] == selected_city) & (gdf['Date'] == selected_date)]

    fig = px.choropleth_mapbox(
        filtered_gdf,
        geojson=filtered_gdf.geometry.__geo_interface__,
        locations=filtered_gdf.index,
        color='PM2.5',
        color_continuous_scale="RdYlGn_r",
        color_continuous_midpoint=40,
        range_color=[20, 120],  # Fixed color scale range
        mapbox_style="carto-positron",
        zoom=10.6,
        center={"lat": filtered_gdf.geometry.centroid.y.mean(), "lon": filtered_gdf.geometry.centroid.x.mean()},
        opacity=0.5,
    )

    fig.update_traces(
        customdata=filtered_gdf[['WARD', 'PM2.5']],
        hovertemplate='<b>Ward:</b> %{customdata[0]}<br><b>PM2.5:</b> %{customdata[1]:.2f}'
    )

    # Remove color bar
    fig.update_layout(coloraxis_showscale=False)

    return fig


# Run the app
if __name__=='__main__':
    app.run_server(debug=False)