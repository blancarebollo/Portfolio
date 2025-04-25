# Import libraries
import streamlit as st
from streamlit_js_eval import get_geolocation
from streamlit.components.v1 import html  # Streamlit to build the web app
import requests  # Requests to interact with Google APIs
import folium  # Folium to generate the map
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

st.set_page_config(page_title="Nearby Finder", layout="centered")

# Get the API key from environment variables
api_key = os.getenv('GOOGLE_API_KEY')  # Make sure your API key is loaded correctly
st.write(f"API Key loaded: {api_key}")  # Debugging the API key

# Function to get latitude and longitude from a text address using Google Geocoding API
def get_coordinates(address):
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}'
    st.write(f"Geocoding URL: {url}")  # Log the URL being called
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            st.error("No coordinates found for that address.")
            return None, None
    else:
        st.error(f"Error retrieving coordinates. Status code: {response.status_code}")
        return None, None

# Function to get nearby places using the Google Places API
def get_places(lat, lng, radius, place_type):
    type_param = ''
    keyword = ''

    if place_type == 'Park':
        type_param = 'park'
    elif place_type == 'Biergarten':
        keyword = 'biergarten'
    elif place_type == 'Lake':
        keyword = 'lake'

    # Corrected URL for Google Places API
    url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&key={api_key}'

    if type_param:
        url += f"&type={type_param}"
    if keyword:
        url += f"&keyword={keyword}"

    response = requests.get(url)
    # st.write("Request URL:", url)  # Helps with debugging

    places = []

    if response.status_code == 200:
        data = response.json()
        # st.json(data)  # Helps with debugging
        for result in data.get('results', []):
            places.append({
                'name': result['name'],
                'address': result.get('vicinity', 'No address'),
                'lat': result['geometry']['location']['lat'],
                'lng': result['geometry']['location']['lng'],
                'map_link': f"https://www.google.com/maps/search/?api=1&query={result['geometry']['location']['lat']},{result['geometry']['location']['lng']}"
            })
    else:
        st.error("Failed to fetch from Google Places API.")

    return places

# Function to display parks on an interactive map
def show_map(places, center_lat, center_lng):
    # Create a map centered on user's location
    map_obj = folium.Map(location=[center_lat, center_lng], zoom_start=14)

    # Add a marker for the user's location
    folium.Marker([center_lat, center_lng], popup='You are here!').add_to(map_obj)

    # Add markers for all found parks
    for place in places:
        folium.Marker(
            [place['lat'], place['lng']],
            popup=f"{place['name']} <br>{place['address']}",
            icon=folium.Icon(color='green')
        ).add_to(map_obj)

    # Return the map as embeddable HTML
    return map_obj._repr_html_()

# Main Streamlit app
def app():
    # Set the page config here before any other Streamlit commands

    st.title("🍃 Find Parks, Biergartens, or Lakes Near You")

    search_type = st.selectbox("What are you looking for?", ["Park", "Biergarten", "Lake"])
    radius = st.slider("Search radius (meters)", 500, 5000, step=500, value=1500)

    location_method = st.radio("Location Method", ["Enter address manually", "Use my current location"])

    if location_method == "Enter address manually":
        address = st.text_input("Enter your address", "Gran Via, Madrid, Spain")
        if st.button("Search"):
            lat, lng = get_coordinates(address)
            if lat:
                places = get_places(lat, lng, radius, search_type)
                if places:
                    st.success(f"Found {len(places)} results near {address}")
                    html(show_map(places, lat, lng), height=500)
                    for p in places:
                        st.markdown(f"**{p['name']}** - {p['address']} [📍Map]({p['map_link']})")
                else:
                    st.warning("No results found.")
            else:
                st.error("Couldn't get coordinates. Check your address.")

    else:
        loc = get_geolocation()  # Get the current location

        if loc and 'coords' in loc:
            lat = loc['coords']['latitude']
            lng = loc['coords']['longitude']
            st.success(f"Detected location: {lat}, {lng}")

            places = get_places(lat, lng, radius, search_type)
            if places:
                st.success(f"Found {len(places)} results near you")
                html(show_map(places, lat, lng), height=500)
                for p in places:
                    st.markdown(f"**{p['name']}** - {p['address']} [📍Map]({p['map_link']})")
            else:
                st.warning("No results found.")
        else:
            st.info("Please allow access to your location.")

# Run the app
if __name__ == '__main__':
    app()
