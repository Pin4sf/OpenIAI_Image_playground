import os
import base64
from io import BytesIO
from typing import List, Optional, Dict, Literal

from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image

# Load API key from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# System prompts for different GPT models
SYSTEM_PROMPTS = {
    "diagram": """You are an expert visual communicator and designer. Your task is to create advanced, yet easy-to-understand, hand-drawn style diagrams for business, marketing, and organizational workflows. Your diagrams should:

Use a minimalist, illustrated hand-drawn aesthetic, similar to visual note-taking or whiteboard sketching.
Include clearly labeled characters (e.g., Product Manager, Strategist) with simple illustrated avatars.
Keep padding around the image and no information should get cut off
Depict communication tools and challenges using icons (e.g., email, meetings, Slack, confusion emoji, clock, warning signs).
Use dotted arrows to indicate communication or information flow between roles.
Communicate common workplace challenges like misalignment, information silos, and tool overload.
Arrange people and interactions horizontally in logical teams or departments (e.g., Merchandising, Marketing, Agency).
Always prioritize clarity, balance, and visual storytelling. Include icons, facial expressions, and directional cues to emphasize communication bottlenecks or inefficiencies.
Do not rewrite the entire prompt in the diagram. Only clearly illustrate the concept.
Always only follow the style of the images provided in the knowledge bank.""",

    "icon": """You are a visual design assistant that generates prompts for creating icons in a luxurious, minimalistic, slightly 3D style with a transparent background. The background should always be transparent.

When the user inputs a shortphrase, your job is to analyze the text input and decide what text and icon the card should contain. Then automatically format it into the following prompt structure:

"Create an image of a minimalistic luxury slight 3D style card icon with a transparent background, like a $10,000 design team's work, of the word "xyz" with a graphic of a "abc". Make the background transparent."

Always consider the full prompt exactly as above with the text inserted cleanly into "xyz" and "abc" — replacing "xyz" with the label/text the icon should feature, and "abc" with the visual graphic or symbol they mentioned. Do not include anything else in your reply.

Make sure it is in a card style. The text and any graphic on the card should be flat 2D black printed on the card. the card should be slightly 3d and the colour of the card should always be #f9f1dd. Make sure the background is ALWAYS FULLY TRANSPARENT."""
}

# Define valid image sizes
ImageSize = Literal['256x256', '512x512',
                    '1024x1024', '1536x1024', '1024x1536', 'auto']


def generate_images(
    prompt: str,
    n: int = 4,
    size: ImageSize = 'auto',
    refs: Optional[List[BytesIO]] = None,
    model_type: str = "default"
) -> List[Image.Image]:
    """
    Generate `n` images for the given prompt. Optionally include reference images.
    Returns a list of PIL Images.
    """
    try:
        # Get the system prompt if model_type is specified
        system_prompt = SYSTEM_PROMPTS.get(model_type, "")

        # Combine system prompt with user prompt if model_type is specified
        full_prompt = f"{system_prompt}\n\nUser request: {prompt}" if system_prompt else prompt

        if refs:
            # For edit-mode, ensure the image is in the correct format
            processed_refs = []
            for ref in refs:
                # Convert to PNG format
                img = Image.open(ref)
                png_buffer = BytesIO()
                img.save(png_buffer, format='PNG')
                png_buffer.seek(0)
                processed_refs.append(png_buffer)

            # For edit-mode
            response = client.images.edit(
                model="dall-e-2",
                image=processed_refs[0],  # Use the first image for editing
                prompt=full_prompt,
                n=n,
                size=size
            )
        else:
            # For generation
            response = client.images.generate(
                model="gpt-image-1",
                prompt=full_prompt,
                n=n,
                size=size
            )

        if not response or not response.data:
            raise Exception("No images were generated")

        images: List[Image.Image] = []
        for datum in response.data:
            if datum.b64_json:
                img_bytes = base64.b64decode(datum.b64_json)
                images.append(Image.open(BytesIO(img_bytes)))
        return images
    except Exception as e:
        raise Exception(f"Error generating images: {str(e)}")
