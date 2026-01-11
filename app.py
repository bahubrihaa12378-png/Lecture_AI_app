import streamlit as st
import html  # Library for escaping text
import textwrap


from pipeline import (
    transcribe_audio,
    clean_transcript,
    generate_structured_notes,
    generate_exam_summary,
    generate_mcqs,
    generate_flashcards,
    ask_lecture_question,
)

# --- INITIALIZE ALL SESSION STATE KEYS ---
# This ensures the variables exist even before the user interacts with the app
if "ready" not in st.session_state:
    st.session_state.ready = False



# --- Helper Functions ---
def safe_text(s):
    # Remove markdown bold stars and escape HTML characters
    clean = s.replace("**", "").strip()
    return html.escape(clean)

def parse_flashcards(text):
    cards = []
    # Split by "Front:" and remove the first empty element if it exists
    blocks = [b for b in text.split("Front:") if b.strip()]
    for block in blocks:
        if "Back:" in block:
            parts = block.split("Back:")
            front = parts[0].strip()
            back = parts[1].strip()
            if front and back:
                cards.append((front, back))
    return cards

st.set_page_config(page_title="Lecture AI", layout="wide")
st.title("🎓 Lecture Voice → Smart Study Material")

# --- CSS for Flashcards ---
st.markdown("""
<style>
.flashcard {
  width: 300px;
  height: 200px;
  perspective: 1000px;
  display: inline-block;
  margin: 15px;
}
.flashcard-inner {
  width: 100%;
  height: 100%;
  position: relative;
  transition: transform 0.6s;
  transform-style: preserve-3d;
  cursor: pointer;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  border-radius: 10px;
}
.flashcard:hover .flashcard-inner {
  transform: rotateY(180deg);
}
.flashcard-front, .flashcard-back {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 10px;
  padding: 20px;
  backface-visibility: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
  font-size: 18px;
  font-weight: 500;
  overflow-y: auto;
}
.flashcard-front {
  background: linear-gradient(135deg, #f0f2f6 0%, #ffffff 100%);
  color: #333;
  border: 1px solid #ddd;
}
.flashcard-back {
  background: linear-gradient(135deg, #dfe8ff 0%, #f0f2ff 100%);
  color: #0044cc;
  transform: rotateY(180deg);
  border: 1px solid #bcd;
}
</style>
""", unsafe_allow_html=True)

# --- Session State Setup ---
if "current_view" not in st.session_state:
    st.session_state.current_view = None
if "messages" not in st.session_state:
    st.session_state.messages = [] # Stores chat history

# --- Upload ---
uploaded_file = st.file_uploader("Upload lecture audio not more than 10 minutes", type=["mp3", "wav", "m4a"])
# --- New Logic: Detect File Change ---
if uploaded_file:
    # If the file name is different from what we last processed, reset the state
    if "current_filename" not in st.session_state or st.session_state.current_filename != uploaded_file.name:
        st.session_state.ready = False
        st.session_state.current_filename = uploaded_file.name
        # Clear previous session data to avoid showing old notes with a new file
        keys_to_clear = ["notes", "summary", "mcqs", "flashcards", "messages", "cleaned"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        # Reset chat specifically
        st.session_state.messages = []




if uploaded_file and not st.session_state.ready:
    with st.spinner("Processing Audio..."):
        audio_path = "temp_audio.wav"
        with open(audio_path, "wb") as f:
            f.write(uploaded_file.read())

        st.session_state.raw = transcribe_audio(audio_path)
        st.session_state.cleaned = clean_transcript(st.session_state.raw)
        st.session_state.notes = generate_structured_notes(st.session_state.cleaned)

        # Ensure chat is fresh for the new file
        st.session_state.messages = []
        st.session_state.ready = True

        st.rerun()





# --- Action Tiles (Always Visible) ---
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("📒 Notes", disabled=not st.session_state.ready, use_container_width=True):
        st.session_state.current_view = "notes"

with col2:
    if st.button("📝 Summary", disabled=not st.session_state.ready, use_container_width=True):
        st.session_state.current_view = "summary"

with col3:
    if st.button("❓ MCQs", disabled=not st.session_state.ready, use_container_width=True):
        st.session_state.current_view = "mcqs"

with col4:
    if st.button("🗂 Flashcards", disabled=not st.session_state.ready, use_container_width=True):
        st.session_state.current_view = "flashcards"
with col5:
    if st.button("💬 Chat", disabled=not st.session_state.ready, use_container_width=True):
        st.session_state.current_view = "chat"

st.divider()

# --- Output Logic ---
if st.session_state.ready and st.session_state.current_view == "notes":
    st.subheader("📒 Structured Notes")
    st.write(st.session_state.notes)

elif st.session_state.ready and st.session_state.current_view == "summary":
    if "summary" not in st.session_state:
        with st.spinner("Generating summary..."):
            st.session_state.summary = generate_exam_summary(st.session_state.notes)
    st.subheader("📝 Exam Summary")
    st.write(st.session_state.summary)

elif st.session_state.ready and st.session_state.current_view == "mcqs":
    if "mcqs" not in st.session_state:
        with st.spinner("Generating MCQs..."):
            st.session_state.mcqs = generate_mcqs(st.session_state.notes)
    st.subheader("❓ MCQs")
    st.write(st.session_state.mcqs)

elif st.session_state.ready and st.session_state.current_view == "flashcards":
    if "flashcards" not in st.session_state:
        with st.spinner("Generating flashcards..."):
            st.session_state.flashcards = generate_flashcards(st.session_state.notes)

    st.subheader("🗂 Flashcards")

    cards = parse_flashcards(st.session_state.flashcards)

    if not cards:
        st.warning("Could not parse flashcards. Check the raw format below:")
        st.code(st.session_state.flashcards)
    else:
        # Wrap everything in a container div to keep them grouped
        flashcard_container_html = '<div style="display: flex; flex-wrap: wrap; justify-content: center;">'

        for front, back in cards:
            # Using textwrap.dedent ensures no leading spaces trigger a code block
            card_html = textwrap.dedent(f"""
                <div class="flashcard">
                    <div class="flashcard-inner">
                        <div class="flashcard-front">{safe_text(front)}</div>
                        <div class="flashcard-back">{safe_text(back)}</div>
                    </div>
                </div>
            """).strip()
            flashcard_container_html += card_html

        flashcard_container_html += '</div>'

        # Render the final combined string
        st.markdown(flashcard_container_html, unsafe_allow_html=True)

# --- NEW: CHAT INTERFACE LOGIC ---
elif st.session_state.ready and st.session_state.current_view == "chat":
    st.subheader("💬 Chat with Llama 3.2 about Lecture")

    # 1. Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 2. Handle new user input
    if prompt := st.chat_input("Ask a question about the lecture..."):
        # Display user message
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate response using Llama 3.2 via pipeline
        with st.spinner("Llama is thinking..."):
            answer = ask_lecture_question(st.session_state.cleaned, prompt)

        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
