import streamlit as st
from io import BytesIO
from typing import List, Optional, Dict
from PIL import Image
import base64
import zipfile
from diagram_utils import generate_diagram
from icon_utils import generate_icons
from auth import login_user, logout_user, is_authenticated, get_current_user

# --- UI setup ---
st.set_page_config(
    page_title="Image Card Generator",
    layout="wide",
)

# Authentication check
if not is_authenticated():
    st.title("Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if login_user(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")
    st.stop()

# Main app content (only shown if authenticated)
st.title("📸 Image Card Generator")

# Add logout button in the sidebar
with st.sidebar:
    st.write(f"Logged in as: {get_current_user()}")
    if st.button("Logout"):
        logout_user()
        st.rerun()

# Initialize session state for storing generated images and selected image
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = {
        "icons": {},  # Store icons by prompt
        "diagrams": {}  # Store diagrams by prompt
    }
if 'selected_image' not in st.session_state:
    st.session_state.selected_image = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'generation_progress' not in st.session_state:
    st.session_state.generation_progress = {
        "current": 0,
        "total": 0,
        "current_prompt": "",
        "current_variation": 0,
        "total_variations": 0,
        "type": ""  # "icon" or "diagram"
    }

# Model selection
model_type = st.selectbox(
    "Select Generator Type",
    ["diagram", "icon"],
    help="Choose the type of image generator to use"
)

# Main content area
main_col1, main_col2 = st.columns([2, 1])

with main_col1:
    # Variations selector (common for both generators)
    variations = st.number_input(
        "Number of variations",
        min_value=1,
        max_value=10,
        value=4 if model_type == "diagram" else 2,
        help=f"Choose how many variations to generate for each {'diagram' if model_type == 'diagram' else 'icon prompt'}"
    )

    # Prompt input
    if model_type == "icon":
        prompt = st.text_area(
            "Enter your icon prompts (one per line):",
            height=120,
            help=f"Enter multiple prompts, one per line. Each prompt will generate {variations} variations."
        )
    else:
        prompt = st.text_area(
            "Enter your diagram prompt:",
            height=120,
            help=f"Enter a single prompt to generate {variations} variations."
        )

    # Optional refs
    refs: List[BytesIO] = []
    uploaded = st.file_uploader(
        "(OPTIONAL) Upload up to 4 reference images (PNG/JPEG)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    if uploaded:
        for file in uploaded:
            data = file.read()
            refs.append(BytesIO(data))

    # Generate button
    if st.button("Generate Images"):
        if not prompt.strip():
            st.error("Please enter a prompt to generate images.")
        else:
            try:
                if model_type == "icon":
                    # Split prompts by newline and filter out empty lines
                    prompts = [p.strip()
                               for p in prompt.split('\n') if p.strip()]

                    # Calculate total images to be generated
                    total_images = len(prompts) * variations
                    st.session_state.generation_progress = {
                        "current": 0,
                        "total": total_images,
                        "current_prompt": "",
                        "current_variation": 0,
                        "total_variations": variations,
                        "type": "icon"
                    }

                    # Create placeholder for progress
                    progress_placeholder = st.empty()
                    progress_bar = progress_placeholder.progress(0)
                    status_placeholder = st.empty()

                    # Create placeholders for images
                    image_placeholders = []
                    cols = st.columns(2)
                    for i in range(total_images):
                        with cols[i % 2]:
                            image_placeholders.append(st.empty())

                    # Initialize session state for this generation
                    st.session_state.generated_images["icons"] = {}

                    # Generate images one by one
                    for img, prompt_text, iteration, current_prompt, total_prompts in generate_icons(
                        prompts=prompts,
                        refs=refs if refs else None,
                        variations=variations
                    ):
                        # Update progress
                        st.session_state.generation_progress["current"] += 1
                        st.session_state.generation_progress["current_prompt"] = prompt_text
                        st.session_state.generation_progress["current_variation"] = iteration

                        progress = st.session_state.generation_progress["current"] / \
                            st.session_state.generation_progress["total"]
                        progress_bar.progress(progress)

                        # Update status message
                        status_placeholder.text(
                            f"Generating variation {iteration} of {variations} for prompt {current_prompt}/{total_prompts}: {prompt_text}"
                        )

                        # Store image in session state
                        if prompt_text not in st.session_state.generated_images["icons"]:
                            st.session_state.generated_images["icons"][prompt_text] = [
                            ]
                        st.session_state.generated_images["icons"][prompt_text].append(
                            img)

                        # Display the image
                        current_idx = len(
                            st.session_state.generated_images["icons"][prompt_text]) - 1
                        with cols[current_idx % 2]:
                            st.image(img, use_container_width=True)

                            # Add download button for individual image
                            buf = BytesIO()
                            img.save(buf, format='PNG')
                            st.download_button(
                                label='Download',
                                data=buf.getvalue(),
                                file_name=f'icon_{prompt_text}_{iteration}.png',
                                mime='image/png',
                                key=f'download_{prompt_text}_{iteration}'
                            )

                            # Add edit button
                            if st.button("Edit This Image", key=f"edit_{prompt_text}_{iteration}"):
                                st.session_state.selected_image = img
                                st.session_state.edit_mode = True
                                st.rerun()

                    # Clear progress indicators after completion
                    progress_placeholder.empty()
                    status_placeholder.empty()

                else:  # diagram generation
                    # Calculate total images to be generated
                    total_images = variations
                    st.session_state.generation_progress = {
                        "current": 0,
                        "total": total_images,
                        "current_prompt": prompt,
                        "current_variation": 0,
                        "total_variations": variations,
                        "type": "diagram"
                    }

                    # Create placeholder for progress
                    progress_placeholder = st.empty()
                    progress_bar = progress_placeholder.progress(0)
                    status_placeholder = st.empty()

                    # Create placeholders for images
                    image_placeholders = []
                    cols = st.columns(2)
                    for i in range(variations):
                        with cols[i % 2]:
                            image_placeholders.append(st.empty())

                    # Initialize session state for this generation
                    st.session_state.generated_images["diagrams"] = {}

                    # Generate variations one by one
                    for img, current_variation, total_variations in generate_diagram(
                        prompt=prompt,
                        variations=variations,
                        refs=refs if refs else None
                    ):
                        # Update progress
                        st.session_state.generation_progress["current"] += 1
                        st.session_state.generation_progress["current_variation"] = current_variation

                        progress = st.session_state.generation_progress["current"] / \
                            st.session_state.generation_progress["total"]
                        progress_bar.progress(progress)

                        # Update status message
                        status_placeholder.text(
                            f"Generating diagram variation {current_variation} of {total_variations}"
                        )

                        # Store image in session state
                        if prompt not in st.session_state.generated_images["diagrams"]:
                            st.session_state.generated_images["diagrams"][prompt] = [
                            ]
                        st.session_state.generated_images["diagrams"][prompt].append(
                            img)

                        # Display the image
                        current_idx = len(
                            st.session_state.generated_images["diagrams"][prompt]) - 1
                        with cols[current_idx % 2]:
                            st.image(img, use_container_width=True)

                            # Add download button for individual image
                            buf = BytesIO()
                            img.save(buf, format='PNG')
                            st.download_button(
                                label='Download',
                                data=buf.getvalue(),
                                file_name=f'diagram_{current_variation}.png',
                                mime='image/png',
                                key=f'download_{current_variation}'
                            )

                            # Add edit button
                            if st.button("Edit This Image", key=f"edit_{current_variation}"):
                                st.session_state.selected_image = img
                                st.session_state.edit_mode = True
                                st.rerun()

                    # Clear progress indicators after completion
                    progress_placeholder.empty()
                    status_placeholder.empty()

            except Exception as e:
                st.error(f"Error generating images: {e}")

with main_col2:
    # Display generated images if they exist
    if st.session_state.generated_images:
        st.subheader("Generated Images")

        if model_type == "icon":
            # Display icons grouped by prompt
            for prompt_text, images in st.session_state.generated_images["icons"].items():
                st.write(f"**Prompt: {prompt_text}**")
                for i, img in enumerate(images):
                    st.image(img, use_container_width=True)

                    # Add download button for individual image
                    buf = BytesIO()
                    img.save(buf, format='PNG')
                    st.download_button(
                        label=f'Download Variation {i+1}',
                        data=buf.getvalue(),
                        file_name=f'icon_{prompt_text}_{i+1}.png',
                        mime='image/png',
                        key=f'download_single_{prompt_text}_{i}'
                    )
        else:
            # Display diagrams grouped by prompt
            for prompt_text, images in st.session_state.generated_images["diagrams"].items():
                st.write(f"**Prompt: {prompt_text}**")
                for i, img in enumerate(images):
                    st.image(img, use_container_width=True)

                    # Add download button for individual image
                    buf = BytesIO()
                    img.save(buf, format='PNG')
                    st.download_button(
                        label=f'Download Variation {i+1}',
                        data=buf.getvalue(),
                        file_name=f'diagram_{i+1}.png',
                        mime='image/png',
                        key=f'download_single_{i}'
                    )

        # Add download all button
        all_images_zip = BytesIO()
        with zipfile.ZipFile(all_images_zip, 'w') as zipf:
            if model_type == "icon":
                for prompt_text, images in st.session_state.generated_images["icons"].items():
                    for i, img in enumerate(images):
                        buf = BytesIO()
                        img.save(buf, format='PNG')
                        zipf.writestr(
                            f'icon_{prompt_text}_{i+1}.png', buf.getvalue())
            else:
                for prompt_text, images in st.session_state.generated_images["diagrams"].items():
                    for i, img in enumerate(images):
                        buf = BytesIO()
                        img.save(buf, format='PNG')
                        zipf.writestr(
                            f'diagram_{prompt_text}_{i+1}.png', buf.getvalue())

        st.download_button(
            label="Download All Images",
            data=all_images_zip.getvalue(),
            file_name="all_images.zip",
            mime="application/zip",
            key="download_all"
        )

# Edit mode section
if st.session_state.edit_mode and st.session_state.selected_image is not None:
    st.subheader("Edit Image")
    edit_col1, edit_col2 = st.columns(2)

    with edit_col1:
        st.image(st.session_state.selected_image, use_container_width=True)

        # Add option to upload a new image for editing
        uploaded_image = st.file_uploader(
            "Or upload a new image to edit:",
            type=["png", "jpg", "jpeg"],
            key="edit_upload"
        )

        if uploaded_image:
            st.session_state.selected_image = Image.open(uploaded_image)
            st.rerun()

    with edit_col2:
        edit_prompt = st.text_area("Enter edit prompt:", height=100)
        if st.button("Apply Edit"):
            with st.spinner("Editing image..."):
                try:
                    # Convert PIL Image to BytesIO for editing
                    img_byte_arr = BytesIO()
                    st.session_state.selected_image.save(
                        img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)

                    # Generate edited image using appropriate generator
                    if model_type == "icon":
                        edited_imgs = list(generate_icons(
                            prompts=edit_prompt,
                            refs=[img_byte_arr],
                            variations=1
                        ))
                        if edited_imgs:
                            # Get first image from generator
                            st.session_state.selected_image = edited_imgs[0][0]
                    else:
                        edited_imgs = list(generate_diagram(
                            prompt=edit_prompt,
                            variations=1,
                            refs=[img_byte_arr]
                        ))
                        if edited_imgs:
                            # Get first image from generator
                            st.session_state.selected_image = edited_imgs[0][0]
                    st.rerun()
                except Exception as e:
                    st.error(f"Error editing image: {e}")

        if st.button("Back to Gallery"):
            st.session_state.edit_mode = False
            st.session_state.selected_image = None
            st.rerun()
