import os
import HDRutils
from HDRutils.merge import merge 

dataset_path = "sihdr/raw"
scene_id = "169"  # Change for different scenes
scene_path = os.path.join(dataset_path, scene_id)

if not os.path.exists(scene_path):
    print(f"Error: The folder '{scene_path}' does not exist.")
    exit()

image_files = sorted([os.path.join(scene_path, f) for f in os.listdir(scene_path) if f.endswith('.CR2')])

if not image_files:
    print(f"Error: No RAW (.CR2) images found in {scene_path}.")
    exit()

hdr_image, unsaturated_mask = merge(image_files)

hdr_output_path = f"hdr_outputs/HDR_{scene_id}.exr"
HDRutils.io.imwrite(hdr_output_path, hdr_image)
print(f"HDR image saved: {hdr_output_path}")

mask_output_path = f"hdr_outputs/Mask_{scene_id}.png"
HDRutils.io.imwrite(mask_output_path, unsaturated_mask)
print(f"Unsaturated mask saved: {mask_output_path}")
