from pdf2image import convert_from_path

pages = convert_from_path("your.pdf")
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-printed")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-printed")

text = ""

for page in pages:
    pixel_values = processor(images=page, return_tensors="pt").pixel_values
    generated_ids = model.generate(pixel_values)
    page_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    text += page_text + "\n\n"

print(text)
