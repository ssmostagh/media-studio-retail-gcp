from google import genai
import streamlit as st
from google.genai import types
from PIL import Image
import io
import os

# --- Configuration (unchanged) ---
PROJECT_ID = "<projectid>"
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
IMG_MODEL = "imagen-4.0-generate-preview-06-06"

# --- Initialize Google GenAI Client (unchanged) ---
try:
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
except Exception as e:
    st.error(f"Failed to initialize Google GenAI Client: {e}")
    st.error(f"Project ID: {PROJECT_ID}, Location: {LOCATION}")
    st.stop()

## Logo Prompt template
logo_template = """ Generate a business logo based on the following
Generate a professional logo design based on the following specifications:

Business Name: {business_name}
Business Description: {business_description}

--- DESIGN BRIEF ---

Logo Style: {style}
Visual Concept: {image_idea}

--- AESTHETICS ---

Core Aesthetics: minimalist, vector art, 2D, flat design, professional, clean
Color Palette: {colors}

--- FINAL INSTRUCTIONS ---

Remember:
- The final output must be a single logo concept isolated on a solid white background.
- This is a professional graphic design for a brand identity, NOT a photograph or a complex illustration.
- Prioritize the clarity and design of the icon/symbol. If text is included, it must be clean and legible, but the visual element is the primary focus.
"""

# --- Session State for Inputs ---
if 'business_name' not in st.session_state:
    st.session_state.business_name = "Cymbal"
if 'business_description' not in st.session_state:
    st.session_state.business_description = None
if 'image_idea' not in st.session_state:
    st.session_state.image_idea = None
if 'colors' not in st.session_state:
    st.session_state.color_palette = None
if 'logo_style' not in st.session_state:
    st.session_state.logo_style =  None

# --- Streamlit UI ---
st.title('Logo Generator')

st.text_input("Business Name:", key="business_name")
st.text_input("Business Description:", key="business_description")
st.text_input("Logo Idea:", key="image_idea")
st.text_input("Color Palette:", key="colors")
logo_style = st.selectbox(
    'What style would you like?', 
    ('Lettermark', 'Wordmark', 'Pictoral', 'Mascot', 'Combination Mark','Emblem'),
    )
st.write("---")

if st.button("Generate Logos"):
    if not st.session_state.business_name:
        st.warning("Please enter the name of your business before generating.")
        st.stop()
    with st.spinner("Generating logo options... this might take a moment!"):
        try:
            logo_prompt = logo_template.format(
                business_name=st.session_state.business_name,
                business_description=st.session_state.business_description,
                image_idea=st.session_state.image_idea,
                colors=st.session_state.colors,
                style=logo_style
            )
            st.info("Prompt sent to image generation model:")
            st.code(logo_prompt)

            response = client.models.generate_images(
                model=IMG_MODEL,
                prompt=logo_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=4,
                    aspect_ratio="1:1",
                    safety_filter_level="block_only_high",
                    add_watermark=False,
                    person_generation="ALLOW_ADULT",
                ),
                )
            st.success("Logos generated successfully!")
            if response.generated_images:
                st.subheader(f"Generated Logo ({len(response.generated_images)}):")
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
                            st.image(output_bytes, caption=f"Logo {i+1}")
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
