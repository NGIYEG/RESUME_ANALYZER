from django.db.models.signals import post_save
from django.dispatch import receiver
from Applicantapp.models import Applicant
from Extractionapp.models import ResumeExtraction
from django.conf import settings
from PIL import Image
import os
from ocr.trocr_model import processor, model
import torch


from ocr.extract_insights import extract_insights

@receiver(post_save, sender=Applicant)
def extract_text_with_trocr(sender, instance, created, **kwargs):
    if not instance.converted_images:
        return

    extraction, _ = ResumeExtraction.objects.get_or_create(applicant=instance)

    all_text = ""

    for img_rel_path in instance.converted_images:
        img_path = os.path.join(settings.MEDIA_ROOT, img_rel_path)
        image = Image.open(img_path).convert("RGB")

        pixel_values = processor(images=image, return_tensors="pt").pixel_values
        generated_ids = model.generate(pixel_values)
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        all_text += generated_text + "\n\n"

    extraction.extracted_text = all_text

    # ---- NEW NLP EXTRACTION ----
    insights = extract_insights(all_text)

    extraction.skills = insights.get("skills")
    extraction.work_experience = insights.get("work_experience")
    extraction.projects = insights.get("projects")
    extraction.education = insights.get("education")

    extraction.processed = True
    extraction.save()
