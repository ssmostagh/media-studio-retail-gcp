# --- imports and configuration are correct ---
from google import genai
import streamlit as st
from PIL import Image
import io
import os
from google import genai
from google.genai import types

from google.genai.types import (
    SubjectReferenceConfig,
    SubjectReferenceImage,
    Image, # This is google.genai.types.Image
    ControlReferenceImage,
    ControlReferenceConfig,
    RawReferenceImage,
    EditImageConfig,
)
# --- Configuration ---
PROJECT_ID = "<project-id>"
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
IMG_MODEL = "imagen-3.0-capability-001"

# --- Initialize Google GenAI Client ---
try:
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
except Exception as e:
    st.error(f"Failed to initialize Google GenAI Client: {e}")
    st.error(f"Project ID: {PROJECT_ID}, Location: {LOCATION}")
    st.stop()


# --- Initialize Session State (unchanged) ---
if 'subject_img' not in st.session_state:
    st.session_state.subject_img = None
if 'cannyedge_img' not in st.session_state:
    st.session_state.cannyedge_img = None
if 'user_prompt' not in st.session_state:
    st.session_state.user_prompt = None        



# --- Streamlit UI (unchanged) ---
st.title('Print Items')

subject_file = st.file_uploader(
    "Choose a product image file (PNG, JPG, JPEG):",
    type=["png", "jpg", "jpeg"],
    key="subject_file"
)
if subject_file is not None:
    st.session_state.subject_img = subject_file.getvalue()
elif st.session_state.subject_img is None:
    default_image_path = "imgs/subject.png"
    if os.path.exists(default_image_path):
        try:
            with open(default_image_path, "rb") as f:
                st.session_state.subject_img = f.read()
        except Exception as e:
            st.warning(f"Could not load default image: {e}")
            st.session_state.subject_img = None
    else:
        st.session_state.subject_img = None

if st.session_state.subject_img:
    st.image(st.session_state.subject_img, caption="Current Product Image", width=250)
else:
    st.info("Please upload a product image.")

st.text_input("Prompt:", key="subject_description")

design_file = st.file_uploader(
    "Choose a design image file (PNG, JPG, JPEG):",
    type=["png", "jpg", "jpeg"],
    key="design_file"
)
if design_file is not None:
    st.session_state.cannyedge_img = design_file.getvalue()
elif st.session_state.cannyedge_img is None:
    default_image_path = "imgs/canny_edge.png"
    if os.path.exists(default_image_path):
        try:
            with open(default_image_path, "rb") as f:
                st.session_state.cannyedge_img = f.read()
        except Exception as e:
            st.warning(f"Could not load default image: {e}")
            st.session_state.cannyedge_img = None
    else:
        st.session_state.cannyedge_img = None

if st.session_state.cannyedge_img:
    st.image(st.session_state.cannyedge_img, caption="Current Design Image", width=250)
else:
    st.info("Please upload a design image.")

st.text_input("Prompt:", key="user_prompt")

# --- Generation Logic ---
if st.session_state.cannyedge_img and st.session_state.subject_img:
    st.subheader("Ready to Print!")
    if st.button("Generate customized product image"):
        try:
            with st.spinner("Generating customized product image... this might take a moment!"):

                # FIX: Wrap the raw bytes in the google.genai.types.Image class
                subject_image_sdk = Image(image_bytes=st.session_state.subject_img)
                design_image_sdk = Image(image_bytes=st.session_state.cannyedge_img)

                # Now, create the reference image objects using the wrapped Image objects
                subject_reference_image = SubjectReferenceImage(
                    reference_id=1,
                    reference_image=subject_image_sdk, # <-- FIX
                    config=SubjectReferenceConfig(
                        subject_description=st.session_state.subject_description, subject_type="SUBJECT_TYPE_PRODUCT"
                    )
                )

                control_reference_image = ControlReferenceImage(
                    reference_id=2,
                    reference_image=subject_image_sdk, # <-- FIX
                    config=ControlReferenceConfig(control_type="CONTROL_TYPE_CANNY"),
                )

                control_ref_img = ControlReferenceImage(
                    reference_id=4,
                    reference_image=design_image_sdk, # <-- FIX
                    config=ControlReferenceConfig(control_type="CONTROL_TYPE_CANNY"),
                )


                response = client.models.edit_image(
                    model=IMG_MODEL,
                    prompt=st.session_state.user_prompt,
                    reference_images=[subject_reference_image, control_reference_image, control_ref_img],
                    config=EditImageConfig(
                        edit_mode="EDIT_MODE_DEFAULT",
                        number_of_images=4,
                        seed=1,
                        safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
                    ),
                )
                
                # --- (The rest of your response handling code is unchanged and should work) ---
                st.success("Preview generation successful!")
                if response.generated_images:
                    st.subheader(f"Generated Preview ({len(response.generated_images)}):")
                    cols = st.columns(min(len(response.generated_images), 4)) 
                    
                    for i, generated_img_info in enumerate(response.generated_images):
                        with cols[i % len(cols)]: 
                            st.write(f"Variation {i+1}:")
                            output_bytes = None
                            if hasattr(generated_img_info, 'image_bytes') and generated_img_info.image_bytes:
                                output_bytes = generated_img_info.image_bytes
                            elif hasattr(generated_img_info, 'image') and hasattr(generated_img_info.image, '_pil_image') and generated_img_info.image._pil_image:
                                pil_img_obj = generated_img_info.image._pil_image
                                buf = io.BytesIO()
                                pil_img_obj.save(buf, format="PNG")
                                output_bytes = buf.getvalue()
                            if output_bytes:
                                st.image(output_bytes, caption=f"Preview {i+1}")
                            else:
                                st.warning(f"Could not retrieve image data for {i+1}.")

                else:
                    st.warning("The API did not return any generated images.")

        except Exception as e:
            st.error(f"Error during Imagen processing: {e}")
            st.exception(e)

