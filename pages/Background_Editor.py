from google import genai
import streamlit as st
from PIL import Image as PILImage # Alias PIL.Image to avoid name collision
import io
import os
# Unused imports removed for clarity:
# pandas, StringIO, IPython.display, re, base64, time, urllib, tempfile

from google.genai.types import (
    EditImageConfig,
    Image, # This is google.genai.types.Image
    MaskReferenceConfig,
    MaskReferenceImage,
    RawReferenceImage,
    HarmBlockThreshold, # For safety_filter_level if passed directly
    # HarmCategory, # Not directly used here but good for safety_settings generally
)

# --- Configuration ---
PROJECT_ID = "<project-id>"
REGION = "us-central1"
# lang_model = "gemini-2.0-flash" # Not used in this specific script
# img_model = "imagen-3.0-fast-generate-001" # Not used in this specific script
edit_model = "imagen-3.0-capability-001" # This is the Imagen model for editing

LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")

# --- Initialize Client ---
try:
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
except Exception as e:
    st.error(f"Failed to initialize Google GenAI Client: {e}")
    st.error(f"Project ID: {PROJECT_ID}, Location: {LOCATION}")
    st.stop()

# --- Initialize Session State (Optional but good for prompt persistence) ---
if 'bg_edit_prompt' not in st.session_state:
    st.session_state.bg_edit_prompt = "A serene beach at sunset with calm waves"
if 'uploaded_image_bytes_for_bg_edit' not in st.session_state:
    st.session_state.uploaded_image_bytes_for_bg_edit = None

# --- Streamlit UI ---
st.title('Background Editor')
st.header('Upload a Photo to Edit its Background')

uploaded_file_obj = st.file_uploader(
    "Choose an image file (PNG, JPG, JPEG):",
    type=["png", "jpg", "jpeg"],
    key="bg_uploader"
)

# Handle image upload or use a default
if uploaded_file_obj is not None:
    st.session_state.uploaded_image_bytes_for_bg_edit = uploaded_file_obj.getvalue()
    st.info("Image uploaded successfully!")
elif st.session_state.uploaded_image_bytes_for_bg_edit is None: # Only try default if nothing in session state
    # Optional: Load a default image if you have one
    default_image_path = "imgs/default_for_bg_edit.png" # Create this path and image
    if os.path.exists(default_image_path):
        try:
            with open(default_image_path, "rb") as f:
                st.session_state.uploaded_image_bytes_for_bg_edit = f.read()
            st.info(f"No file uploaded. Using default image: {default_image_path}")
        except Exception as e:
            st.warning(f"Could not load default image: {e}")
            st.session_state.uploaded_image_bytes_for_bg_edit = None # Ensure it's None
    else:
        st.info("No file uploaded and no default image found. Please upload an image.")
        st.session_state.uploaded_image_bytes_for_bg_edit = None


# Proceed if we have image bytes
if st.session_state.uploaded_image_bytes_for_bg_edit:
    st.subheader("Original Image:")
    st.image(st.session_state.uploaded_image_bytes_for_bg_edit, caption="Your Image", width=400)

    st.subheader("Describe the New Background")
    # Use session state for the prompt text input
    st.session_state.bg_edit_prompt = st.text_input(
        "Enter description for the new background:",
        value=st.session_state.bg_edit_prompt,
        key="bg_edit_prompt_input"
    )

    if st.button("🎨 Edit Background", key="submit_bg_edit"):
        if not st.session_state.bg_edit_prompt.strip():
            st.warning("Please enter a description for the background.")
        else:
            with st.spinner("Generating new backgrounds... This might take a few moments."):
                try:
                    # Prepare the source image for the API
                    source_gcp_image = Image(image_bytes=st.session_state.uploaded_image_bytes_for_bg_edit)

                    raw_ref_image = RawReferenceImage(
                        reference_image=source_gcp_image,
                        reference_id=0
                    )
                    mask_ref_image = MaskReferenceImage(
                        reference_id=1,
                        reference_image=None, # No explicit mask needed for MASK_MODE_BACKGROUND
                        config=MaskReferenceConfig(mask_mode="MASK_MODE_BACKGROUND"),
                    )

                    # Make the API call to Imagen
                    response = client.models.edit_image(
                        model=edit_model,
                        prompt=st.session_state.bg_edit_prompt,
                        reference_images=[raw_ref_image, mask_ref_image],
                        config=EditImageConfig(
                            edit_mode="EDIT_MODE_BGSWAP",
                            number_of_images=4, # <<< REQUEST 4 IMAGES
                            # aspect_ratio="1:1", # Optional: "16:9", "ORIGINAL"
                            seed=42, # Optional: for reproducibility, or omit for variety
                            safety_filter_level=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE, # Your choice
                            person_generation="ALLOW_ADULT", # Your choice
                        ),
                    )

                    st.success("Backgrounds edited successfully!")

                    if response.generated_images:
                        st.subheader(f"Generated Background Variations ({len(response.generated_images)}):")
                        # Display images in columns for better layout
                        cols = st.columns(min(len(response.generated_images), 4)) # Max 4 columns, or as many as images
                        
                        for i, generated_img_info in enumerate(response.generated_images):
                            with cols[i % len(cols)]: # Cycle through columns
                                st.write(f"Variation {i+1}:")
                                output_bytes = None
                                if hasattr(generated_img_info, 'image_bytes') and generated_img_info.image_bytes:
                                    output_bytes = generated_img_info.image_bytes
                                elif hasattr(generated_img_info, 'image') and hasattr(generated_img_info.image, '_pil_image') and generated_img_info.image._pil_image:
                                    # If SDK gives a PIL image, convert to bytes for st.image
                                    pil_img_obj = generated_img_info.image._pil_image
                                    buf = io.BytesIO()
                                    pil_img_obj.save(buf, format="PNG") # Or JPEG
                                    output_bytes = buf.getvalue()
                                
                                if output_bytes:
                                    st.image(output_bytes, caption=f"Edited version {i+1}")
                                else:
                                    st.warning(f"Could not retrieve image data for edited version {i+1}.")
                                    # For debugging, you can print the structure of generated_img_info
                                    # st.json(generated_img_info.to_dict() if hasattr(generated_img_info, 'to_dict') else str(generated_img_info))
                    else:
                        st.warning("The API did not return any generated images.")
                        # st.json(response.to_dict() if hasattr(response, 'to_dict') else str(response))


                except Exception as e:
                    st.error(f"An error occurred during image editing: {e}")
                    st.exception(e) # Provides full traceback for debugging

else: # This else corresponds to 'if st.session_state.uploaded_image_bytes_for_bg_edit:'
    # This message is shown if no image is uploaded and no default is loaded.
    if not uploaded_file_obj: # only show if uploader is also empty (avoid showing if default load failed but uploader empty)
        st.warning("Please upload an image to edit its background.")
