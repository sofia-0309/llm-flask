import io
import random
from pathlib import Path
import google.genai as genai
from config import GEMINI_API_KEY


class ImageGenerator:

    def __init__(self, patient, output_dir="generated_images"):
        self.patient = patient
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.model_name = "imagen-4.0-generate-001"

        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def build_prompt(self):
        """
        builds a realistic and safe medical image prompt based on patient attributes.
        """

        age = self.patient.age
        gender = self.patient.gender.lower()
        condition = self.patient.chief_complaint.lower()
        complaint = getattr(self.patient, "chief_complaint", condition)

        return (
            f"A realistic clinical photo of a {age}-year-old {gender} patient showing signs of {complaint}. "
            f"Neutral lighting, medical setting, natural skin texture, realistic anatomy, no distortions."
        )
    
    def generate_image(self, prompt_text):
        """
        calls the Google GenAI API to generate a single image.
        """

        result = self.client.models.generate_images(
            model=self.model_name,
            prompt=prompt_text,
            config=dict(
                number_of_images=1,
                output_mime_type="image/png",
                aspect_ratio="1:1"
            )
        )

        # get bytes of first generated image
        image_bytes = result.generated_images[0].image.image_bytes
        return image_bytes
    

    def generate_profile_picture(self):
        """
        Generates a non-clinical portrait of the patient for their profile picture.
        """

        age = self.patient.age
        gender = self.patient.gender.lower()

        # find way to make more diverse

        # weighted racial/ethnic distribution (adjust as needed)
        races = {
            "White": 0.16,
            "Black": 0.16,
            "Hispanic": 0.16,
            "Asian": 0.16,
            "Native American": 0.16,
            "Middle Eastern": 0.16,
        }

        # Select a race based on probability
        race = random.choices(list(races.keys()), weights=races.values(), k=1)[0].lower()

        self.patient.race = race

        # Build the prompt with diversity included
        prompt = (
            f"A professional headshot of a {age}-year-old {race} {gender} patient. "
            f"Neutral background, soft lighting, natural expression, realistic proportions, "
            f"medical profile photo style, front-facing portrait, appropriate attire."
        )

        result = self.client.models.generate_images(
            model=self.model_name,
            prompt=prompt,
            config=dict(
                number_of_images=1,
                output_mime_type="image/png",
                aspect_ratio="1:1"
            )
        )

        image_bytes = result.generated_images[0].image.image_bytes
        return image_bytes