"""RAG per personaggio: indicizza i testi in Qdrant e li cerca filtrando sul personaggio.

Usa gli stessi mattoni visti a lezione (Lab 09): OpenAIEmbedder, QdrantVectorstore,
IngestionPipeline (DoclingParser + RecursiveSplitter + ChunkEmbedder).
Ogni chunk porta nei metadati 'source_file' e 'personaggio'.
"""
import os

from datapizza.clients.openai import OpenAIClient
from datapizza.core.vectorstore import VectorConfig
from datapizza.embedders import ChunkEmbedder
from datapizza.embedders.openai import OpenAIEmbedder
from datapizza.modules.parsers.docling import DoclingParser
from datapizza.modules.splitters import RecursiveSplitter
from datapizza.pipeline import IngestionPipeline
from datapizza.vectorstores.qdrant import QdrantVectorstore

from .dati import DATA_DIR

EMB_NAME = "content_embedding"
COLLECTION = "chat_storica"
POOL = 300  # quanti chunk chiedere a Qdrant prima di filtrare per personaggio (alto: con articoli lunghi i chunk crescono)


class RagStorico:
    def __init__(self, reindex: bool = False):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY mancante: copia .env.example in .env e inserisci la chiave.")

        self.embedder = OpenAIEmbedder(api_key=api_key, model_name="text-embedding-3-small")
        self.llm = OpenAIClient(api_key=api_key, model="gpt-4o-mini")

        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6336"))
        self.vs = QdrantVectorstore(host=host, port=port)
        try:
            client = self.vs.get_client()
            esiste = client.collection_exists(COLLECTION)
        except Exception as e:  # Qdrant spento / porta sbagliata
            raise RuntimeError(
                f"Qdrant non raggiungibile su {host}:{port}. Avvia il container Docker (vedi README)."
            ) from e

        if reindex and esiste:
            self.vs.delete_collection(COLLECTION)
            esiste = False

        # riusa l'indice se la collection esiste ED è popolata (evita ri-parsing e ri-embedding)
        chunks = list(self.vs.dump_collection(COLLECTION)) if esiste else []
        if not chunks:
            if esiste:
                self.vs.delete_collection(COLLECTION)
            self._indicizza()

    def _indicizza(self):
        self.vs.create_collection(
            collection_name=COLLECTION,
            vector_config=[VectorConfig(dimensions=1536, name=EMB_NAME)],
        )
        pipeline = IngestionPipeline(
            modules=[
                DoclingParser(),
                RecursiveSplitter(max_char=1024, overlap=128),
                ChunkEmbedder(client=self.embedder, embedding_name=EMB_NAME),
            ],
            vector_store=self.vs,
            collection_name=COLLECTION,
        )
        corpus = DATA_DIR / "corpus"
        for cartella in sorted(p for p in corpus.iterdir() if p.is_dir()):
            file_testo = sorted(list(cartella.glob("*.md")) + list(cartella.glob("*.pdf")))
            for f in file_testo:
                print(f"  indicizzo {cartella.name}/{f.name}")
                pipeline.run(
                    file_path=str(f),
                    metadata={"source_file": f.name, "personaggio": cartella.name},
                )

    def cerca(self, personaggio_id: str, domanda: str, k: int = 3):
        """Chunk più vicini alla domanda, SOLO dai testi di quel personaggio."""
        qv = self.embedder.embed(domanda)
        pool = self.vs.search(collection_name=COLLECTION, query_vector=qv, k=POOL, vector_name=EMB_NAME)
        return [h for h in pool if h.metadata.get("personaggio") == personaggio_id][:k]
