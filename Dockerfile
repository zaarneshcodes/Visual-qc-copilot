# One container runs both services: FastAPI (internal, port 8000) + Streamlit (public, port 7860).
# Training happens in Colab; this image only serves the exported ONNX models, so it has no torch.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces runs containers as user 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH PYTHONUNBUFFERED=1
WORKDIR $HOME/app

COPY --chown=user requirements.txt requirements-rag.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt -r requirements-rag.txt

# Bake Chroma's embedding model into the image so the first request is not slow
RUN python -c "from chromadb.utils.embedding_functions import DefaultEmbeddingFunction as D; D()(['warm up'])"

COPY --chown=user . .
RUN chmod +x start.sh

EXPOSE 7860
CMD ["./start.sh"]
