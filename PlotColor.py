import seaborn as sb
import random
import numpy as np

# Initialize country_colors dictionary to store generated colors
country_colors = {}

# Function to generate random color using 'husl' color palette
def generate_random_color():
    return sb.color_palette('husl', as_cmap=True)(random.random())


def ensure_visual_distinctness():
    global country_colors

    # List of country names for comparison
    countries = list(country_colors.keys())

    # Loop through each country and compare its color with others
    for i, country in enumerate(countries):
        color = country_colors[country]

        for j, existing_country in enumerate(countries):
            if i != j:
                existing_color = country_colors[existing_country]

                # Calculate the Euclidean distance between two RGB colors
                color_distance = np.linalg.norm(np.array(color) - np.array(existing_color))

                # If the color distance is too small, generate a new color
                while color_distance < 0.5:
                    new_color = generate_random_color()
                    country_colors[country] = new_color
                    color_distance = np.linalg.norm(np.array(new_color) - np.array(existing_color))