import os
import fitz
from PIL import Image
import google.generativeai as genai
import requests
import shutil
from tqdm import tqdm
import app.constraints as constraints 
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import DocumentConverter, PdfFormatOption
from dotenv import load_dotenv
import urllib.request
import random

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def download_file(url: str):
    file = urllib.request.urlopen(url)
    
    local_filename = str(random.getrandbits(128)) + ".pdf"
    with open(f'{local_filename}.pdf','wb') as output:
        output.write(file.read())
    
    return local_filename

def get_extractor():
    pipeline_options = PdfPipelineOptions(do_table_structure=True)
    pipeline_options.table_structure_options.mode = (
        TableFormerMode.ACCURATE
    )  # use more accurate TableFormer model
    pipeline_options.ocr_options.lang = ["en", "th"]  # example of languages for EasyOCR

    doc_converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )

    return doc_converter

def extract_image_from_pdf(pdf_path, prov, output_dir="extracted_images"):
    page_number = prov[0]["page_no"]
    bbox = prov[0]["bbox"]
    l = bbox["l"]
    t = bbox["t"]
    r = bbox["r"]
    b = bbox["b"]

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Open the PDF
    pdf_document = fitz.open(pdf_path)

    # Get the first page (since your coordinates are from page 1)
    page = pdf_document[page_number - 1]

    # Define the rectangle (bbox) for extraction
    page_height = page.rect.height
    rect = fitz.Rect(l, page_height - t, r, page_height - b)

    # Get the pixel map of the specified region
    pix = page.get_pixmap(clip=rect)
    # Convert to PIL Image and save
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Close the PDF
    pdf_document.close()
    return img


def describe_image(img):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        [
            "Write a very short, describe this picture. Without your opinion, just describe what you see.",
            img,
        ],
        stream=False,
    )
    return "<!image - " + response.text + ">"

def extract_text_from_pdf(pdf_path, extractor):
    if "http:" in pdf_path or "https:" in pdf_path:
        pdf_path = download_file(pdf_path)
    
    result = extractor.convert(pdf_path)

    result_dict = result.document.export_to_dict()
    img_desc = []

    index = 0
    for prov in tqdm(result_dict["pictures"]):
        if index > constraints.MAX_IMAGE_DESCRIBE:
            img_desc.append("")
            continue

        img = extract_image_from_pdf(pdf_path, prov["prov"])
        if img.size[0] < 150 or img.size[1] < 150:
            img_desc.append("<icon or logo>")
            continue

        img_desc.append(describe_image(img))
        index += 1

    markdown = result.document.export_to_markdown()

    images_count = markdown.count("<!-- image -->")
    for i in range(images_count):
        markdown = markdown.replace("<!-- image -->", img_desc[i], 1)

    return markdown
