from app.db.session import SessionLocal
from app.models.repository_chunk import RepositoryChunk, ChunkProvider, ChunkType

class ChunkDBTest():
    def __init__(self):
        pass
        
    def get_chunk_content(self) -> list[RepositoryChunk]:
        chunks = []
        
        # Create session
        db = SessionLocal()
        
        try: 
            rows = db.query(RepositoryChunk).all()
            
            with open("res.txt", "w+") as f:
                for row in rows:
                    f.write("content ---------------------------------\n\n")
                    f.write(f"chunk-repo-id: {row.id}\n")
                    f.write(f"chunk-repo-url: {row.repository.source_url}\n")
                    f.write(f"chunk-symbol_ids: {row.symbol_ids}\n")
                    f.write(f"chunk-type: {row.chunk_type}\n")
                    f.write(f"chunk-origin: {row.origin}\n")
                    f.write(f"chunk-provider: {row.provider}\n")
                    f.write(f"chunk-part_total: {row.part_total}\n")
                    f.write(f"chunk-is_partial: {row.is_partial}\n")
                    f.write(f"chunk-part_index: {row.part_index}\n")
                    f.write(f"chunk-token_count: {row.token_count}\n")
                    f.write(f"chunk-scope_chain: {row.scope_chain}\n")
                    f.write(f"chunk-content_hash: {row.content_hash}\n")
                    if row.enriched_content is None:
                        continue
                    f.write(row.enriched_content+"\n")
                    f.write("-----------------------------------------\n\n")
            
            return chunks
        finally:
            db.close()   
    
    
fetch_chunk = ChunkDBTest()
fetch_chunk.get_chunk_content()


