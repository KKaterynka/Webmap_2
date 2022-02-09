import folium
import os
import json
import geopy
from geopy.geocoders import Nominatim
import math
from math import cos, sin, atan, sqrt, radians
import argparse

# parser
parser = argparse.ArgumentParser()

# arguments
parser.add_argument('year', type=int, help='Year of films')
parser.add_argument('lat', type=float, help='Latitude')
parser.add_argument('lon', type=float, help='Longitude')
parser.add_argument('path', help='Path to dataset')

args = parser.parse_args()

user_latitude = radians(float(args.lat))
user_longitude = radians(float(args.lon))
year = args.year

# Create a map
map = folium.Map(tiles="Stamen Terrain", location=[user_latitude, user_longitude], zoom_start=3)

tooltip = 'Click For More Info'

# Geojson data
style_liner = {'fillColor': '#DFE912', 'color': '#60FF61'}
overlay = os.path.join('data', 'us_liner.json')
folium.GeoJson(overlay, name='United States', style_function=lambda x: style_liner).add_to(map)

# Create custom icon
logoIcon = folium.features.CustomIcon('data/film_icon.png', icon_size=(90, 90))
folium.Marker([44.068203, -114.742043],
              popup="<strong>US is the country with the largest number of film productions!</strong>",
              icon=logoIcon).add_to(map)

places_film = []
distances = []


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Returns the distance between two points
    based on theirs' latitude and longitude.

            Parameters:
                    lat1 (float): A latitude of first point
                    lon1 (float): A longitude of first point
                    lat2 (float): A latitude of second point
                    lon2 (float): A longitude of second point

            Returns:
                    distance (float): Float distance between two points.

    >>> calculate_distance(0.8698417304649891, 0.4192846349968026, 0.594349028661431, -2.0637255833652053)
    9976.59324086067
    >>> calculate_distance(0.800028560385216, -1.2395893834341374, 0.594349028661431, -2.0637255833652053)
    4166.993843761246
    >>> calculate_distance(0.9920147781045922, 0.5938175601962355, 0.5282879054484069, -1.7062860622340936)
    9326.484169816207
    """
    RADIUS = 6373.0
    haversin_distance_1 = (1 - math.cos(lat2 - lat1)) / 2 + math.cos(lat2) * math.cos(
        lat1) * ((1 - math.cos(lon2 - lon1)) / 2)
    haversin_distance_2 = 2 * math.atan2(sqrt(haversin_distance_1), sqrt(1 - haversin_distance_1))
    distance = RADIUS * haversin_distance_2
    return distance


def exact_location(location):
    """
    Returns accurate location
    of the given inaccurate location.

            Parameters:
                    location (str): given (inaccurate) location

            Returns:
                    distance (str): accurate location

    >>> exact_location("Los Angeles, California, USA")
    Location(Los Angeles, Los Angeles County, California, United States, (34.0536909, -118.242766, 0.0))
    >>> exact_location("Coventry, West Midlands, England, UK")
    Location(Coventry, West Midlands Combined Authority, West Midlands, England, United Kingdom, (52.4081812, -1.510477, 0.0))
    >>> exact_location("Alamo Drafthouse Ritz, Austin, Texas, USA")
    Location(Alamo Drafthouse Cinema - The Ritz, 320, East 6th Street, Downtown, Austin, Travis County, Texas, 78701, United States, (30.26740345, -97.73958582383372, 0.0))
    """
    geo_address = Nominatim(user_agent='accurate-coordinates').geocode(location)
    while geo_address is None:
        location = location[location.find(",") + 1:].strip()
        geo_address = Nominatim(user_agent='accurate-coordinates').geocode(location)
    return geo_address



with open(args.path, 'r', encoding='utf-8') as fdata:
    # Skip first few lines
    for _ in range(14):
        next(fdata)

    for line in fdata:

        # Extract name of film
        braket_index_start = line.find("(")
        braket_index_close = line.find(")")
        figure_braket_index = line.find("}")
        if figure_braket_index == -1:
            line_name = line[2:braket_index_start - 2].strip()
        else:
            line_name = line[
                        2:braket_index_start - 2].strip() + " " + f"({line[line.find('{') + 1:figure_braket_index].strip()})"

        # Extract year of film
        line_year = line[braket_index_start + 1:braket_index_close]

        # Extract location of film
        if figure_braket_index == -1:
            line_location = line[braket_index_close + 1:].strip()
        else:
            line_location = line[figure_braket_index + 1:].strip()
        if line_location.find("(") != -1:
            line_location = line_location[:line_location.find("(")].strip()

        # Find exact location using geopy module
        geo_address = exact_location(line_location)

        # Convert latitude and longitude to radians
        line_latitude = radians(float(geo_address.latitude))
        line_longitude = radians(float(geo_address.longitude))

        # Calculate distance between two points
        distance = calculate_distance(user_latitude, user_longitude, line_latitude, line_longitude)
        res_lat = geo_address.latitude
        res_lon = geo_address.longitude

        # Check whether two markers overlay
        if distance not in distances and year == int(line_year):
            distances.append(distance)
        elif distance in distances and year == int(line_year):
            res_lat += 3 * distances.count(distance)
            res_lon -= 2 * distances.count(distance)
            distances.append(distance)

        # Create a list of future markers
        if year == int(line_year):
            places_film.append((line_name, float(res_lat), float(res_lon), distance))

places_film = sorted(places_film, key=lambda i: i[-1])[:10]

# Create markers
for i in range(0, len(places_film)):
    folium.Marker([places_film[i][1], places_film[i][2]], popup=f"<strong>{places_film[i][0]}</strong>",
                  tooltip=tooltip,
                  icon=folium.Icon(color='cadetblue', icon='film', prefix='fa')).add_to(map)

map.save('task2.html')

