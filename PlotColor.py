import seaborn as sb
import random

# Initialize country_colors dictionary to store generated colors
country_colors = {}

# Function to generate random color using 'husl' color palette
def generate_random_color():
    return sb.color_palette('husl', as_cmap=True)(random.random())

# Function to ensure generated colors are visually distinct
def ensure_visual_distinctness():
    global country_colors

    # Check color distance and ensure colors are visually distinct
    for country in country_colors:
        color = country_colors[country]
        for existing_country, existing_color in country_colors.items():
            if country != existing_country:
                # Calculate color distance (Euclidean distance in RGB space)
                color_distance = ((color[0] - existing_color[0])**2 + (color[1] - existing_color[1])**2 + (color[2] - existing_color[2])**2)**0.5
                if color_distance < 0.5:  # Adjust threshold as needed for distinctness
                    # Generate a new color if distance is too small
                    country_colors[country] = generate_random_color()
                    ensure_visual_distinctness()  # Recursively check again