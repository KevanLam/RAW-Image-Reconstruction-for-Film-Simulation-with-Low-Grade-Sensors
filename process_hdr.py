import HDRutils
import cv2
import numpy as np
import os
from HDRutils.merge import merge 

# Get the absolute path of the script's location
base_path = os.path.dirname(os.path.abspath(__file__))

# Set dataset path using absolute reference
scene_id = "001"
scene_path = os.path.join(base_path, "Kalantri_dataset_training", scene_id)

# Print the resolved path for debugging
print("Looking for folder at:", scene_path)

# Verify the folder exists
if not os.path.exists(scene_path):
    print(f"Error: The folder '{scene_path}' does not exist.")
    exit()

# List files in the folder to confirm access
print("Files in folder:", os.listdir(scene_path))

# Ensure the scene folder exists
if not os.path.exists(scene_path):
    print(f"Error: The folder '{scene_path}' does not exist.")
    exit()

# Get all TIFF image files in sorted order
image_files = sorted([os.path.join(scene_path, f) for f in os.listdir(scene_path) if f.endswith('.tif')])

if not image_files:
    print(f"Error: No .tif images found in {scene_path}.")
    exit()

# Load images using OpenCV
images = [cv2.imread(img, cv2.IMREAD_UNCHANGED) for img in image_files]

# Read exposure values from exposure.txt
exposure_file = os.path.join(scene_path, "exposure.txt")
if not os.path.exists(exposure_file):
    print(f"Error: Exposure file '{exposure_file}' is missing.")
    exit()

exposure_times = np.loadtxt(exposure_file)

# Merge images into an HDR image using HDRutils
hdr_image = merge(images, exposure_times, exp=exposure_times)

# Save the HDR image using OpenCV
hdr_output_path = f"hdr_outputs/HDR_{scene_id}.exr"
cv2.imwrite(hdr_output_path, hdr_image)
print(f"HDR image saved: {hdr_output_path}")

# Apply OpenCV Drago tone mapping
tonemap = cv2.createTonemapDrago(gamma=1.0)
ldr_image = tonemap.process(hdr_image)
ldr_image = np.clip(ldr_image * 255, 0, 255).astype(np.uint8)  # Normalize


# Save the tone-mapped image using OpenCV
ldr_output_path = f"tone_mapped_outputs/LDR_{scene_id}.jpg"
cv2.imwrite(ldr_output_path, (ldr_image * 255).astype(np.uint8))
print(f"Tone-mapped image saved: {ldr_output_path}")