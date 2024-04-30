import os
from PIL import Image
import pdb

concept = "Reflect"
query_repeats = None # Number of times to repeat process, set to None for max. # of trials with given stimuli

stimuli_directory = f"/Users/anisamajhi/Desktop/Stimuli100_50_Hard/{concept}_Objects100" # Insert object file directory
output_directory = f"/Users/anisamajhi/Desktop/Human_Trials_Hard/{concept}" # Insert folder to contain results

os.makedirs(output_directory, exist_ok=True)
os.makedirs(output_directory, exist_ok=True)
os.makedirs(f"{output_directory}/Train", exist_ok=True)
os.makedirs(f"{output_directory}/Test", exist_ok=True)

#——————————————————————————————————————————————————————————————————————————————————————————————————————————————————

# Rename either below to "concept_to_parameters" if using, remove "_simple" or "_hard" to use
concept_to_parameters_simple = {
	"2DRotation": (["+90", "-90", 180]),
	"Counting": (["+1","+2","-1","-2"]),  
	"Colour": (["Red", "Green", "Blue"]),
	"Reflect": (["X", "Y"]), 
	"Resize": (["0.5XY", "2XY"])
}

concept_to_parameters = {
    "2DRotation": (["+45", "-45", "+90", "-90", "+135", "-135", 180]), 
    "Counting": (["+1","+2","-1","-2","x2","x3","d2","d3"]), 
    "Colour": (["Red","Yellow", "Green", "Blue", "Grey"]),
    "Reflect": (["X", "Y", "XY"]),
    "Resize": (["0.5X", "0.5Y", "0.5XY", "2X", "2Y", "2XY"]) 
}

def get_indexed_files(param):
	indexed_files = {}
	beginning = concept + str(param)

	for filename in os.listdir(stimuli_directory):
		if filename.startswith(beginning + "_"):
			index = int(filename.split('_')[1])
			if index not in indexed_files:
				indexed_files[index] = []
			indexed_files[index].append(filename)

	return indexed_files

def format_files_by_type(indexed_files, index, file_type):
    train_files = [filename for filename in indexed_files[index] if 'train' in filename]
    
    if file_type == 'train':  # Create pairs of input and output files
        for filename in train_files:
            if 'input' in filename:
                input_filename = filename
            elif 'output' in filename:
                output_filename = filename

        # Extract the pairs into a list of lists
        formatted_files = [input_filename, output_filename]

    elif file_type == 'test':
        test_files_input = [filename for filename in indexed_files[index] if 'test' in filename]
        formatted_files = sorted(test_files_input)

    return formatted_files

def read_image(img_path): 
    #print(f"Attempting to open the file at: {img_path}")
    png_image = Image.open(img_path)
    
    # Check if the image has an alpha channel
    if png_image.mode in ('RGBA', 'LA') or (png_image.mode == 'P' and 'transparency' in png_image.info):
        # Create a new RGB image with the same size and white background
        rgb_image = Image.new("RGB", png_image.size, (255, 255, 255))
        # Paste the PNG image onto the RGB image, using alpha channel as mask
        rgb_image.paste(png_image, mask=png_image.split()[3]) # 3 is the index of alpha channel in 'RGBA'
    else:
        # If no alpha channel, just convert to RGB
        rgb_image = png_image.convert('RGB')

    rgb_image.thumbnail((300, 300))

    return rgb_image

def stitch_images_v(images, add_borders=True, tight=True):
    border_size = 20
    color="black"
    # Read image using pillow 
    if add_borders:
        new_height = sum([image.height for image in images]) + (len(images) - 1) * border_size
    else: 
        new_height = sum([image.height for image in images])

    new_width = max([image.width for image in images])

    # Create a new image with a black background
    new_image = Image.new('RGB', (new_width, new_height), color="white")

    y_offset = 0
    for image in images:
        paste_width = (new_width - image.width) // 2
        new_image.paste(image, (paste_width, y_offset))
        y_offset += image.height

        # Determine past width so the image is centered with respect to new_width

        if add_borders and y_offset < new_height:
            if tight:
                border_mask = Image.new('RGB', (image.width, border_size), color=color)
                new_image.paste(border_mask, (paste_width, y_offset))

            else: 
                border_mask = Image.new('RGB', (new_width, border_size), color=color)
                new_image.paste(border_mask, (0, y_offset))
            y_offset += border_size
    
    return new_image

def stitch_images_h(image1, image2):
    border_size = 40
    border_color="black"
    background_color="white"

    # Read image using pillow 
    new_width = image1.width + image2.width + border_size

    new_height = max(image1.height, image2.height)

    # Create a new image with a black background
    new_image = Image.new('RGB', (new_width, new_height), color=background_color)
    
    # Paste image1 and image2 onto the new image
    new_image.paste(image1, (0, (new_height - image1.height) // 2))

    new_image.paste(image2, (image1.width + border_size, (new_height - image2.height) // 2))
    
    new_image.paste(Image.new('RGB', (border_size//10, new_height), color=border_color), (image1.width +  (border_size - border_size//10)//2, 0))

    return new_image

def stitch_images_train(image1, image2, param, query):
    train0_image = stitch_images_h(image1, image2)

    train_image_path = f"{output_directory}/train/{concept}{param}_train{query}.jpg"
    train0_image.save(train_image_path)

    # To add grid cell train image (2x2, train row top, 2 empty white cells bottom)
    '''
    white_image1 = Image.new('RGB', (image1.width, image2.height), color="white")
    white_image2 = Image.new('RGB', (image2.width, image2.height), color="white")  
    white_images_stitched = stitch_images_h(white_image1, white_image2)

    final_image = stitch_images_v([train0_image, white_images_stitched],tight=False)

    train_image_path = f"{output_directory}/train/{concept}{param}_train{query}.1.jpg"
    final_image.save(train_image_path)
    '''

def stitch_images_test(stitched_images,  param, query):
    image1 = stitched_images[0]

    stitched_images_h = []

    for num, image in enumerate(stitched_images[1:]):
        # Add white border to the bottom of image
        stitched_img = stitch_images_h(image1, image)

        stitched_images_h.append(stitched_img)
        test_image_path = f"{output_directory}/test/{concept}{param}_test{query}_{num}.jpg"
        stitched_img.save(test_image_path)

for param in concept_to_parameters[concept]:
    stimuli_set = get_indexed_files(param)
    if query_repeats is None:
        query_repeats = len(stimuli_set)
    
    print("----------------------------------------------")
    print(f"Beginning Sub-Concept {concept} {param}")
    
    for query in list(range(query_repeats)):
        train_stimuli_set = format_files_by_type(stimuli_set, query, 'train')

        stitch_images_train(read_image(f"{stimuli_directory}/{train_stimuli_set[0]}").convert("RGB"), read_image(f"{stimuli_directory}/{train_stimuli_set[1]}").convert("RGB"), param, query)

        test_stimuli_set = format_files_by_type(stimuli_set, query, 'test')
        test_stimuli_input, test_stimuli_set = test_stimuli_set[0], test_stimuli_set[1:]

        test_stimuli_set.append(test_stimuli_input)

        stitched_images = [read_image(f"{stimuli_directory}/{test_stimuli_input}").convert("RGB")] 
        for num, test_stimuli in enumerate(test_stimuli_set):
            stitched_image = read_image(f"{stimuli_directory}/{test_stimuli}").convert("RGB")
            stitched_images.append(stitched_image) 

        stitch_images_test(stitched_images, param, query)
