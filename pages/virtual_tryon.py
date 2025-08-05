import streamlit as st
import base64
import io
import os
import re
import timeit
from PIL import Image
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic import PredictResponse
from google.cloud import storage
import matplotlib.pyplot as plt # Keep this if you still want to use display_row for debugging or other purposes

# --- Configuration ---
PROJECT_ID = "<projectid>"  # @param {type:"string"}
LOCATION = "us-central1"  # @param ["us-central1"]

aiplatform.init(project=PROJECT_ID, location=LOCATION)

api_regional_endpoint = f"{LOCATION}-aiplatform.googleapis.com"
client_options = {"api_endpoint": api_regional_endpoint}
client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)

# IMPORTANT: Verify this model endpoint. Sometimes models are updated or
# have different versions. Check your Vertex AI console.
model_endpoint = f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/virtual-try-on-exp-05-31"
print(f"Prediction client initiated on project {PROJECT_ID} in {LOCATION}.")


# Parses the generated image bytes from the response and converts it
# to a PIL Image object.
# This function expects a single prediction dictionary, NOT the whole PredictResponse object.
def prediction_to_pil_image(
    prediction_dict: dict, size=(640, 640)
) -> Image.Image:
    """
    Parses the generated image bytes from a single prediction dictionary
    and converts it to a PIL Image object.
    """
    encoded_bytes_string = None
    # The Vertex AI Virtual Try-On model's prediction output structure is often like this:
    # { 'bytesBase64Encoded': '...' } or { 'image': { 'bytesBase64Encoded': '...' } }
    if "bytesBase64Encoded" in prediction_dict:
        encoded_bytes_string = prediction_dict["bytesBase64Encoded"]
    elif "image" in prediction_dict and isinstance(prediction_dict["image"], dict) and "bytesBase64Encoded" in prediction_dict["image"]:
        encoded_bytes_string = prediction_dict["image"]["bytesBase64Encoded"]
    # Add other potential keys if you discover them from debugging the API response

    if not encoded_bytes_string:
        raise ValueError("No base64 encoded image found in the prediction dictionary.")

    decoded_image_bytes = base64.b64decode(encoded_bytes_string)
    image_pil = Image.open(io.BytesIO(decoded_image_bytes))
    image_pil.thumbnail(size)
    return image_pil

# This function is good as is for converting Streamlit uploads to base64
def convert_uploaded_file_to_base64_string(uploaded_file):
    if uploaded_file is not None:
        try:
            raw_bytes = uploaded_file.getvalue()
            base64_bytes = base64.b64encode(raw_bytes)
            base64_string = base64_bytes.decode("utf-8")
            return base64_string
        except Exception as e:
            st.error(f"Error converting file to base64: {e}")
            return None
    return None

# --- Streamlit UI Setup ---
st.title('Virtual Try On')
st.markdown('''Please remember the current supported categories:''')
st.markdown(''' 1) Tops: shirts, hoodies, sweaters, tank tops, blouses''')
st.markdown(''' 2) Bottoms: pants, leggings, shorts, skirts dresses''')
st.markdown(''' 3) Footwear: Sneakers, boots, sandals, flats, heels, formal shoes''')

# --- Initialize Session State ---
# Store the RAW BYTES here from uploads
if 'vto_model_bytes' not in st.session_state:
    st.session_state.vto_model_bytes = None
if 'vto_prod_bytes' not in st.session_state:
    st.session_state.vto_prod_bytes = None
# Store the BASE64 ENCODED STRINGS here for the API call
if 'encoded_vto_model' not in st.session_state:
    st.session_state.encoded_vto_model = None
if 'encoded_vto_prod' not in st.session_state:
    st.session_state.encoded_vto_prod = None

# --- Upload Model Image ---
st.header('Upload a photo of your model')
uploaded_model = st.file_uploader(
    "Choose model image file (PNG, JPG, JPEG):",
    type=["png", "jpg", "jpeg"],
    key="model_uploader" # Ensure this key is unique
)
if uploaded_model is not None:
    # Store raw bytes for potential display or re-encoding
    st.session_state.vto_model_bytes = uploaded_model.getvalue()
    # Encode for API call and store the base64 string
    st.session_state.encoded_vto_model = convert_uploaded_file_to_base64_string(uploaded_model)
    st.info(f"Model image '{uploaded_model.name}' uploaded successfully!")
    # Display the uploaded image for confirmation
    st.image(st.session_state.vto_model_bytes, caption="Model Image", use_container_width=True)
elif st.session_state.vto_model_bytes is None:
    st.info("Please upload a model image.")

# --- Upload Product Image ---
st.header('Upload a photo of the product')
uploaded_item = st.file_uploader(
    "Choose product image file (PNG, JPG, JPEG):",
    type=["png", "jpg", "jpeg"],
    key="item_uploader" # Ensure this key is unique
)
if uploaded_item is not None:
    # Store raw bytes for potential display or re-encoding
    st.session_state.vto_prod_bytes = uploaded_item.getvalue()
    # Encode for API call and store the base64 string
    st.session_state.encoded_vto_prod = convert_uploaded_file_to_base64_string(uploaded_item)
    st.info(f"Product image '{uploaded_item.name}' uploaded successfully!")
    # Display the uploaded image for confirmation
    st.image(st.session_state.vto_prod_bytes, caption="Product Image", use_container_width=True)
elif st.session_state.vto_prod_bytes is None:
    st.info("Please upload a product image.")

# --- Generate Try-On Button and Logic ---
if st.session_state.encoded_vto_model and st.session_state.encoded_vto_prod:
    st.subheader("Ready to Try On!")
    if st.button("Generate try-on image"):
        try:
            with st.spinner("Generating your virtual try-on..."):
                # --- CALL VERTEX AI API ---
                sample_count = 1
                base_steps = 25 # Controls quality vs speed
                safety_setting = "block_low_and_above" # Or "block_none" if you expect certain content
                person_generation = "allow_adult" # Or "dont_allow"

                # The Vertex AI Virtual Try-On API expects specific instance formatting.
                # It expects a list of instances, and each instance is a dictionary.
                # The image data should be base64 encoded strings.
                instances_payload = [
                    {
                        "personImage": {"image": {"bytesBase64Encoded": st.session_state.encoded_vto_model}},
                        "productImages": [{"image": {"bytesBase64Encoded": st.session_state.encoded_vto_prod}}],
                    }
                ]

                parameters_payload = {
                    "sampleCount": sample_count,
                    "baseSteps": base_steps,
                    "safetySetting": safety_setting,
                    "personGeneration": person_generation,
                }

                response = client.predict(
                    endpoint=model_endpoint,
                    instances=instances_payload,
                    parameters=parameters_payload # Pass parameters here
                )
                # --- END API CALL ---

            if response and response.predictions:
                st.success("Virtual try on successful!")
                st.subheader(f"Generated try-on ({len(response.predictions)}):")

                num_predictions = len(response.predictions)
                # Use Streamlit columns for better display
                cols = st.columns(min(num_predictions, 4)) # Max 4 columns

                for i, prediction_data_dict in enumerate(response.predictions):
                    try:
                        # Process each prediction dictionary to get a PIL Image
                        pil_image = prediction_to_pil_image(prediction_data_dict)
                        
                        # Display in the correct column
                        with cols[i % len(cols)]:
                            st.write(f"Variation {i+1}:")
                            st.image(pil_image, caption=f"Try-on image {i+1}", use_container_width=True)
                            
                    except ValueError as ve: # Catch errors from prediction_to_pil_image
                        with cols[i % len(cols)]:
                            st.warning(f"Could not display try-on image {i+1}: {ve}")
                    except Exception as e: # Catch any other display errors
                        with cols[i % len(cols)]:
                            st.error(f"An error occurred displaying image {i+1}: {e}")
                            st.exception(e) # For detailed debugging

            else:
                st.warning("The API did not return any generated images or the response was empty.")
                # For debugging, print the entire response structure to see what was returned.
                # This is the most crucial step if you get no images.
                st.json(response.to_dict() if hasattr(response, 'to_dict') else str(response))

        except Exception as e:
            st.error(f"An error occurred during try-on: {e}")
            st.exception(e) # Provides full traceback for debugging
