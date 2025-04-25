# Import libraries
import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from streamlit.components.v1 import html # Streamlit to build the web app
import requests                  # Requests to interact with Google APIs
import folium                    # Folium to generate the map
from dotenv import load_dotenv
import os

load_dotenv()


api_key = os.getenv('your_api_key')      # (Optional here) Useful to handle in-memory files

# Function to get latitude and longitude from a text address using Google Geocoding API
def get_coordinates(address):
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}'
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
        st.error("Error retrieving coordinates.")
        return None, None

# Function to get nearby parks using the Google Places API
def get_places(lat, lng, radius, place_type):
    if place_type == 'Park':
        type_param = 'park'
        keyword = ''
    elif place_type == 'Biergarten':
        type_param = 'biergarten'
        keyword = 'biergarten'
    elif place_type == 'Lake':
        type_param = 'natural_feature'
        keyword = 'lake'

    url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type={type_param}&keyword={keyword}&key={api_key}'
    response = requests.get(url)
    places = []

    if response.status_code == 200:
        data = response.json()
        for result in data['results']:
            name = result['name']
            address = result.get('vicinity', 'No address provided')
            lat = result['geometry']['location']['lat']
            lng = result['geometry']['location']['lng']
            maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"

            places.append({
                'name': name,
                'address': address,
                'lat': lat,
                'lng': lng,
                'map_link': maps_url
            })
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
            icon = folium.Icon(color = 'green')
        ).add_to(map_obj)

    # Return the map as embeddable HTML
    return map_obj._repr_html_()

# Main Streamlit app
def app():
    st.set_page_config(page_title="Nearby Finder", layout="centered")
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
        location = streamlit_js_eval(
            js_expressions="""
                new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(
                (pos) => resolve({coords: pos.coords}),
                (err) => reject(err)
            );
            });
            """,
        key="get_geolocation"
)

        if location and 'coords' in location:
            lat = location['coords']['latitude']
            lng = location['coords']['longitude']
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
