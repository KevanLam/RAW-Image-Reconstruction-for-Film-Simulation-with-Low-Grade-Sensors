import os
import cv2
import numpy as np

def merge_hdr_opencv(image_paths, exposure_times=None, output_dir="hdr_outputsopencv", output_prefix="HDR", tone_mapping=True):
    """
    Merge multiple exposure images into an HDR image using OpenCV and export as linear 16-bit TIFF.
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
    

    print("Aligning images...")
    alignMTB = cv2.createAlignMTB()
    alignMTB.process(images, images)
    

    print("Calculating Camera Response Function (CRF)...")
    calibrateDebevec = cv2.createCalibrateDebevec()
    responseDebevec = calibrateDebevec.process(images, exposure_times)
    

    print("Merging images into one HDR image...")
    mergeDebevec = cv2.createMergeDebevec()
    hdrDebevec = mergeDebevec.process(images, exposure_times, responseDebevec)
    

    hdr_path = os.path.join(output_dir, f"{output_prefix}.hdr")
    cv2.imwrite(hdr_path, hdrDebevec)
    print(f"Saved HDR image: {hdr_path}")
    
    print("Saving 16-bit linear TIFF...")
    

    max_luminance = np.max(hdrDebevec)
    print(f"Maximum HDR luminance value: {max_luminance}")
    
    if max_luminance > 0:
        # Use 80% of the available range to avoid clipping
        scale_factor = (0.8 * 65535) / max_luminance
    else:
        scale_factor = 1.0
    
    print(f"Using scale factor: {scale_factor}")
    tiff_16bit = np.clip(hdrDebevec * scale_factor, 0, 65535).astype(np.uint16)
    tiff_path = os.path.join(output_dir, f"{output_prefix}_16bit_linear.tiff")
    cv2.imwrite(tiff_path, tiff_16bit)
    print(f"Saved 16-bit linear TIFF: {tiff_path}")
    
    # Apply tone mapping if requested
    tone_mapped_paths = {}
    if tone_mapping:
        # Drago tone mapping
        print("Tone mapping using Drago's method...")
        tonemapDrago = cv2.createTonemapDrago(1.0, 0.7)
        ldrDrago = tonemapDrago.process(hdrDebevec)
        ldrDrago = 3 * ldrDrago
        drago_path = os.path.join(output_dir, f"{output_prefix}_Drago.jpg")
        cv2.imwrite(drago_path, ldrDrago * 255)
        print(f"Saved Drago tone-mapped image: {drago_path}")
        tone_mapped_paths['drago'] = drago_path
        
        # Reinhard tone mapping
        print("Tone mapping using Reinhard's method...")
        tonemapReinhard = cv2.createTonemapReinhard(1.5, 0, 0, 0)
        ldrReinhard = tonemapReinhard.process(hdrDebevec)
        reinhard_path = os.path.join(output_dir, f"{output_prefix}_Reinhard.jpg")
        cv2.imwrite(reinhard_path, ldrReinhard * 255)
        print(f"Saved Reinhard tone-mapped image: {reinhard_path}")
        tone_mapped_paths['reinhard'] = reinhard_path
        
        # Mantiuk tone mapping
        print("Tone mapping using Mantiuk's method...")
        tonemapMantiuk = cv2.createTonemapMantiuk(2.2, 0.85, 1.2)
        ldrMantiuk = tonemapMantiuk.process(hdrDebevec)
        ldrMantiuk = 3 * ldrMantiuk
        mantiuk_path = os.path.join(output_dir, f"{output_prefix}_Mantiuk.jpg")
        cv2.imwrite(mantiuk_path, ldrMantiuk * 255)
        print(f"Saved Mantiuk tone-mapped image: {mantiuk_path}")
        tone_mapped_paths['mantiuk'] = mantiuk_path
    
    # Return paths to saved files
    return {
        'hdr': hdr_path,
        'tiff_16bit': tiff_path,
        'tone_mapped': {
            'drago': tone_mapped_paths.get('drago'),
            'reinhard': tone_mapped_paths.get('reinhard'),
            'mantiuk': tone_mapped_paths.get('mantiuk')
        }
    }

def extract_exposure_time_from_raw(cr2_file):
    """
    Extract exposure time from RAW file metadata.
    
    Parameters:
    cr2_file (str): Path to CR2 file
    
    Returns:
    float: Exposure time in seconds
    """
    try:
        import rawpy
        raw = rawpy.imread(cr2_file)
        
        # rawpy
        try:
            exposure_time = raw.raw_metadata.exposure_time
            print(f"Found exposure time via rawpy: {exposure_time}")
            return exposure_time
        except:
            pass
        
        # exifread
        try:
            import exifread
            with open(cr2_file, 'rb') as f:
                tags = exifread.process_file(f)
                
                if 'EXIF ExposureTime' in tags:
                    exposure_str = str(tags['EXIF ExposureTime'])
                    
                    if '/' in exposure_str:
                        num, denom = exposure_str.split('/')
                        exposure_time = float(num) / float(denom)
                    else:
                        exposure_time = float(exposure_str)
                    
                    print(f"Extracted exposure time via exifread: {exposure_time}")
                    return exposure_time
        except ImportError:
            print("exifread not installed, trying alternative methods")
        except Exception as e:
            print(f"Error with exifread: {e}")
        
        # Pillow
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            
            with Image.open(cr2_file) as img:
                exif_data = img._getexif()
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == 'ExposureTime':
                            print(f"Extracted exposure time via Pillow: {value}")
                            return float(value)
        except ImportError:
            print("Pillow not installed, trying alternative methods")
        except Exception as e:
            print(f"Error with Pillow: {e}")
            
    except Exception as e:
        print(f"Error extracting metadata: {e}")
    
    # Failed
    print(f"Could not extract exposure time from {os.path.basename(cr2_file)}")
    return None

def process_cr2_files(dataset_path, scene_id, output_dir="hdr_outputsopencv"):
    """
    Process CR2 photos in a scene folder to create an HDR image.
    """
    scene_path = os.path.join(dataset_path, scene_id)
    
    if not os.path.exists(scene_path):
        print(f"Error: The folder '{scene_path}' does not exist.")
        return None
    
    # Find files
    image_files = sorted([os.path.join(scene_path, f) for f in os.listdir(scene_path) if f.endswith('.CR2')])
    
    if not image_files:
        print(f"Error: No RAW (.CR2) found in {scene_path}.")
        return None
    
    file_names = [f"'{os.path.basename(f)}'" for f in image_files]
    print(f"Processing files: [{', '.join(file_names)}]")
    
    # Real exp using metadata 
    exposure_times = []
    for cr2_file in image_files:
        exposure_time = extract_exposure_time_from_raw(cr2_file)
        
        if exposure_time is not None:
            exposure_times.append(exposure_time)
        else:
            # Relative exp
            default_exposures = [1/8000.0, 1/1000.0, 1/125.0, 1/15.0, 1/2.0]
            idx = len(exposure_times)
            if idx < len(default_exposures):
                fallback_exposure = default_exposures[idx]
            else:
                fallback_exposure = default_exposures[-1]
            
            print(f"Using relative exposure time for {os.path.basename(cr2_file)}: {fallback_exposure}")
            exposure_times.append(fallback_exposure)
    
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
            print("rawpy and/or imageio modules not found")
            return None
        except Exception as e:
            print(f"Error processing {os.path.basename(cr2_file)}: {e}")
    
    if len(jpeg_files) < 2:
        print("Not enough valid images(minimum 2)")
        return None
    
    exposure_times = exposure_times[:len(jpeg_files)]
    exposure_times = np.array(exposure_times, dtype=np.float32)
    
    print(f"Using extracted exposure times: {exposure_times}")
    
    hdr_path = merge_hdr_opencv(
        jpeg_files, 
        exposure_times=exposure_times,
        output_dir=output_dir,
        output_prefix=f"HDR_{scene_id}"
    )
    
    return hdr_path

def main():
    
    def use_cr2():
        print("Using second approach with CR2 files and metadata extraction...")
        dataset_path = "sihdr/raw"
        scene_id = "002"
        
        process_cr2_files(dataset_path, scene_id)


    use_cr2()

if __name__ == "__main__":
    main()