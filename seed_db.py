from src.app.database import Base, SessionLocal, engine
from src.app.models import PrintJob

Base.metadata.create_all(bind=engine)
db = SessionLocal()

job = PrintJob(
    title="Example 3D Vase",
    source="Thingiverse",
    source_url="http://example.com",
    status="TO BE PRINTED",
    author="Jules",
)

db.add(job)
db.commit()
db.close()
