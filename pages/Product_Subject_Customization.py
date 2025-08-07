from google import genai
import streamlit as st
import io
import os
import json # For parsing Gemini's JSON output if we go that route

from google.genai.types import (
    GenerateContentConfig,
    HarmBlockThreshold,
    HarmCategory,
    MediaResolution,
    Part,
    EditImageConfig,
    Image,
    SubjectReferenceImage,
    SubjectReferenceConfig, # Ensure this is imported if used
)

# --- Configuration ---
PROJECT_ID = "<projectid>"
REGION = "us-central1"
lang_model = "gemini-2.0-flash" # YOUR Gemini model
edit_model = "imagen-3.0-capability-001" # YOUR Imagen model
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", REGION) # Use REGION as default

# --- Initialize Client ---
try:
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
except Exception as e:
    st.error(f"Failed to initialize Google GenAI Client: {e}"); st.stop()

# --- Initialize Session State ---
if 'user_base_imagen_prompt' not in st.session_state: # User's initial idea for the scene
    st.session_state.user_base_imagen_prompt = "A lifestyle shot of [1] on a marble countertop."
if 'final_imagen_prompt_for_imagen' not in st.session_state: # This will hold the prompt ready for IMAGEN
    st.session_state.final_imagen_prompt_for_imagen = ""
if 'uploaded_subject_image_details' not in st.session_state:
    st.session_state.uploaded_subject_image_details = []
if 'ran_once_without_upload' not in st.session_state:
    st.session_state.ran_once_without_upload = False
# No need for 'gemini_output_for_display' if 'final_imagen_prompt_for_imagen' serves as the single source of truth for display

# --- Streamlit UI ---
st.title('Product Customization Studio BETA')

st.header('1. Upload Product Reference Image(s)')
st.caption("The first image will be the primary reference for `[1]`.")
subject_files_widget_output = st.file_uploader( # Renamed for clarity
    "Choose image(s) of your product:",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
    key="subject_uploader_widget_key"
)

if subject_files_widget_output: # New files uploaded
    st.session_state.uploaded_subject_image_details = []
    for file_obj in subject_files_widget_output:
        st.session_state.uploaded_subject_image_details.append(
            {"bytes": file_obj.getvalue(), "type": file_obj.type, "name": file_obj.name}
        )
    # If new images are uploaded, the old Gemini prompt might be irrelevant
    st.session_state.final_imagen_prompt_for_imagen = "" # Clear old prompt

# Display uploaded images
if st.session_state.uploaded_subject_image_details:
    st.write("Your Uploaded Images:")
    # ... (your image display columns logic - seems fine) ...
    num_images = len(st.session_state.uploaded_subject_image_details)
    cols_per_row = min(4, num_images) if num_images > 0 else 1
    for i in range(0, num_images, cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            img_idx = i + j
            if img_idx < num_images and j < len(cols):
                cols[j].image(st.session_state.uploaded_subject_image_details[img_idx]["bytes"],
                              caption=f"{st.session_state.uploaded_subject_image_details[img_idx]['name']}", width=150)
else:
    if not st.session_state.ran_once_without_upload:
        st.info("Please upload at least one product image.")
    st.session_state.ran_once_without_upload = True

st.header('2. Describe Desired Scene')
st.caption("Use `[1]` to refer to your uploaded product (first image). Gemini can help refine this.")
# User's initial input for the scene
st.session_state.user_base_imagen_prompt = st.text_area(
    "Your idea for the scene:",
    value=st.session_state.user_base_imagen_prompt,
    height=100,
    key="user_base_prompt_for_gemini_key"
)

st.header('3. AI Prompt Generation & Image Customization')

# System instruction for Gemini (placeholder `[1]` version)
system_instruction_for_gemini = """
You are an expert GenAI prompting assistant for Imagen 3, specializing in subject customization that uses an explicit subject reference placeholder `[1]`.
Goal: Take reference product image(s) and a user's scene idea, and produce a detailed Imagen 3 prompt.

**Crucial for Imagen Subject Reference:**
- In the output prompt, when referring to the main product from the reference image(s), you **MUST use the placeholder `[1]`**.
- Imagen uses `[1]` to link to the subject reference images.

**Prompt Generation Guidelines:**
- **Product Context (Optional):** Briefly add 1-3 key descriptive adjectives from the image *around* `[1]` (e.g., "a sleek, stainless steel [1] on a table"). Do NOT replace `[1]` with a full description.
- **Scene Description:** Fully describe the user's desired scene around the `[1]` placeholder (setting, actions, mood, lighting, artistic style).
- **User's Intent:** If the user's prompt has its own placeholder (e.g., '[the watch]'), replace it with `[1]`.
- **Clarity for Imagen:** Be precise for scene elements.
- **Output:** ONLY the final Imagen prompt. No conversational fluff.

Example: User uploads image of vintage watch. User prompt: "My watch on rustic desk with coffee."
Ideal Output for Imagen: "A vintage, leather-strapped [1] resting on a rustic wooden desk, next to a steaming ceramic coffee cup. Warm, soft morning light. Close-up shot."
"""
def construct_gemini_user_text(user_scene_idea): # Renamed from your 'prompt' function
    return f'User\'s desired base scene/customization idea: "{user_scene_idea}"\n\nGenerate optimized Imagen 3 prompt using `[1]` for the product, per system instructions.'


# --- Combined Button Logic for Gemini (Prompt Gen) & Imagen (Image Gen) ---
col1, col2 = st.columns(2)

with col1:
    if st.button("✨ Generate/Refine Imagen Prompt (with Gemini)", key="gemini_prompt_button",
                  disabled=not st.session_state.uploaded_subject_image_details or not st.session_state.user_base_imagen_prompt.strip()):
        with st.spinner("Gemini is crafting the Imagen prompt..."):
            if not st.session_state.uploaded_subject_image_details: # Should be caught by disabled but good check
                st.error("No images uploaded for Gemini."); st.stop()

            gemini_image_parts = []
            # Using first image for Gemini's visual reference for description (if system prompt asks for it)
            first_image_detail = st.session_state.uploaded_subject_image_details[0]
            try:
                gemini_image_parts.append(Part.from_bytes(
                    data=first_image_detail["bytes"], mime_type=first_image_detail["type"]
                ))
            except AttributeError: st.error("Part object missing 'from_bytes'. Check library."); st.exception(e); st.stop()
            except Exception as e: st.error(f"Error creating image Part for Gemini: {e}"); st.exception(e); st.stop()

            gemini_user_text_str = construct_gemini_user_text(st.session_state.user_base_imagen_prompt)
            try:
                text_part_for_gemini = Part(text=gemini_user_text_str) # Using direct instantiation for text part
            except Exception as e: st.error(f"Failed to create text Part: {e}"); st.exception(e); st.stop()

            all_contents_for_gemini = [text_part_for_gemini] + gemini_image_parts

            try:
                gemini_response = client.models.generate_content(
                    model=lang_model, # YOUR lang_model
                    contents=all_contents_for_gemini,
                    config=GenerateContentConfig(
                        system_instruction=system_instruction_for_gemini,
                        # media_resolution=MediaResolution.MEDIA_RESOLUTION_LOW, # From your original code
                    )
                )
                generated_text_from_gemini = getattr(gemini_response, 'text', None)
                if not generated_text_from_gemini and gemini_response.candidates and gemini_response.candidates[0].content.parts:
                    generated_text_from_gemini = "".join(p.text for p in gemini_response.candidates[0].content.parts if hasattr(p, 'text'))

                if generated_text_from_gemini and generated_text_from_gemini.strip():
                    st.session_state.final_imagen_prompt_for_imagen = generated_text_from_gemini.strip()
                    st.success("Gemini generated/refined the Imagen prompt!")
                    # No st.rerun() here, the text_area below will pick up the new session_state value
                else: st.error("Gemini returned an empty prompt.")
            except Exception as e: st.error(f"Error calling Gemini: {e}"); st.exception(e)

# Text area for the FINAL Imagen prompt (populated by Gemini or user edited)
st.session_state.final_imagen_prompt_for_imagen = st.text_area(
    "**Final Prompt for Imagen (edit if needed):**",
    value=st.session_state.final_imagen_prompt_for_imagen, # Displays Gemini's output or user's edits
    height=150,
    key="final_imagen_prompt_area_key",
    help="This prompt (containing [1]) will be sent to Imagen."
)


with col2:
    if st.button("🎨 Generate Image with Imagen", key="imagen_generate_button",
                  disabled=not st.session_state.uploaded_subject_image_details or not st.session_state.final_imagen_prompt_for_imagen.strip()):

        imagen_prompt_to_use = st.session_state.final_imagen_prompt_for_imagen

        if "[1]" not in imagen_prompt_to_use: # Crucial check
            st.warning("The Final Imagen Prompt must include `[1]` to refer to your product. Please edit or regenerate."); st.stop()

        with st.spinner(f"Imagen ('{edit_model}') is generating your image..."):
            imagen_reference_images_list = []
            # Using ALL uploaded images as SubjectReferenceImage for [1]
            # Imagen should ideally use these to better understand the subject for the [1] placeholder.
            # If Imagen only uses the first one with reference_id=1, this is okay too.
            # Your provided example used reference_id=1 for mujer[1].
            # If multiple uploaded images refer to the same subject [1]:
            # Option 1: Create one SubjectReferenceImage from the first uploaded image.
            # Option 2: Create multiple SubjectReferenceImages, all with reference_id=1. (Let's try this)
            # Option 3: Create multiple SubjectReferenceImages with unique IDs (0,1,2)
            #           but prompt refers only to [1]. Less clear how Imagen handles this.

            # Using first image as the primary SubjectReferenceImage for [1]
            # (as per updated understanding from your snippet)
            if not st.session_state.uploaded_subject_image_details:
                 st.error("No images uploaded for Imagen reference."); st.stop()

            first_image_for_imagen_ref = st.session_state.uploaded_subject_image_details[0]
            subject_gcp_image = Image(image_bytes=first_image_for_imagen_ref["bytes"])

            # For SubjectReferenceConfig, we need a description.
            # Let's use a simple one or derive it via another Gemini call if complex.
            # For now, a generic one, or you can have a text_input for it.
            # Or derive it from Gemini's general understanding if the Gemini system prompt was different.
            # For now, let's use a simple description based on filename if available.
            subject_desc_for_config = f"the uploaded product: {first_image_for_imagen_ref.get('name', 'product')}"
            # This could also be a fixed string like you had "a headshot of a woman"
            # Or derived from another Gemini output.

            subject_ref_img = SubjectReferenceImage(
                reference_id=1, # To match [1] in the prompt
                reference_image=subject_gcp_image,
                config=SubjectReferenceConfig( # As per your example
                    subject_description=subject_desc_for_config,
                    subject_type="SUBJECT_TYPE_PRODUCT" # Or "SUBJECT_TYPE_GENERIC" - check valid enums
                )
            )
            references_for_imagen = [subject_ref_img]

            # !!! CRITICAL: Verify edit_mode from docs !!!
            # Your example used "EDIT_MODE_DEFAULT". Using that.
            chosen_imagen_edit_mode = "EDIT_MODE_DEFAULT"

            try:
                imagen_response = client.models.edit_image(
                    model=edit_model, # YOUR edit_model
                    prompt=imagen_prompt_to_use,
                    reference_images=references_for_imagen,
                    config=EditImageConfig(
                        edit_mode=chosen_imagen_edit_mode,
                        number_of_images=4, #
                       # seed=1, # From your example
                        safety_filter_level=HarmBlockThreshold.BLOCK_ONLY_HIGH,
                        person_generation="ALLOW_ADULT", # From your example
                    )
                )
                st.success("Imagen processing complete!")
                if imagen_response.generated_images: # This list will now contain up to 4 images
                    st.subheader(f"Generated Images by Imagen ({len(imagen_response.generated_images)} variations):")
                    
                    # Determine number of columns, e.g., 2 or 4
                    num_generated = len(imagen_response.generated_images)
                    cols_per_row_output = min(num_generated, 2) # Display 2 images per row, or 4 if you prefer
                    
                    for i in range(0, num_generated, cols_per_row_output):
                        cols = st.columns(cols_per_row_output)
                        for j in range(cols_per_row_output):
                            img_idx_output = i + j
                            if img_idx_output < num_generated:
                                with cols[j]: # Use the current column
                                    img_info = imagen_response.generated_images[img_idx_output]
                                    output_bytes = getattr(img_info, 'image_bytes', None)
                                    if not output_bytes and hasattr(img_info, 'image') and hasattr(img_info.image, '_pil_image'):
                                        buf = io.BytesIO()
                                        img_info.image._pil_image.save(buf, format="PNG") # Or JPG
                                        output_bytes = buf.getvalue()
                                    
                                    if output_bytes:
                                        st.image(output_bytes, caption=f"Imagen Output {img_idx_output + 1}")
                                    else:
                                        st.warning(f"Could not display Imagen output {img_idx_output + 1}.")
                else:
                    st.warning("Imagen returned no images.")

            except Exception as e: st.error(f"Error during Imagen processing: {e}"); st.exception(e)


# Your previous code for the Gemini call (which you said didn't show the prompt)
# was mixed into the "Generate & Customize" button.
# I've separated it for clarity: one button for Gemini, one for Imagen.
# The text_area for final_imagen_prompt_for_imagen is the bridge.
