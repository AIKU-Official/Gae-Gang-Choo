from sentence_transformers import SentenceTransformer
from chromadb import Documents, EmbeddingFunction, Embeddings


class EmbedGenerator(EmbeddingFunction):
    MODEL_NAME = "jhgan/ko-sroberta-multitask"
    model = SentenceTransformer(MODEL_NAME)

    def __call__(self, input: Documents) -> Embeddings:
        return self.model.encode(input).tolist()
