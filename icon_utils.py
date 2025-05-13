import os
import base64
from io import BytesIO
from typing import List, Optional, Literal, Union, Generator
import streamlit as st
from openai import OpenAI
from PIL import Image

# Initialize OpenAI client with API key from secrets
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# System prompt for icon generation
ICON_SYSTEM_PROMPT = """You are a visual design assistant that generates prompts for creating icons in a luxurious, minimalistic, slightly 3D style with a transparent background. The background should always be transparent.

When the user inputs a shortphrase, your job is to analyze the text input and decide what text and icon the card should contain. Then automatically format it into the following prompt structure:

"Create an image of a minimalistic luxury slight 3D style card icon with a transparent background, like a $10,000 design team's work, of the word "xyz" with a graphic of a "abc". Make the background transparent."

Always consider the full prompt exactly as above with the text inserted cleanly into "xyz" and "abc" — replacing "xyz" with the label/text the icon should feature, and "abc" with the visual graphic or symbol they mentioned. Do not include anything else in your reply.

Make sure it is in a card style. The text and any graphic on the card should be flat 2D black printed on the card. the card should be slightly 3d and the colour of the card should always be #f9f1dd. Make sure the background is ALWAYS FULLY TRANSPARENT."""

# Define valid image sizes
ImageSize = Literal['256x256', '512x512',
                    '1024x1024', '1536x1024', '1024x1536', 'auto']


def generate_icons(
    prompts: Union[str, List[str]],
    size: ImageSize = 'auto',
    refs: Optional[List[BytesIO]] = None,
    system_prompt: Optional[str] = None
) -> Generator[tuple[Image.Image, str], None, None]:
    """
    Generate icon images for each prompt in the list.
    If a single string is provided, it will be treated as a list with one item.
    Yields tuples of (image, prompt) as they are generated.

    Args:
        prompts: Single prompt or list of prompts
        size: Image size
        refs: Optional reference images for editing
        system_prompt: Optional custom system prompt to use
    """
    try:
        # Convert single prompt to list
        if isinstance(prompts, str):
            prompts = [prompts]

        # Use provided system prompt or default
        current_system_prompt = system_prompt if system_prompt is not None else ICON_SYSTEM_PROMPT

        for prompt in prompts:
            # Combine system prompt with user prompt
            full_prompt = f"{current_system_prompt}\n\nUser request: {prompt}"

            if refs:
                # For edit-mode, ensure the image is in the correct format
                processed_refs = []
                for ref in refs:
                    img = Image.open(ref)
                    png_buffer = BytesIO()
                    img.save(png_buffer, format='PNG')
                    png_buffer.seek(0)
                    processed_refs.append(png_buffer)

                # For edit-mode
                response = client.images.edit(
                    model="gpt-image-1",
                    image=processed_refs[0],
                    prompt=full_prompt,
                    n=1,
                    size=size
                )
            else:
                # For generation
                response = client.images.generate(
                    model="gpt-image-1",
                    prompt=full_prompt,
                    n=1,
                    size=size
                )

            if response and response.data:
                for datum in response.data:
                    if datum.b64_json:
                        img_bytes = base64.b64decode(datum.b64_json)
                        img = Image.open(BytesIO(img_bytes))
                        yield img, prompt

    except Exception as e:
        raise Exception(f"Error generating icon images: {str(e)}")
