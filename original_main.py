# main.py
import os
import glob
import uuid
from config import IMAGES_DIR, PREPROCESSED_DIR, CELLS_DIR, MODEL_PATH, PDF_DPI
from modules.pdf_converter import convert_pdf_to_images
from modules.image_preprocessor import preprocess_image
from modules.name_prn_extractor import extract_name_prn
from modules.cell_extractor import extract_cells
from modules.answer_predictor import predict_all_answers
from modules.answer_predictor import predict_cell
from utils.prn_utils import normalize_prn



def process_pdf(pdf_path):
    """Process a single PDF end-to-end and return one result dict per page."""
    results = []

    # ----- create a **fresh** folder for this PDF -----
    pdf_id = os.path.splitext(os.path.basename(pdf_path))[0]
    """run_dir = os.path.join(IMAGES_DIR, f"run_{pdf_id}_{uuid.uuid4().hex[:8]}")
    os.makedirs(run_dir, exist_ok=True)

    # convert only this PDF into images inside that folder
    image_paths = convert_pdf_to_images(pdf_path, run_dir, PDF_DPI)
    image_paths = sorted(image_paths)  # keep stable order"""
    run_dir = os.path.join(IMAGES_DIR, f"run_{pdf_id}_{uuid.uuid4().hex[:8]}")
    os.makedirs(run_dir, exist_ok=True)

    # convert PDF pages to images (order preserved)
    image_paths = convert_pdf_to_images(pdf_path, run_dir, PDF_DPI)


    for page_num, image_path in enumerate(image_paths, 1):
        try:
            preprocessed_path = preprocess_image(image_path, PREPROCESSED_DIR)

            name, prn = extract_name_prn(preprocessed_path)
            safe_prn = normalize_prn(prn)

            new_image_path = os.path.join(run_dir, f"{safe_prn}.jpg")

            # handle duplicate PRNs
            counter = 1
            while os.path.exists(new_image_path):
                new_image_path = os.path.join(run_dir, f"{safe_prn}_dup{counter}.jpg")
                counter += 1

            os.rename(image_path, new_image_path)
            image_path = new_image_path


            page_cells_dir = os.path.join(CELLS_DIR, f"{pdf_id}_page_{page_num}")
            os.makedirs(page_cells_dir, exist_ok=True)
            #cell_paths = extract_cells(preprocessed_path, page_cells_dir)

            #answers = predict_all_answers(cell_paths, MODEL_PATH)

            cell_images = extract_cells(image_path)
            answers = {}
            for qno, ((row, col), cell_img) in enumerate(sorted(cell_images.items()), start=1):
                answers[qno] = predict_cell(cell_img)

            results.append(
                {
                    "page": page_num,
                    "name": name,
                    "prn": prn,
                    "answers": answers,
                    "image_path": preprocessed_path,
                }
            )

            # optional logging
            print("\n" + "=" * 70)
            print(f"Page {page_num}")
            print(f"Name: {name}")
            print(f"PRN: {prn}")
            print("=" * 70 + "\n")

        except Exception as e:
            print(f"ERROR on page {page_num}: {e}")
            continue

    return results
"""def normalise_prn_for_filename(prn: str) -> str:
    #Convert PRN to 3-digit string for filenames.
    
    digits = "".join(c for c in prn if c.isdigit())
    if not digits:
        return "000"

    if len(digits) >= 3:
        return digits[-3:]           # take last 3 digits
    return digits.zfill(3)"""       # pad to 3 digits



def main():
    """Main entry point."""
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model not found at {MODEL_PATH}")
        return
    
    pdf_files = glob.glob(os.path.join(INPUT_DIR, "*.pdf"))
    
    if not pdf_files:
        print(f"No PDFs found in {INPUT_DIR}")
        return
    
    print(f"\nProcessing {len(pdf_files)} PDF(s)...\n")
    
    for pdf_path in pdf_files:
        print(f"Processing: {os.path.basename(pdf_path)}")
        try:
            process_pdf(pdf_path)
        except Exception as e:
            print(f"ERROR: {str(e)}")


if __name__ == "__main__":
    main()