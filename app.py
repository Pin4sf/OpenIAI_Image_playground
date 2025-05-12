import streamlit as st
from io import BytesIO
from typing import List, Optional
from PIL import Image
import base64
import zipfile
from openai_utils import generate_images
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
    st.session_state.generated_images = []
if 'selected_image' not in st.session_state:
    st.session_state.selected_image = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

# Model selection
model_type = st.selectbox(
    "Select Generator Type",
    ["default", "diagram", "icon"],
    help="Choose the type of image generator to use"
)

# Main content area
main_col1, main_col2 = st.columns([2, 1])

with main_col1:
    # Prompt input
    prompt = st.text_area("Enter your image prompt:", height=120)

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
            # Create placeholder for images
            image_placeholders = []
            cols = st.columns(2)
            for i in range(4):  # Changed to 4 images
                with cols[i % 2]:  # Use modulo to alternate between columns
                    image_placeholders.append(st.empty())

            try:
                # Generate images one by one
                for i in range(4):  # Changed to 4 images
                    # Updated progress message
                    with st.spinner(f"Generating image {i+1}/4..."):
                        imgs = generate_images(
                            prompt=prompt,
                            n=1,  # Generate one at a time
                            refs=refs if refs else None,
                            model_type=model_type
                        )
                        if imgs:
                            # Store the image in session state
                            st.session_state.generated_images.append(imgs[0])

                            # Create a container for this image and its controls
                            with cols[i % 2]:  # Use modulo to alternate between columns
                                # Display the image
                                st.image(imgs[0], use_container_width=True)

                                # Add download button for individual image
                                buf = BytesIO()
                                imgs[0].save(buf, format='PNG')
                                st.download_button(
                                    label='Download',
                                    data=buf.getvalue(),
                                    file_name=f'image_{len(st.session_state.generated_images)}.png',
                                    mime='image/png',
                                    key=f'download_{i}'
                                )

                                # Add edit button
                                if st.button("Edit This Image", key=f"edit_{i}"):
                                    st.session_state.selected_image = imgs[0]
                                    st.session_state.edit_mode = True
                                    st.rerun()

            except Exception as e:
                st.error(f"Error generating images: {e}")

with main_col2:
    # Display generated images if they exist
    if st.session_state.generated_images:
        st.subheader("Generated Images")
        for i, img in enumerate(st.session_state.generated_images):
            # Fixed deprecated parameter
            st.image(img, use_container_width=True)

            # Add download button for individual image
            buf = BytesIO()
            img.save(buf, format='PNG')
            st.download_button(
                label=f'Download Image {i+1}',
                data=buf.getvalue(),
                file_name=f'image_{i+1}.png',
                mime='image/png',
                key=f'download_single_{i}'
            )

        # Add download all button
        all_images_zip = BytesIO()
        with zipfile.ZipFile(all_images_zip, 'w') as zipf:
            for i, img in enumerate(st.session_state.generated_images):
                buf = BytesIO()
                img.save(buf, format='PNG')
                zipf.writestr(f'image_{i+1}.png', buf.getvalue())

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

                    # Generate edited image
                    edited_imgs = generate_images(
                        prompt=edit_prompt,
                        n=1,
                        refs=[img_byte_arr],
                        model_type=model_type
                    )
                    if edited_imgs:
                        st.session_state.selected_image = edited_imgs[0]
                        st.rerun()
                except Exception as e:
                    st.error(f"Error editing image: {e}")

        if st.button("Back to Gallery"):
            st.session_state.edit_mode = False
            st.session_state.selected_image = None
            st.rerun()
