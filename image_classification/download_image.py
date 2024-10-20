import os
import requests
import pandas as pd

# Set up your API token and image folder
ACCESS_TOKEN = 'MLY|8934424159913931|f23721e7784538139bc06e29912b9362'
image_folder = 'downloaded_images_2024'

# Load the DataFrame from a CSV (or from wherever it's created)
df1 = pd.read_csv('mandaluyong_bounding_box_a_data_2024.csv')
df2 = pd.read_csv('final-2024.csv')

df = df2[~df2.apply(tuple, axis=1).isin(df1.apply(tuple, axis=1))]

df.to_csv('batch2-df.csv',index=False)

# # Loop through the DataFrame to access each image_id, latitude, and longitude
# i=1
# for index, row in df.iterrows():
#     image_id = row['image_id']
#     lat = row['latitude']
#     lon = row['longitude']

#     # Format the image file name as image_id_lat_lon
#     image_name = f"{image_id}_{lat}_{lon}.jpg"
#     image_path = os.path.join(image_folder, image_name)
    
#     # Get the image URL for the current image_id
#     url = f"https://graph.mapillary.com/{image_id}?access_token={ACCESS_TOKEN}&fields=thumb_1024_url"
#     response = requests.get(url)
    
#     if response.status_code == 200:
#         image_info = response.json()
#         image_url = image_info.get('thumb_1024_url')

#         # Download the image if the URL is valid
#         if image_url:
#             img_response = requests.get(image_url)
#             if img_response.status_code == 200:
#                 # Save the image in the specified folder
#                 with open(image_path, 'wb') as file:
#                     file.write(img_response.content)
#                 print(f"({i}/{df.shape[0]}) Downloaded image {image_name}")
#             else:
#                 print(f"({i}/{df.shape[0]}) Failed to download image {image_id}: Image request failed")
#         else:
#             print(f"({i}/{df.shape[0]}) Image URL not found for image_id: {image_id}")
#     else:
#         print(f"({i}/{df.shape[0]}) Failed to get image metadata for image_id: {image_id}")
    
#     i += 1
