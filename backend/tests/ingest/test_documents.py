from app.database.documents import embedding_dimensions, parse_embedding_vector


def test_parse_embedding_vector_from_list() -> None:
    vector = parse_embedding_vector([0.1, 0.2, 0.3])
    assert vector == [0.1, 0.2, 0.3]
    assert embedding_dimensions(vector) == 3


def test_parse_embedding_vector_from_pgvector_string() -> None:
    raw = "[" + ",".join("0.1" for _ in range(1536)) + "]"
    vector = parse_embedding_vector(raw)
    assert vector is not None
    assert len(vector) == 1536
    assert embedding_dimensions(raw) == 1536
