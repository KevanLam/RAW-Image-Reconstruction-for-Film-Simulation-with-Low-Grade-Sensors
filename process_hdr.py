import os
import HDRutils
from HDRutils.merge import merge 

dataset_path = "sihdr/raw"
scene_id = "064"  # Change for different scenes
scene_path = os.path.join(dataset_path, scene_id)

if not os.path.exists(scene_path):
    print(f"Error: The folder '{scene_path}' does not exist.")
    exit()

image_files = sorted([os.path.join(scene_path, f) for f in os.listdir(scene_path) if f.endswith('.CR2')])

if not image_files:
    print(f"Error: No RAW (.CR2) images found in {scene_path}.")
    exit()

file_names = [f"'{os.path.basename(f)}'" for f in image_files]
print(f"files = [{', '.join(file_names)}]")

# Merge with exposure estimation enabled
hdr_image = merge(image_files, estimate_exp='mst')[0]

hdr_output_path = f"hdr_outputs/HDR_{scene_id}.exr"
HDRutils.io.imwrite(hdr_output_path, hdr_image)
print(f"HDR image saved: {hdr_output_path}")