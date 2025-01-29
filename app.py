import streamlit as st
from logic import analyze_compliance, generate_pdf_from_docx, generate_word_doc, extract_text_from_image

def main():
    st.title("Compliance Checklist Tool (Word or PDF)")

    # Additional fields
    title_input = st.text_input("Enter Title (optional)")
    references_input = st.text_area("Enter References (optional)", height=100)

    # Choose input type
    upload_type = st.selectbox("Select Input Type:", ["Upload Text", "Upload Image"])

    if upload_type == "Upload Text":
        handle_text_input(title_input,  references_input)
    else:
        handle_image_input(title_input,  references_input)

    # After the user runs the check, if we have results in session_state, show the download options
    if st.session_state.analysis_done and st.session_state.docx_stream:
        st.subheader("Download Report")
        format_choice = st.selectbox("Select download format", ["Word", "PDF"], key="format_choice")

        if format_choice == "PDF":
            # If we haven't generated a PDF yet, do it now
            if st.session_state.pdf_stream is None:
                st.session_state.pdf_stream = generate_pdf_from_docx(st.session_state.docx_stream)

            st.download_button(
                label="Download Compliance Report (PDF)",
                data=st.session_state.pdf_stream,
                file_name="compliance_report.pdf",
                mime="application/pdf"
            )
        else:
            st.download_button(
                label="Download Compliance Report (Word)",
                data=st.session_state.docx_stream,
                file_name="compliance_report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

def handle_text_input(title_input, references_input):
    post_text = st.text_area("Enter the content to check compliance:", height=300)
    if st.button("Check Compliance"):
        if post_text.strip():
            _process_compliance(
                post_text=post_text,
                title_input=title_input,
                references_input=references_input,
                is_image=False,
                image_file=None,
                extracted_text=""
            )
        else:
            st.warning("Please enter text to analyze.")

def handle_image_input(title_input,  references_input):
    uploaded_image = st.file_uploader("Upload an image (PNG/JPG/JPEG)", type=["png","jpg","jpeg"])
    if uploaded_image:
        st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
        if st.button("Check Compliance for Image"):
            extracted_text = extract_text_from_image(uploaded_image)
            _process_compliance(
                post_text="",  # We'll rely on the image and extracted text
                title_input=title_input,
                references_input=references_input,
                is_image=True,
                image_file=uploaded_image,
                extracted_text=extracted_text
            )

def _process_compliance(post_text, title_input,  references_input, is_image=False, image_file=None, extracted_text=""):
    """
    Actually run compliance analysis and build doc.  
    Store results in st.session_state so we don't re-run on each widget change.
    """
    with st.spinner("Analyzing compliance..."):
        # If is_image=True, we pass extracted_text for the compliance check
        text_for_analysis = extracted_text if is_image else post_text

        strengths, weaknesses, checklist = analyze_compliance(text_for_analysis)

        # Store them
        st.session_state.strengths = strengths
        st.session_state.weaknesses = weaknesses
        st.session_state.checklist = checklist

        # Display results
        display_results(strengths, weaknesses, checklist)

        # Generate the DOCX (and store in session state)
        docx_stream = generate_word_doc(
            post_text=post_text,
            strengths=strengths,
            weaknesses=weaknesses,
            checklist=checklist,
            title_input=title_input,
            references_input=references_input,
            is_image=is_image,
            image_file=image_file,
            extracted_text=extracted_text
        )

        st.session_state.docx_stream = docx_stream
        st.session_state.pdf_stream = None  # reset any previously generated PDF
        st.session_state.analysis_done = True

def display_results(strengths, weaknesses, checklist):
    st.subheader("Analysis Results")
    col1, col2 = st.columns(2)

    with col1:
        st.write("### ✅ Strengths")
        if strengths:
            for s in strengths:
                st.success(f"{s['Requirement']}: {s['Comments']}")
        else:
            st.info("No strengths identified")

    with col2:
        st.write("### ❌ Weaknesses")
        if weaknesses:
            for w in weaknesses:
                st.error(f"{w['Requirement']}: {w['Comments']}")
        else:
            st.info("No weaknesses identified")

    st.write("### 📋 Compliance Checklist")
    if checklist:
        st.table(checklist)
    else:
        st.info("No checklist items found.")

# -------------------------
#   Run
# -------------------------
if __name__ == "__main__":
    main()
