import streamlit as st
from io import BytesIO
from typing import List, Optional, Dict
from PIL import Image
import base64
import zipfile
from diagram_utils import generate_diagram, DIAGRAM_SYSTEM_PROMPT
from icon_utils import generate_icons, ICON_SYSTEM_PROMPT
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
if 'system_prompt' not in st.session_state:
    st.session_state.system_prompt = DIAGRAM_SYSTEM_PROMPT

# Model selection
model_type = st.selectbox(
    "Select Generator Type",
    ["diagram", "icon"],
    help="Choose the type of image generator to use"
)

# Update system prompt based on model selection
if model_type == "diagram":
    st.session_state.system_prompt = DIAGRAM_SYSTEM_PROMPT
else:
    st.session_state.system_prompt = ICON_SYSTEM_PROMPT

# Main content area
main_col1, main_col2 = st.columns([2, 1])

with main_col1:
    # System prompt editing
    st.subheader("System Prompt")
    system_prompt = st.text_area(
        "Edit the system prompt:",
        value=st.session_state.system_prompt,
        height=200,
        help="Edit the system prompt that guides the image generation"
    )
    st.session_state.system_prompt = system_prompt

    # Prompt input
    if model_type == "icon":
        prompt = st.text_area(
            "Enter your icon prompts (one per line):",
            height=120,
            help="Enter multiple prompts, one per line. Each prompt will generate one image."
        )
    else:
        prompt = st.text_area(
            "Enter your diagram prompt:",
            height=120,
            help="Enter a single prompt to generate one image."
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
                with st.spinner("Generating image(s)..."):
                    if model_type == "icon":
                        prompts = [p.strip()
                                   for p in prompt.split('\n') if p.strip()]
                        cols = st.columns(2)
                        # Append to previous images instead of overwriting
                        if "icons" not in st.session_state.generated_images:
                            st.session_state.generated_images["icons"] = {}
                        for img, prompt_text in generate_icons(
                            prompts=prompts,
                            refs=refs if refs else None,
                            system_prompt=st.session_state.system_prompt
                        ):
                            if prompt_text not in st.session_state.generated_images["icons"]:
                                st.session_state.generated_images["icons"][prompt_text] = [
                                ]
                            st.session_state.generated_images["icons"][prompt_text].append(
                                img)
                            current_idx = len(
                                st.session_state.generated_images["icons"][prompt_text]) - 1
                            with cols[current_idx % 2]:
                                st.image(img, use_container_width=True)
                                buf = BytesIO()
                                img.save(buf, format='PNG')
                                st.download_button(
                                    label='Download',
                                    data=buf.getvalue(),
                                    file_name=f'icon_{prompt_text}_{current_idx}.png',
                                    mime='image/png',
                                    key=f'download_{prompt_text}_{current_idx}'
                                )
                                if st.button("Edit This Image", key=f"edit_{prompt_text}_{current_idx}"):
                                    st.session_state.selected_image = img
                                    st.session_state.edit_mode = True
                                    st.rerun()
                    else:
                        # Diagram generation
                        img = generate_diagram(
                            prompt=prompt,
                            refs=refs if refs else None,
                            system_prompt=st.session_state.system_prompt
                        )
                        if img:
                            if "diagrams" not in st.session_state.generated_images:
                                st.session_state.generated_images["diagrams"] = {
                                }
                            if prompt not in st.session_state.generated_images["diagrams"]:
                                st.session_state.generated_images["diagrams"][prompt] = [
                                ]
                            st.session_state.generated_images["diagrams"][prompt].append(
                                img)
                            st.image(img, use_container_width=True)
                            buf = BytesIO()
                            img.save(buf, format='PNG')
                            st.download_button(
                                label='Download',
                                data=buf.getvalue(),
                                file_name=f'diagram_{len(st.session_state.generated_images["diagrams"][prompt])-1}.png',
                                mime='image/png',
                                key=f'download_diagram_{len(st.session_state.generated_images["diagrams"][prompt])-1}'
                            )
                            if st.button("Edit This Image", key=f"edit_diagram_{len(st.session_state.generated_images['diagrams'][prompt])-1}"):
                                st.session_state.selected_image = img
                                st.session_state.edit_mode = True
                                st.rerun()
            except Exception as e:
                st.error(f"Error generating images: {e}")

with main_col2:
    # Display generated images if they exist
    if st.session_state.generated_images:
        st.subheader("Generated Images")
        images_to_zip = []
        if model_type == "icon":
            for prompt_text, images in st.session_state.generated_images["icons"].items():
                st.write(f"**Prompt: {prompt_text}**")
                for idx, img in enumerate(images):
                    st.image(img, use_container_width=True)
                    buf = BytesIO()
                    img.save(buf, format='PNG')
                    st.download_button(
                        label='Download',
                        data=buf.getvalue(),
                        file_name=f'icon_{prompt_text}_{idx+1}.png',
                        mime='image/png',
                        key=f'download_single_{prompt_text}_{idx}'
                    )
                    images_to_zip.append(
                        (f'icon_{prompt_text}_{idx+1}.png', buf.getvalue()))
        else:
            for prompt_text, images in st.session_state.generated_images["diagrams"].items():
                st.write(f"**Prompt: {prompt_text}**")
                for idx, img in enumerate(images):
                    st.image(img, use_container_width=True)
                    buf = BytesIO()
                    img.save(buf, format='PNG')
                    st.download_button(
                        label='Download',
                        data=buf.getvalue(),
                        file_name=f'diagram_{idx+1}.png',
                        mime='image/png',
                        key=f'download_single_diagram_{idx}'
                    )
                    images_to_zip.append(
                        (f'diagram_{idx+1}.png', buf.getvalue()))
        # Show Download All (ZIP) if more than one image
        if len(images_to_zip) > 1:
            all_images_zip = BytesIO()
            with zipfile.ZipFile(all_images_zip, 'w') as zipf:
                for fname, data in images_to_zip:
                    zipf.writestr(fname, data)
            st.download_button(
                label="Download All (ZIP)",
                data=all_images_zip.getvalue(),
                file_name="all_images.zip",
                mime="application/zip",
                key="download_all_zip"
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
                            system_prompt=st.session_state.system_prompt
                        ))
                        if edited_imgs:
                            # Get first image from generator
                            st.session_state.selected_image = edited_imgs[0][0]
                    else:
                        edited_img = generate_diagram(
                            prompt=edit_prompt,
                            refs=[img_byte_arr],
                            system_prompt=st.session_state.system_prompt
                        )
                        if edited_img:
                            st.session_state.selected_image = edited_img
                    st.rerun()
                except Exception as e:
                    st.error(f"Error editing image: {e}")

        if st.button("Back to Gallery"):
            st.session_state.edit_mode = False
            st.session_state.selected_image = None
            st.rerun()
