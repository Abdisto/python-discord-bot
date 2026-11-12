import urllib.request
import json
import base64
from io import BytesIO
from PIL import Image, ImageDraw

def get_texture(uuid):
    url = f'https://sessionserver.mojang.com/session/minecraft/profile/{uuid}'
    response = urllib.request.urlopen(url)
    data = json.loads(response.read().decode('utf-8'))

    properties = data["properties"]
    texture_data = next((prop for prop in properties if prop["name"] == "textures"), None)

    if texture_data:
        texture_value = texture_data["value"]
        decoded_data = base64.b64decode(texture_value).decode("utf-8")
        texture_json = json.loads(decoded_data)
        texture_url = texture_json["textures"]["SKIN"]["url"]

        return texture_url

def extract_and_save_regions(raw_png_data, filename):
    border = 2 # pixel border width
    resize_factor = 4

    # Load the image from the raw binary data
    image = Image.open(BytesIO(raw_png_data))

    # Define the regions to extract
    regions = {
        "region1": (8, 8, 16, 16),  # (left, upper, right, lower)
        "region2": (40, 8, 48, 16)
    }

    # Extract the regions
    region1 = image.crop(regions["region1"])  # Crop region1
    region2 = image.crop(regions["region2"])  # Crop region2

    region1 = region1.resize((8*resize_factor, 8*resize_factor), Image.NEAREST)
    region2 = region2.resize((8*resize_factor+resize_factor, 8*resize_factor+resize_factor), Image.NEAREST)

    # Create a new blank image with the size of the largest region
    max_width = max(region1.width+4+2*border, region2.width+4+2*border) # +4 for pixel shift / +2*border for border duh
    max_height = max(region1.height+4+2*border, region2.height+4+2*border)

    result_image = Image.new('RGBA', (max_width, max_height))  # Create an empty image with transparent background

    # Paste region1 and region2 onto the new image at the same position
    result_image.paste(region1, (int(resize_factor/2+border), int(resize_factor/2+border)), region1)  # Paste region1 at (0, 0)
    result_image.paste(region2, (0+border, 0+border), region2)  # Paste region2 at (0, 0)

    # Save the layered result
    result_image.save(f"{filename}.png")
    print(f"Saved {filename}.png")

def get_head(player):
    url = f'https://api.mojang.com/users/profiles/minecraft/{player}'
    response = urllib.request.urlopen(url)
    data = json.loads(response.read().decode('utf-8'))
    uuid = data["id"]

    print(uuid)

    texture_url = get_texture(uuid)

    png_response = urllib.request.urlopen(texture_url)
    raw_png_data = png_response.read()
    # print(f"Raw PNG data: {raw_png_data}")
    if raw_png_data:
        extract_and_save_regions(raw_png_data, player)

get_head('Blacklight_Mc')
get_head('Luftiy')
