
"""
Course: CSE 351
Assignment: 06
Author: [Your Name]

Process images using a multiprocessing pipeline:
1. Smooth images
2. Convert images to grayscale
3. Detect edges and save the final images
"""

import multiprocessing as mp
import os
import cv2

from cse351 import *

# Folders
INPUT_FOLDER = "faces"
STEP3_OUTPUT_FOLDER = "step3_edges"

# Image processing parameters
GAUSSIAN_BLUR_KERNEL_SIZE = (5, 5)
CANNY_THRESHOLD1 = 75
CANNY_THRESHOLD2 = 155

# Allowed image extensions
ALLOWED_EXTENSIONS = [".jpg"]

# Queue settings
QUEUE_SIZE = 32


# ---------------------------------------------------------
def smooth_worker(queue1, queue2):
    """Read original images and smooth them."""
    cv2.setNumThreads(1)

    while True:
        filename = queue1.get()

        if filename is None:
            break

        try:
            image = cv2.imread(filename)

            if image is None:
                print(f"Could not read image: {filename}")
                continue

            smoothed = cv2.GaussianBlur(
                image, GAUSSIAN_BLUR_KERNEL_SIZE, 0
            )

            queue2.put((os.path.basename(filename), smoothed))

        except Exception as e:
            print(f"Error smoothing {filename}: {e}")


# ---------------------------------------------------------
def grayscale_worker(queue2, queue3):
    """Read smoothed images and convert them to grayscale."""
    cv2.setNumThreads(1)

    while True:
        item = queue2.get()

        if item is None:
            break

        filename, image = item

        try:
            grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            queue3.put((filename, grayscale))

        except Exception as e:
            print(f"Error converting {filename} to grayscale: {e}")


# ---------------------------------------------------------
def edge_worker(queue3, output_folder):
    """Detect edges and save the final images."""
    cv2.setNumThreads(1)

    while True:
        item = queue3.get()

        if item is None:
            break

        filename, image = item

        try:
            edges = cv2.Canny(
                image, CANNY_THRESHOLD1, CANNY_THRESHOLD2
            )

            output_path = os.path.join(output_folder, filename)

            if not cv2.imwrite(output_path, edges):
                print(f"Could not save image: {output_path}")

        except Exception as e:
            print(f"Error detecting edges for {filename}: {e}")


# ---------------------------------------------------------
def run_image_processing_pipeline():
    """Run the three-stage multiprocessing pipeline."""

    print("Starting image processing pipeline...")

    os.makedirs(STEP3_OUTPUT_FOLDER, exist_ok=True)

    # Get the original image filenames.
    filenames = [
        os.path.join(INPUT_FOLDER, filename)
        for filename in os.listdir(INPUT_FOLDER)
        if os.path.splitext(filename)[1].lower()
        in ALLOWED_EXTENSIONS
    ]

    filenames.sort()

    print(f"Found {len(filenames)} images.")

    if not filenames:
        print("No images found to process.")
        return

    # Use a portion of the available CPU cores for each stage.
    cpu_count = os.cpu_count() or 4
    workers_per_stage = max(1, cpu_count // 3)

    print(f"CPU cores available: {cpu_count}")
    print(f"Workers per stage: {workers_per_stage}")

    # Create queues between the stages.
    queue1 = mp.Queue(maxsize=QUEUE_SIZE)
    queue2 = mp.Queue(maxsize=QUEUE_SIZE)
    queue3 = mp.Queue(maxsize=QUEUE_SIZE)

    # Create the three groups of worker processes.
    smooth_processes = [
        mp.Process(target=smooth_worker, args=(queue1, queue2))
        for _ in range(workers_per_stage)
    ]

    grayscale_processes = [
        mp.Process(target=grayscale_worker, args=(queue2, queue3))
        for _ in range(workers_per_stage)
    ]

    edge_processes = [
        mp.Process(
            target=edge_worker,
            args=(queue3, STEP3_OUTPUT_FOLDER)
        )
        for _ in range(workers_per_stage)
    ]

    # Start every worker before adding jobs to the queues.
    for process in smooth_processes:
        process.start()

    for process in grayscale_processes:
        process.start()

    for process in edge_processes:
        process.start()

    # Stage 1: Send original image paths to the smoothing workers.
    for filename in filenames:
        queue1.put(filename)

    # Tell each smoothing worker to stop after finishing its jobs.
    for _ in smooth_processes:
        queue1.put(None)

    # Wait until all smoothing workers finish before stopping stage 2.
    for process in smooth_processes:
        process.join()

    for _ in grayscale_processes:
        queue2.put(None)

    # Wait until all grayscale workers finish before stopping stage 3.
    for process in grayscale_processes:
        process.join()

    for _ in edge_processes:
        queue3.put(None)

    for process in edge_processes:
        process.join()

    # Close queue resources.
    queue1.close()
    queue2.close()
    queue3.close()

    # Verify the number of final images.
    output_count = sum(
        1
        for filename in os.listdir(STEP3_OUTPUT_FOLDER)
        if os.path.splitext(filename)[1].lower()
        in ALLOWED_EXTENSIONS
    )

    print("\nImage processing pipeline finished!")
    print(f"Original images: {len(filenames)}")
    print(f"Final images created: {output_count}")
    print(f"Original folder: '{INPUT_FOLDER}'")
    print(f"Final output folder: '{STEP3_OUTPUT_FOLDER}'")

    if output_count == len(filenames):
        print("All images were processed successfully.")
    else:
        print("Warning: Some images may not have been processed.")


# ---------------------------------------------------------
if __name__ == "__main__":
    mp.freeze_support()

    log = Log(show_terminal=True)
    log.start_timer("Processing Images")

    if not os.path.isdir(INPUT_FOLDER):
        print(f"Error: The input folder '{INPUT_FOLDER}' was not found.")
        print("Extract the images into the faces folder first.")
    else:
        run_image_processing_pipeline()

    log.write()
    log.stop_timer("Total Time To complete")
