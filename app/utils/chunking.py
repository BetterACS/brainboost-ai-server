import random

def sliding_window_chunking(text, chunk_size, overlap_size):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(''.join(text[start:end]))
        start += chunk_size - overlap_size

    return chunks


def get_chunk_distribution(min_chunks: int, max_questions: int, min_questions: int, context: str, overlap_size: int = 200, chunks_size: int = 4200):
    chunks = []
    while len(chunks) < min_chunks:
        if chunks_size < 500:
            return {"status": 500, "data": "Context is too small."}

        chunks = sliding_window_chunking(context, chunk_size=chunks_size, overlap_size=overlap_size)
        chunks_size -= int(chunks_size // 2.5)
        overlap_size -= 30

    # Max 10 chunks
    if len(chunks) > 10:
        chunks = random.sample(chunks, 10)

    min_q = 1
    max_q = 3

    question_distribution = [random.randint(min_q, max_q) for _ in range(len(chunks))]

    # Adjust if total exceeds max_questions
    while sum(question_distribution) > max_questions:
        for i in range(len(question_distribution)):
            if question_distribution[i] > min_q and sum(question_distribution) > max_questions:
                question_distribution[i] -= 1

    # Adjust if total is less than min_questions
    while sum(question_distribution) < min_questions:
        for i in range(len(question_distribution)):
            if question_distribution[i] < max_q and sum(question_distribution) < min_questions:
                question_distribution[i] += 1

    return chunks, question_distribution
