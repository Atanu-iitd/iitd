import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import geopandas as gpd
from shapely.wkt import loads
import plotly.express as px
import matplotlib.pyplot as plt
import io
import base64
from PIL import Image  # Import PIL for image processing
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
from io import StringIO


# Replace 'YOUR_FILE_ID' with the actual file ID from the shareable link
file_id = '17l0kbgPJG7WoYs94tma7cdtakarM_SRJ'

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

# Convert the 'geometry' column to Shapely geometries
df['geometry'] = df['geometry'].apply(loads)

# Create a GeoDataFrame
gdf = gpd.GeoDataFrame(df, geometry='geometry')

# List of cities in your DataFrame
cities = df['City'].unique()

# Create Dash app
app = dash.Dash(__name__)
server = app.server
# Create a colorbar using Matplotlib without associated plot
fig_colorbar, ax_colorbar = plt.subplots(figsize=(10, 6), dpi=1200)  # Adjust the figsize and dpi as needed
cmap = plt.cm.get_cmap('jet')
norm = plt.Normalize(vmin=20, vmax=120)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])

# Hide the axes
ax_colorbar.set_visible(False)

# Add colorbar to the figure
cb = plt.colorbar(sm, ax=ax_colorbar, extend='both', label='PM 2.5(µg/m3)', orientation='horizontal')

# Save the colorbar as an image
colorbar_img = io.BytesIO()
fig_colorbar.savefig(colorbar_img, format='png', bbox_inches='tight', pad_inches=0)
plt.close(fig_colorbar)

# Convert the image to base64
colorbar_img_str = f"data:image/png;base64,{base64.b64encode(colorbar_img.getvalue()).decode()}"

# Layout of the app
app.layout = html.Div([
    # Title, Logo, and Additional Image
    html.Div([
        # Left Image (Logo)
        html.Img(src=app.get_asset_url('image.png'), style={'height': '100px', 'width': '100px'}),

        # Title
        html.H1("Dashboard for Ward Level PM 2.5 Prediction for Howrah and Kolkata", style={'text-align': 'center'}),

        # Right Image
        html.Img(src=app.get_asset_url('another_image.png'), style={'height': '100px', 'width': '100px'}),
    ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'space-between'}),
    
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
    ], style={'margin-bottom': '0px'}),
    
    # Plotly Express Map
    html.Div([
        dcc.Graph(
            id='pm25-map',
            style={'height': '600px', 'width': '100%', 'display': 'inline-block', 'margin-bottom': '0px'}  # Set the height and width of the Mapbox
        ),
    ]),
    
    # Image below the graph
    html.Div([
        html.Img(
            src=colorbar_img_str,
            style={'height': '100px', 'width': '100%', 'display': 'inline-block', 'margin-top': '0px'}
        ),
    ]),
    
    
    # Footer
    html.Div([
        html.P("Created and Maintained by IIT Delhi Team", style={'text-align': 'left', 'font-size': '20px'}),
    ], style={'margin-top': '20px', 'padding': '10px', 'background-color': '#f0f0f0'}),
])


# Callback to update the map based on the selected city and date
@app.callback(
    Output('pm25-map', 'figure'),
    [Input('city-dropdown', 'value'),
     Input('date-picker', 'date')]
)
def update_map(selected_city, selected_date):
    filtered_gdf = gdf[(gdf['City'] == selected_city) & (gdf['Date'] == selected_date)]
    
    # Plotly Express Map
    fig_map = px.choropleth_mapbox(
        filtered_gdf,
        geojson=filtered_gdf.geometry.__geo_interface__,
        locations=filtered_gdf.index,
        color='PM2.5',
        color_continuous_scale="jet",
        color_continuous_midpoint=70,
        range_color=[20, 120],  # Fixed color scale range
        mapbox_style="open-street-map",
        #mapbox_style="carto-positron",
        zoom=10.6,
        center={"lat": filtered_gdf.geometry.centroid.y.mean(), "lon": filtered_gdf.geometry.centroid.x.mean()},
        opacity=0.8,
        labels={'color':'PM2.5'},
    )
    
    fig_map.update_traces(
        customdata=filtered_gdf[['WARD', 'PM2.5']],
        hovertemplate='<b>Ward:</b> %{customdata[0]}<br><b>PM2.5:</b> %{customdata[1]:.2f}'
    )
    
    # Hide color bar
    fig_map.update_layout(coloraxis_showscale=False)
    
    return fig_map

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
    date_options = [{'label': datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d'), 'value': date} for date in filtered_dates]
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

# Run the app
if __name__ == '__main__':
    app.run_server(debug=False)
