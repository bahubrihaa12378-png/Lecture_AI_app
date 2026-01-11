import whisper
import ollama

model = whisper.load_model("base")



def transcribe_audio(audio_path):
    result = model.transcribe(audio_path)
    return result["text"]


def clean_transcript(raw_transcript):
    system_instruction = (
        "You are an academic transcription editor. "
        "Clean the following lecture transcript:\n"
        "- Fix grammar and punctuation\n"
        "- Remove filler words and repetitions\n"
        "- Correct obvious transcription errors using context\n"
        "- Preserve technical terms exactly\n"
        "- Do NOT summarize\n"
        "- Do NOT add or remove content"
    )

    try:
        response = ollama.chat(model='llama3.2', messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': f"Transcript:\n{raw_transcript}"}
        ])
        return response['message']['content']

    except Exception as e:
        return f"Error connecting to Local LLM or model: {e}"

# Update your chatbot function slightly to handle the combined context
def ask_lecture_question(context, question):
    system_instruction = (
        "You are a helpful study assistant. Use the provided context (Lecture Transcript and/or PDF slides) "
        "to answer the question. If the answer is not in the context, say you don't know."
    )
    try:
        response = ollama.chat(model='llama3.2', messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': f"CONTEXT:\n{context}\n\nUSER QUESTION: {question}"}
        ])
        return response['message']['content']
    except Exception as e:
        return f"Error: {e}"


def generate_structured_notes(cleaned_transcript):
    system_instruction = (
        "You are a university teaching assistant. "
        "Convert the following cleaned lecture transcript into structured study notes:\n"
        "- Use clear headings and subheadings\n"
        "- Present key ideas as bullet points\n"
        "- Clearly mark definitions\n"
        "- Preserve examples mentioned by the instructor\n"
        "- Maintain the original meaning\n"
        "- Do NOT summarize\n"
        "- Do NOT add or remove  information"
    )

    try:
        response = ollama.chat(model='llama3.2', messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': f"Transcript:\n{cleaned_transcript}"}
        ])
        return response['message']['content']

    except Exception as e:
        return f"Error generating structured notes: {e}"


def generate_exam_summary(structured_notes):
    system_instruction = (
        "You are an exam preparation assistant. "
        "From the lecture notes below:\n"
        "- Select ONLY the most exam-relevant points and omit less critical details\n"
        "- Extract key definitions, formulas, or rules\n"
        "- Highlight concepts emphasized by the instructor\n"
        "- Assume the student has very limited revision time\n"
        "- Do NOT add new information"
    )

    try:
        response = ollama.chat(model='llama3.2', messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': f"Lecture Notes:\n{structured_notes}"}
        ])
        return response['message']['content']

    except Exception as e:
        return f"Error generating exam summary: {e}"


def generate_mcqs(structured_notes):
    system_instruction = (
        "You are an examiner. "
        "Based ONLY on the lecture notes below:\n"
        "- Generate 5 multiple-choice questions\n"
        "- Each question must have exactly one correct answer\n"
        "- Provide three plausible distractors\n"
        "- Focus on conceptual understanding\n"
        "- Do NOT add new information"
    )

    try:
        response = ollama.chat(model='llama3.2', messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': f"Lecture Notes:\n{structured_notes}"}
        ])
        return response['message']['content']

    except Exception as e:
        return f"Error generating MCQs: {e}"


def generate_flashcards(structured_notes):
    system_instruction = (
        "Generate flashcards from the lecture notes:\n"
        "- Front: question or term\n"
        "- Back: concise answer\n"
        "- Keep answers short and precise\n"
        "- Do NOT add new information"
    )

    try:
        response = ollama.chat(model='llama3.2', messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': f"Lecture Notes:\n{structured_notes}"}
        ])
        return response['message']['content']

    except Exception as e:
        return f"Error generating flashcards: {e}"





# ===== PIPELINE EXECUTION =====

def run_pipeline(audio_path):
    raw_transcript = transcribe_audio(audio_path)
    cleaned_output = clean_transcript(raw_transcript)
    structured_notes = generate_structured_notes(cleaned_output)
    exam_summary = generate_exam_summary(structured_notes)
    mcqs = generate_mcqs(structured_notes)
    flashcards = generate_flashcards(structured_notes)

    return {
        "raw_transcript": raw_transcript,
        "cleaned_output": cleaned_output,
        "structured_notes": structured_notes,
        "exam_summary": exam_summary,
        "mcqs": mcqs,
        "flashcards": flashcards
    }