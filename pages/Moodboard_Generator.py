from google import genai
import streamlit as st
from google.genai import types
from PIL import Image
import io
import os

# --- Configuration (unchanged) ---
PROJECT_ID = "<project-id>"
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
MODEL_ID = "gemini-2.5-flash-001"
IMG_MODEL = "imagen-4.0-generate-preview-06-06"

# --- Initialize Google GenAI Client (unchanged) ---
try:
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
except Exception as e:
    st.error(f"Failed to initialize Google GenAI Client: {e}")
    st.error(f"Project ID: {PROJECT_ID}, Location: {LOCATION}")
    st.stop()

# --- Moodboard Prompt Template and Fixed Values (unchanged) ---
moodboard_prompt_template = """
Generate a professional fashion design moodboard based on the following:
Title/Theme: {title}
Keywords/Vibes: {keywords}
Target Audience: {target_audience}
Layout notes:
* Layout: 2x6 grid with a column for color swatches on the side
* There must be a column of color swatches on the left side
* Include images reflecting the overall aesthetic and keywords, with an emphasis on incorporating objects, trims, textures, patterns, and other decorative elements.
* Color palette should complement the theme and vibes.
* At least three objects. These objects must be relevant to the prompt and be in active use.
* At least two images of scenery or landscape.
* Include diverse fashion concepts relevant to the target audience.
* Include fabric textures as swatches on the grid.
Color Swatches (Column 1):
* {color_1}
* {color_2}
* {color_3}
* {color_4}
* {color_5}
* {color_6}
Remember: {remember}
"""

fixed_colors = {
    "color_1": "Washed Stone",
    "color_2": "Rose Mist",
    "color_3": "Oat Milk",
    "color_4": "Sage Green",
    "color_5": "Charcoal Grey",
    "color_6": "Taupe",
}

remember_notes = """
* <note 1>
* <note 2>
* ...
"""

# --- Streamlit UI ---
st.title('Moodboard Generation 🎨')
st.header('Please enter your title, keywords, and target audience:')

# --- Session State for Inputs ---
if 'title_input' not in st.session_state:
    st.session_state.title_input = "Minimalist Spring Fashion"
if 'keywords' not in st.session_state:
    st.session_state.keywords = "Ethereal, organic textures, calm, sophisticated palette"
if 'target_audience' not in st.session_state:
    st.session_state.target_audience = "Young, urban women interested in sustainable style"

st.text_input("Moodboard Title:", key="title_input")
st.text_input("Keywords/Vibes:", key="keywords")
st.text_input("Target Audience:", key="target_audience")

st.write("---")

# --- Generate Moodboards Button ---
if st.button("Generate Moodboards ✨", use_container_width=True):
    if not st.session_state.title_input:
        st.warning("Please enter a Moodboard Title before generating.")
        st.stop()

    with st.spinner("Generating your moodboards... this might take a moment!"):
        try:
            final_prompt = moodboard_prompt_template.format(
                title=st.session_state.title_input,
                keywords=st.session_state.keywords,
                target_audience=st.session_state.target_audience,
                color_1=fixed_colors["color_1"],
                color_2=fixed_colors["color_2"],
                color_3=fixed_colors["color_3"],
                color_4=fixed_colors["color_4"],
                color_5=fixed_colors["color_5"],
                color_6=fixed_colors["color_6"],
                remember=remember_notes
            )

            st.info("Prompt sent to image generation model:")
            st.code(final_prompt)

            # Make the API call to Imagen
            response = client.models.generate_images(
                model=IMG_MODEL,
                prompt=final_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=4,
                    aspect_ratio="16:9",
                    safety_filter_level="block_only_high",
                    add_watermark=False,
                    person_generation="ALLOW_ADULT",
                ),
                )
            st.success("Moodboards generated successfully!")

            if response.generated_images:
                st.subheader(f"Generated Moodboard Variations ({len(response.generated_images)}):")
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
                            st.image(output_bytes, caption=f"Moodboard {i+1}")
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
