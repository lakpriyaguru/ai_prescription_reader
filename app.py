from flask import Flask, render_template, request, send_from_directory, url_for
import os
import gc
import time
import torch
from craft_text_detector import Craft
from craft_text_detector.utils import Cutils
from rapidfuzz import process
import pandas as pd
import logging
from werkzeug.utils import secure_filename
from PIL import Image

# csv file
csv_file = "csv/bnf.csv"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize CRAFT model
device = "cuda" if torch.cuda.is_available() else "cpu"
craft = Craft(output_dir='craft_output/', crop_type="box", cuda=(device == "cuda"))
craft.load_craftnet_model()
Craftutils = Cutils()

# Load words from CSV and cache them
def load_words_from_csv(csv_file=csv_file, column_name="drug_name"):
    """Load words from a CSV file given the column name, handling errors gracefully."""
    try:
        df = pd.read_csv(csv_file, on_bad_lines="skip")
        return df[column_name].dropna().tolist()
    except Exception as e:
        logger.error(f"Error loading CSV file: {e}")
        return []

words_cache = load_words_from_csv()

# Find the closest word using fuzzy matching
def find_closest_word(misspelled_word, word_list):
    """Find the most similar word from the list using fuzzy matching."""
    if not word_list:
        return None
    best_match = process.extractOne(misspelled_word, word_list)
    return best_match[0] if best_match else None

# Fuzzy check for an array of words
def fuzz_check(misspelled_word_array):
    corrected_word_array = []
    for misspelled_word in misspelled_word_array:
        corrected_word = find_closest_word(misspelled_word, words_cache)
        corrected_word_array.append(corrected_word)
    return corrected_word_array

# Detect text in the image using CRAFT
def craft_detect_text(file_path):
    try:
        craft.detect_text(file_path)
        gc.collect()
        torch.cuda.empty_cache()
    except Exception as e:
        logger.error(f"Error detecting text with CRAFT: {e}")
        return None

# Flask Application
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Route to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files from the uploads folder."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Route to handle the index page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'imagefile' not in request.files:
            return render_template('index.html', prediction_status=False)
        
        file = request.files['imagefile']
        if file.filename == '':
            return render_template('index.html', prediction_status=False)
        
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Generate the URL for the uploaded image
            uploaded_image_url = url_for('uploaded_file', filename=filename)
            
            start_time = time.time()
            
            # Detect text regions using CRAFT
            craft_detect_text(file_path)

            # Predict medicines from the detected text
            medicines = Craftutils.predict(file_path)
            medicines_1 = medicines

            # Extract medicine names
            medicine_names = [medicine['name'] for medicine in medicines_1]
            print(medicine_names)

            # Check the spelling of the predicted medicines
            corrected_names = fuzz_check(medicine_names)
            print(corrected_names)

            # Replace the original names with the corrected names
            for i, corrected_name in enumerate(corrected_names):
                if corrected_name:
                    medicines_1[i]['name'] = corrected_name

            # Check the spelling of the predicted medicines
            # response_text = medicines
            response_text = medicines_1

            end_time = time.time()
            execution_time = round(end_time - start_time, 2)
            
            return render_template('index.html', prediction_status=True, detected_text=response_text, execution_time=execution_time, uploaded_image_url=uploaded_image_url)
    
    return render_template('index.html', prediction_status=False)

if __name__ == '__main__':
    app.run(debug=True)