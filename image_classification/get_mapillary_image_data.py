import requests
import pandas as pd
from datetime import datetime, timedelta

# Bounding box
min_lon = 121.03214776391893
max_lon = 121.05675591082228
min_lat = 14.571781902967313
max_lat = 14.585730268391343

# Set up your API token and search parameters
ACCESS_TOKEN = 'MLY|8674705402643629|3204a2d76cfab03986db6b0907a58a1a'
bbox = [min_lon, min_lat, max_lon, max_lat]  # Bounding box coordinates

# Start and end dates
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 10, 21)

image_list = []

# Generate and print each date in the specified format
current_date = start_date
while current_date <= end_date:

    next_date = current_date + timedelta(days=1)

    current_date_str = (current_date.strftime("%Y-%m-%d"))
    next_date_str = (next_date.strftime("%Y-%m-%d"))

    url = f"https://graph.mapillary.com/images?access_token={ACCESS_TOKEN}&bbox={','.join(map(str, bbox))}&fields=id,geometry,captured_at,camera_type&start_captured_at={current_date_str}T00:00:00Z&end_captured_at={next_date_str}T00:00:00Z&is_pano=False"


    response = requests.get(url)
    images_data = response.json()

    # Loop through each image and extract required data
    i=0
    for image in images_data['data']:
        image_id = image['id']
        latitude = image['geometry']['coordinates'][1]
        longitude = image['geometry']['coordinates'][0]
        captured_at = image.get('captured_at')
        camera_type = image.get('camera_type', 'Unknown')  # Handle missing camera_type

        # Append the data as a dictionary to the list
        image_list.append({
            'image_id': image_id,
            'latitude': latitude,
            'longitude': longitude,
            'captured_at': captured_at,
            'camera_type': camera_type
        })
        i += 1
        print(f'{current_date} - done with image #{i}')

    current_date = next_date

# Convert the list of dictionaries into a DataFrame
df = pd.DataFrame(image_list)

# Export the DataFrame to a CSV file
df.to_csv(f'final-2024.csv', index=False)

print("Image data has been successfully saved!")
