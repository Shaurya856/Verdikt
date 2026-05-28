from fact_checker.components.chunker import Chunk, chunk_document


class TestChunkDocument:
    def test_single_sentence(self):
        chunks = chunk_document("This is one sentence.")
        assert len(chunks) == 1
        assert chunks[0].text == "This is one sentence."
        assert chunks[0].index == 0

    def test_two_short_sentences_merged(self):
        chunks = chunk_document("First sentence. Second sentence.")
        assert len(chunks) == 1
        assert "First sentence" in chunks[0].text
        assert "Second sentence" in chunks[0].text

    def test_empty_text_returns_empty(self):
        assert chunk_document("") == []

    def test_whitespace_only_returns_empty(self):
        assert chunk_document("   \n\n  ") == []

    def test_indices_are_sequential(self):
        text = " ".join(f"Sentence {i}." for i in range(8))
        chunks = chunk_document(text)
        for i, chunk in enumerate(chunks):
            assert chunk.index == i

    def test_token_count_is_positive(self):
        chunks = chunk_document("This sentence has five words.")
        assert chunks[0].token_count > 0

    def test_two_long_sentences_not_merged(self):
        # Each sentence is 200 words — together they exceed the 300-word default limit.
        long1 = " ".join(["word"] * 200) + "."
        long2 = " ".join(["word"] * 200) + "."
        chunks = chunk_document(f"{long1} {long2}", max_tokens=300)
        assert len(chunks) == 2

    def test_custom_max_tokens(self):
        # With max_tokens=5, two 4-word sentences can still be merged (4+4=8 > 5? no, 4≤5).
        # "one two three four." = 4 words, "five six seven eight." = 4 words
        # combined = 8 words > 5 → NOT merged
        s1 = "one two three four."
        s2 = "five six seven eight."
        chunks = chunk_document(f"{s1} {s2}", max_tokens=5)
        assert len(chunks) == 2

    def test_chunk_dataclass_fields(self):
        chunks = chunk_document("Hello world.")
        assert isinstance(chunks[0], Chunk)
        assert hasattr(chunks[0], "index")
        assert hasattr(chunks[0], "text")
        assert hasattr(chunks[0], "token_count")
