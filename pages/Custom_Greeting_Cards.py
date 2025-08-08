from google import genai
import streamlit as st
from google.genai import types
from PIL import Image
import io
import os

# --- Configuration  ---
PROJECT_ID = "<projectid>"
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
IMG_MODEL = "imagen-4.0-generate-preview-06-06"

# --- Initialize Google GenAI Client ---
try:
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
except Exception as e:
    st.error(f"Failed to initialize Google GenAI Client: {e}")
    st.error(f"Project ID: {PROJECT_ID}, Location: {LOCATION}")
    st.stop()

## Greeting Card Template
greeting_card_template = """
Generate a greeting card illustration based on the following:
Reason: {card_reason}
Tone: {tone}
Image: {image_idea}
Color Palette: {colors}
Style: {card_style}

Remember:
- The output should be a single, high-quality illustration suitable for a greeting card.
- No text should be included in the illustration unless specified.
"""

# --- Session State for Inputs ---
if 'card_reason' not in st.session_state:
    st.session_state.card_reason = None
if 'tone' not in st.session_state:
    st.session_state.tone = None
if 'image_idea' not in st.session_state:
    st.session_state.image_idea = None
if 'colors' not in st.session_state:
    st.session_state.colors = None
if 'style' not in st.session_state:
    st.session_state.style =  None

# --- Streamlit UI ---
st.title('Custom Card Generator')
st.header("Let's generate a greeting card!!")
st.text_input("What's the reason for the card?", key="card_reason")
st.text_input("What tone would you like? (i.e: comedic, romantic, etc)", key="tone")
st.text_input("Do you have an idea of the image you'd like to see?", key="image_idea")
st.text_input("What colors do you want to see?", key="colors")
style = st.selectbox(
    'What style would you like?', 
    ('Cartoon', 'Minimal', 'Whimsical', 'Retro', 'Graphic Design','Illustration','Gothic'),
    )
st.write("---")

if st.button("Generate Card Options"):
    if not st.session_state.card_reason:
        st.warning("Please enter the reason for the card before generating.")
        st.stop()
    with st.spinner("Generating card options... this might take a moment!"):
        try:
            card_prompt = greeting_card_template.format(
                card_reason=st.session_state.card_reason,
                tone=st.session_state.tone,
                image_idea=st.session_state.image_idea,
                colors=st.session_state.colors,
                card_style=style
            )
            response = client.models.generate_images(
                model=IMG_MODEL,
                prompt=card_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=4,
                    aspect_ratio="3:4",
                    safety_filter_level="block_only_high",
                    add_watermark=False,
                    person_generation="ALLOW_ADULT",
                ),
            )
            st.success("Card options generated successfully!")
            if response.generated_images:
                st.subheader(f"Card ({len(response.generated_images)}):")
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
                            st.image(output_bytes, caption=f"Card {i+1}")
                            st.download_button("Download Card", output_bytes, f"logo_{i+1}.png", mime="image/png")
                        else:
                            st.warning(f"Could not retrieve image data for {i+1}.")
                            # For debugging, you can print the structure of generated_img_info
                            # st.json(generated_img_info.to_dict() if hasattr(generated_img_info, 'to_dict') else str(generated_img_info))
            else:
                st.warning("The API did not return any generated images.")
                # st.json(response.to_dict() if hasattr(response, 'to_dict') else str(response))

        except Exception as e:
            st.error(f"An error occurred during image editing: {e}")
            st.exception(e) # Provides full traceback for debugging
