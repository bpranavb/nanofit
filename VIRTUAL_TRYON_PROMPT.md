# Virtual Try-On Prompt

This is the current prompt being sent to **Gemini 2.5 Flash Image** model for virtual try-on generation.

---

## Current Active Prompt

```
**Primary Directive: High-Fidelity Virtual Try-On**

You are an expert digital tailor. Your task is to execute a precise clothing swap.

**!!! CORE SAFETY DIRECTIVE: PROTECT IDENTITY !!!**
**This is the most important rule. The person's face and head in Image 1 are a STRICT NO-EDIT ZONE. They must be transferred to the final image perfectly, pixel for pixel, without ANY modification. Any change to the facial features, expression, skin tone, or hair is a complete failure of the task.**

**Input Definitions:**
- **Image 1 (The Canvas):** Contains the person, their pose, and the background. This is the base image that will be edited.
- **Image 2 (The Source):** Contains the garment(s). This is the ONLY source for the new clothing's appearance.

**--- CRITICAL RULES ---**

1.  **PRESERVE THE CANVAS:** As stated in the Core Safety Directive, the person's identity is paramount. In addition, the original **pose** and the entire **background** MUST be preserved with photorealistic accuracy. Do not change them.

2.  **EXTRACT FROM THE SOURCE:** You must analyze Image 2 to extract the garment's key attributes:
    - **Exact Color:** The precise hue, saturation, and brightness.
    - **Complete Pattern & Design:** The full visual design, embroidery, or print.
    - **Fabric Texture:** The material's look and feel (e.g., cotton, silk, denim).

3.  **DISCARD ORIGINAL CLOTHING:** You MUST completely ignore and discard all visual information from the clothes the person is wearing in Image 1. Their original clothing's color, pattern, and texture are IRRELEVANT and must NOT influence the output.

**--- STEP-BY-STEP EXECUTION ---**

1.  **Isolate:** Identify and isolate the primary garment(s) in Image 2. Ignore any mannequin, hanger, or person.
2.  **Map:** Identify the area of clothing on the person in Image 1, carefully excluding the head, neck, and hands.
3.  **Replace and Render:** Generate a new image where you flawlessly render the extracted garment attributes (Exact Color, Design, Texture) from Image 2 onto the mapped clothing area of Image 1. The new clothing must fit the person's body and pose naturally, including realistic folds and shadows.

**!! FINAL MANDATE !!**
The output image's clothing must be a perfect visual match to the garment in Image 2. The person's face and identity must be 100% identical to Image 1. There should be zero color blending from the original clothing. The resulting image must be photorealistic and seamlessly edited.
```

---

## Previous/Original Prompt (For Reference)

This was the original simpler prompt (commented out in code):

```
Your task is to perform a virtual try-on. The first image contains a person. The second image contains one or more clothing items. Identify the garments (e.g., shirt, pants, jacket) in the second image, ignoring any person or mannequin wearing them. Then, generate a new, photorealistic image where the person from the first image is wearing those garments. The person's original pose, face, and the background should be maintained.
```

---

## Prompt Structure Breakdown

### 1. **Primary Directive**
Sets the overall goal: High-fidelity virtual try-on

### 2. **Core Safety Directive**
- Strongest emphasis on preserving the person's face and identity
- Uses emphatic language ("STRICT NO-EDIT ZONE", "pixel for pixel")
- Frames face modification as complete failure

### 3. **Input Definitions**
- Clear naming: "Canvas" (person image) and "Source" (clothing image)
- Establishes which image is edited and which provides clothing

### 4. **Critical Rules**
- **Rule 1:** Preserve identity, pose, and background
- **Rule 2:** Extract exact attributes from clothing image
- **Rule 3:** Discard original clothing from person image

### 5. **Step-by-Step Execution**
- Clear 3-step process: Isolate → Map → Replace & Render
- Specific instructions for each step

### 6. **Final Mandate**
- Reinforces key requirements one more time
- Emphasizes photorealistic result

---

## Key Prompt Engineering Techniques Used

### 1. **Repetition**
- Face preservation mentioned multiple times
- Reinforces most critical requirement

### 2. **Emphatic Formatting**
- ALL CAPS for critical terms
- Bold text for emphasis
- Exclamation marks for urgency

### 3. **Failure Framing**
- "complete failure of the task" if face changes
- Strong language to discourage unwanted behavior

### 4. **Specific Instructions**
- Not just "preserve face" but "pixel for pixel"
- Not just "use clothing" but "exact color, pattern, texture"

### 5. **Clarity Through Structure**
- Named sections with clear headers
- Step-by-step breakdown
- Input definitions upfront

---

## Model Configuration

```python
# Model being used
model = "gemini-2.5-flash-image"

# Configuration
config = types.GenerateContentConfig(
    response_modalities=["IMAGE"]
)

# Content structure
content = types.Content(
    parts=[
        person_part,        # Image 1: Person photo
        clothing_part,      # Image 2: Clothing photo
        optimized_text_part # The prompt above
    ]
)
```

---

## Location in Code

**File:** `backend/server.py`  
**Lines:** 183-212  
**Function:** `create_tryon()`

---

## Modifying the Prompt

To modify the prompt, edit lines 183-212 in `backend/server.py`:

```python
text_prompt = """
[Your new prompt here]
"""
```

Then restart the backend:
```bash
sudo supervisorctl restart backend
```

---

## Prompt Effectiveness Notes

This prompt was developed through iterative refinement to:
- Maximize face/identity preservation
- Ensure accurate clothing color transfer
- Prevent color blending from original clothes
- Maintain natural pose and background
- Handle various clothing types (shirts, dresses, jackets, etc.)

The emphatic language and repetition are intentional to strongly guide the AI model's behavior.

---

**Last Updated:** 2025-10-26
