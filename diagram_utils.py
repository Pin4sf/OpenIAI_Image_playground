import os
import base64
from io import BytesIO
from typing import List, Optional, Literal, Generator
import streamlit as st
from openai import OpenAI
from PIL import Image

# Initialize OpenAI client with API key from secrets
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# System prompt for diagram generation
DIAGRAM_SYSTEM_PROMPT = """You are an expert visual communicator and designer. Your task is to create advanced, yet easy-to-understand, hand-drawn style diagrams for business, marketing, and organizational workflows. Your diagrams should:

Use a minimalist, illustrated hand-drawn aesthetic, similar to visual note-taking or whiteboard sketching.
Include clearly labeled characters (e.g., Product Manager, Strategist) with simple illustrated avatars.
Keep padding around the image and no information should get cut off
Depict communication tools and challenges using icons (e.g., email, meetings, Slack, confusion emoji, clock, warning signs).
Use dotted arrows to indicate communication or information flow between roles.
Communicate common workplace challenges like misalignment, information silos, and tool overload.
Arrange people and interactions horizontally in logical teams or departments (e.g., Merchandising, Marketing, Agency).
Always prioritize clarity, balance, and visual storytelling. Include icons, facial expressions, and directional cues to emphasize communication bottlenecks or inefficiencies.
If there is too much text or visual content try to reduce the font and keep space for visual clarity.
Have a proper whiteboard background for clear image.
Do not rewrite the entire prompt in the diagram. Only clearly illustrate the concept.
Always only follow the style of the images provided in the knowledge bank."""

# Define valid image sizes
ImageSize = Literal['256x256', '512x512',
                    '1024x1024', '1536x1024', '1024x1536', 'auto']


def generate_diagram(
    prompt: str,
    size: ImageSize = 'auto',
    refs: Optional[List[BytesIO]] = None,
    system_prompt: Optional[str] = None
) -> Optional[Image.Image]:
    """
    Generate a single diagram image for the given prompt.

    Args:
        prompt: The diagram prompt
        size: Image size
        refs: Optional reference images for editing
        system_prompt: Optional custom system prompt to use
    """
    try:
        # Use provided system prompt or default
        current_system_prompt = system_prompt if system_prompt is not None else DIAGRAM_SYSTEM_PROMPT

        # Combine system prompt with user prompt
        full_prompt = f"{current_system_prompt}\n\nUser request: {prompt}"

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
                model="gpt-image-1",
                image=processed_refs[0],  # Use the first image for editing
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
                    return Image.open(BytesIO(img_bytes))
        return None

    except Exception as e:
        raise Exception(f"Error generating diagram image: {str(e)}")
