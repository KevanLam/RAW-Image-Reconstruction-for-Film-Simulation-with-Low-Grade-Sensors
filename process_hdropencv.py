import os
import cv2
import numpy as np

def merge_hdr_opencv(image_paths, exposure_times=None, output_dir="hdr_outputsopencv", output_prefix="HDR", tone_mapping = True):
    """
    Merge multiple exposure images into an HDR image using OpenCV.
    
    Parameters:
    image_paths (list): List of paths to input images
    exposure_times (list): List of exposure times for each image. If None, will attempt to estimate.
    output_dir (str): Directory to save output files
    output_prefix (str): Prefix for output filenames
    tone_mapping (bool): Whether to apply tone mapping
    
    Returns:
    str: Path to the saved HDR image
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Read images
    print("Reading images...")
    images = []
    for img_path in image_paths:
        im = cv2.imread(img_path)
        if im is None:
            print(f"Failed to read image: {img_path}")
            continue
        images.append(im)
    
    if len(images) < 2:
        raise ValueError("At least 2 images are required for HDR merge")
    
    # Handle exposure times
    if exposure_times is None:
        print("No exposure times provided. Using simple estimation...")
        exposure_times = np.array([1/8000.0, 1/1000.0, 1/125.0, 1/15.0, 1/2.0], dtype=np.float32)
        exposure_times = exposure_times[:len(images)]
    
    exposure_times = np.array(exposure_times, dtype=np.float32)
    
    print(f"Using exposure times: {exposure_times}")
    
    # Align input images
    print("Aligning images...")
    alignMTB = cv2.createAlignMTB()
    alignMTB.process(images, images)
    
    # Obtain Camera Response Function
    print("Calculating Camera Response Function (CRF)...")
    calibrateDebevec = cv2.createCalibrateDebevec()
    responseDebevec = calibrateDebevec.process(images, exposure_times)
    
    # Merge images into an HDR linear image
    print("Merging images into one HDR image...")
    mergeDebevec = cv2.createMergeDebevec()
    hdrDebevec = mergeDebevec.process(images, exposure_times, responseDebevec)
    
    hdr_path = os.path.join(output_dir, f"{output_prefix}.hdr")
    cv2.imwrite(hdr_path, hdrDebevec)
    print(f"Saved HDR image: {hdr_path}")
    
    # Apply tone mapping if requested
    if tone_mapping:
        # Drago tone mapping
        print("Tone mapping using Drago's method...")
        tonemapDrago = cv2.createTonemapDrago(1.0, 0.7)
        ldrDrago = tonemapDrago.process(hdrDebevec)
        ldrDrago = 3 * ldrDrago
        drago_path = os.path.join(output_dir, f"{output_prefix}_Drago.jpg")
        cv2.imwrite(drago_path, ldrDrago * 255)
        print(f"Saved Drago tone-mapped image: {drago_path}")
        
        # Reinhard tone mapping
        print("Tone mapping using Reinhard's method...")
        tonemapReinhard = cv2.createTonemapReinhard(1.5, 0, 0, 0)
        ldrReinhard = tonemapReinhard.process(hdrDebevec)
        reinhard_path = os.path.join(output_dir, f"{output_prefix}_Reinhard.jpg")
        cv2.imwrite(reinhard_path, ldrReinhard * 255)
        print(f"Saved Reinhard tone-mapped image: {reinhard_path}")
        
        # Mantiuk tone mapping
        print("Tone mapping using Mantiuk's method...")
        tonemapMantiuk = cv2.createTonemapMantiuk(2.2, 0.85, 1.2)
        ldrMantiuk = tonemapMantiuk.process(hdrDebevec)
        ldrMantiuk = 3 * ldrMantiuk
        mantiuk_path = os.path.join(output_dir, f"{output_prefix}_Mantiuk.jpg")
        cv2.imwrite(mantiuk_path, ldrMantiuk * 255)
        print(f"Saved Mantiuk tone-mapped image: {mantiuk_path}")
    
    return hdr_path

def process_cr2_files(dataset_path, scene_id, output_dir="hdr_outputsopencv"):
    """
    Process CR2 files for a specific scene and create HDR image.
    This function handles RAW files using OpenCV's HDR merging.
    
    Parameters:
    dataset_path (str): Path to the dataset directory
    scene_id (str): ID of the scene to process
    output_dir (str): Directory to save output files
    
    Returns:
    str: Path to the saved HDR image
    """
    scene_path = os.path.join(dataset_path, scene_id)
    
    if not os.path.exists(scene_path):
        print(f"Error: The folder '{scene_path}' does not exist.")
        return None
    
    # Find files
    image_files = sorted([os.path.join(scene_path, f) for f in os.listdir(scene_path) if f.endswith('.CR2')])
    
    if not image_files:
        print(f"Error: No RAW (.CR2) images found in {scene_path}.")
        return None
    
    file_names = [f"'{os.path.basename(f)}'" for f in image_files]
    print(f"Processing files: [{', '.join(file_names)}]")
    

    # Using exposure times
    exposure_times = np.array([1/8000.0, 1/1000.0, 1/125.0, 1/15.0, 1/2.0], dtype=np.float32)
    
    # Ensure we have the right number of exposure times for the images
    if len(exposure_times) != len(image_files):
        print(f"Warning: Number of exposure times ({len(exposure_times)}) doesn't match number of images ({len(image_files)}).")
        
        if len(exposure_times) > len(image_files):
            exposure_times = exposure_times[:len(image_files)]
        else:
            last_exposure = exposure_times[-1]
            exposure_times = np.append(exposure_times, 
                                      [last_exposure] * (len(image_files) - len(exposure_times)))
    
    # Convert CR2 to JPEG (OpenCV can't directly process CR2)
    jpeg_files = []
    for cr2_file in image_files:
        jpeg_file = cr2_file.replace('.CR2', '.jpg')
        
        try:
            import rawpy
            import imageio
            
            with rawpy.imread(cr2_file) as raw:

                rgb = raw.postprocess(
                    use_camera_wb=True,
                    half_size=False,
                    no_auto_bright=True,
                    output_color=rawpy.ColorSpace.sRGB
                )
                
                imageio.imsave(jpeg_file, rgb)
                
                jpeg_files.append(jpeg_file)
                print(f"Converted {os.path.basename(cr2_file)} to JPEG")
        except ImportError:
            print("rawpy and/or imageio modules not found. Please install them for CR2 conversion.")
            print("Try: pip install rawpy imageio")
            return None
    
    hdr_path = merge_hdr_opencv(
        jpeg_files, 
        exposure_times=exposure_times,
        output_dir=output_dir,
        output_prefix=f"HDR_{scene_id}"
    )
    
    return hdr_path

def main():
    """
    def test():
        print("Using first approach with JPEG files...")
        filenames = ["img_0.033.jpg", "img_0.25.jpg", "img_2.5.jpg", "img_15.jpg"]
        
        times = np.array([ 1/30.0, 0.25, 2.5, 15.0 ], dtype=np.float32)
        times = times[:len(filenames)]
        image_paths = [os.path.join(os.getcwd(), f) for f in filenames]
        merge_hdr_opencv(image_paths, times)
    """
    
    def use_cr2():
        print("Using second approach CR2 files...")
        dataset_path = "sihdr/raw"
        scene_id = "191"
        
        process_cr2_files(dataset_path, scene_id)


    #test()
    use_cr2()

if __name__ == "__main__":
    main()