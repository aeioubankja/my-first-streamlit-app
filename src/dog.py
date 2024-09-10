import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from urllib.request import urlopen
import json
from copy import deepcopy
from shapely.geometry import shape, Point
from shapely.ops import unary_union
import geopandas as gpd

# dog_df = pd.read_csv("./data/dog.csv")
# dog_d

# decorator of function (In this case, for any df)
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    return df

dog_df = load_data(path="./data/dog.csv")
dog_df = deepcopy(dog_df) # for security

dog = dog_df.rename(columns={
    'HALTER_ID': 'Owner_ID',
    'ALTER': 'Age',
    'GESCHLECHT': 'Gender',
    'STADTKREIS': 'City_District',
    'STADTQUARTIER': 'City_Quarter',
    'RASSE1': 'Breed1',
    'RASSE1_MISCHLING': 'Breed1_Mix',
    'RASSE2': 'Breed2',
    'RASSE2_MISCHLING': 'Breed2_Mix',
    'RASSENTYP': 'Breed_Type',
    'GEBURTSJAHR_HUND': 'Dog_Birth_Year',
    'GESCHLECHT_HUND': 'Dog_Gender',
    'HUNDEFARBE': 'Dog_Color'
})

# dog
# dog_df

# Define a mapping directly from the original age ranges to the new categories
age_group_mapping = {
    '11-20': 'Teenager(<=20)',
    '21-30': 'Adult(21-60)',
    '31-40': 'Adult(21-60)',
    '41-50': 'Adult(21-60)',
    '51-60': 'Adult(21-60)',
    '61-70': 'Elderly(>60)',
    '71-80': 'Elderly(>60)',
    '81-90': 'Elderly(>60)',
    '91-100': 'Elderly(>60)'
}

# Map the existing age ranges to the new age groups
dog['Age_Group'] = dog['Age'].map(age_group_mapping)

# Center-aligned title with color
st.markdown(
    """
    <h1 style='text-align: center; color: #4a4a4a;'>Zurich Dog Exploration</h1>
    """,
    unsafe_allow_html=True
)

# st.title('Zurich Dog Exploration')
# st.header('Exploration')

# with st.sidebar:
#     st.header('Show All Data')

#     if st.sidebar.checkbox("In German language"):
#         st.dataframe(data=dog_df)

#     if st.sidebar.checkbox("In English language"):
#         st.dataframe(data=dog)

st.sidebar.header('Show All Data')

# Sidebar for language selection
show_german = st.sidebar.checkbox("In German Language")
show_english = st.sidebar.checkbox("In English Language")

# Display the selected DataFrame based on checkbox selection
if show_german:
    st.subheader('All Data')
    st.dataframe(data=dog_df)

if show_english:
    st.subheader('All Data')
    st.dataframe(data=dog)

# Sidebar for filters
with st.sidebar:
    st.header("Filters")
    
    Breeds = ["All"] + sorted(pd.unique(dog['Breed1']))
    Breed = st.selectbox("Choose a Breed", Breeds)
    
    Owner = st.radio(
        label='Owner Properties', options=dog['Gender'].unique())
    
    # Generate checkboxes for unique Age Groups
    age_selected = []
    for age_group in dog['Age_Group'].unique():
        if st.checkbox(f"Include {age_group}", value=True):
            age_selected.append(age_group)

# Filter the DataFrame based on the selected values
filtered_df = dog[
    (dog['Breed1'] == Breed if Breed != "All" else True) &
    (dog['Gender'] == Owner) &
    (dog['Age_Group'].isin(age_selected))
]

# dog['Breed_Type'].unique()
dogs_per_district = filtered_df.groupby("City_District").size().reset_index(name='COUNT')

with open("./data/stzh.adm_stadtkreise_a.json") as response:
     jsonfile = json.load(response)

# Create a GeoDataFrame from the GeoJSON data
gdf = gpd.GeoDataFrame.from_features(jsonfile['features'])

# Calculate centroids of each district
gdf['centroid'] = gdf.geometry.centroid
gdf['lat'] = gdf['centroid'].y
gdf['lon'] = gdf['centroid'].x

# Convert to DataFrame
centroid_df = gdf[['name', 'lat', 'lon']].rename(columns={'name': 'City_District'})

# Determine the most common breed for each district
most_common_breeds = filtered_df.groupby('City_District')['Breed1'].agg(lambda x: x.mode()[0]).reset_index()

# Ensure both columns are of type string
centroid_df['City_District'] = centroid_df['City_District'].astype(str)
most_common_breeds['City_District'] = most_common_breeds['City_District'].astype(str)

# Merge the centroid coordinates with the most common breeds
district_breeds = pd.merge(centroid_df, most_common_breeds, on='City_District')

# Add breed image URLs to the DataFrame (for example)
# You need to replace these with the actual URLs of the breed images
# district_breeds['Image_URL'] = [
#     'https://example.com/labrador.png',  # Replace with actual URL
#     'https://example.com/poodle.png',    # Replace with actual URL
#     'https://example.com/beagle.png'     # Replace with actual URL
# ]

# Add a line break before the figure
st.markdown("<br>", unsafe_allow_html=True)

# Create the choropleth map
# Right now we have 2 dataframe --> dogs_per_district for background of each district, district_breeds for centroid of each district
fig = px.choropleth_mapbox(
    dogs_per_district, 
    color="COUNT",
    geojson=jsonfile, 
    locations="City_District", 
    featureidkey="properties.name",
    center={"lat": 47.38, "lon": 8.54},
    mapbox_style="carto-positron", 
    zoom=10.8,
    opacity=0.7,
    width=700,
    height=600,
    labels={"City_District":"District",
           "COUNT":"Number of Dogs"},
    title="<b>Number of Dogs per District</b>",
    color_continuous_scale="Blues",
)

# Add the breed name in each district center
# Check if there is data to display
if not district_breeds.empty:
    fig.add_trace(
        go.Scattermapbox(
            lat=district_breeds['lat'],
            lon=district_breeds['lon'],
            mode='markers',
            marker=dict(
                size=10,
                color='black'
            ),
            text=district_breeds['Breed1'],
            textposition='bottom center',
            hoverinfo='text',  # Only show text on hover
            showlegend=False
        )
    )

fig.update_layout(
    margin={"r":0,"t":35,"l":0,"b":0},
    font_family="Balto",
    font_color="black",
    hoverlabel={"bgcolor":"white", 
                "font_size":12,
                "font_family":"Balto"},
    title={"font_size":20}
)

# Display the Plotly figure in the Streamlit app
st.plotly_chart(fig)


st.markdown("<h2 style='font-size:20px;'>Filter Data</h2>", unsafe_allow_html=True)

# Display only the specified columns
columns_to_show = ['Age_Group', 'Gender', 'City_District', 'City_Quarter', 'Breed1', 'Breed_Type']
filtered_df = filtered_df[columns_to_show]

# Display the filtered data
st.dataframe(filtered_df)