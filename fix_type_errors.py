with open("src/app/main.py", "r") as f:
    text = f.read()

# Fix the dictionary mapping where Pyright complains about str being passed as Column[str] key
# The issue is `db.query(PrintJob.file_path)` returns tuples. The generator `job.file_path` accesses the item, but `db.query(PrintJob.file_path)` might not be fully typed.
# Wait, the error is in main.py:393 `config_map.get(s_name, ServiceConfig(enabled=0))`
# Ah, config_map is a dictionary with `c.service_name` as keys. `c.service_name` is a Column[str] typed variable in SQLAlchemy if not accessed properly, or it evaluates to str.
# Let's fix `config_map = {str(c.service_name): c for c in configs}`
text = text.replace(
    'config_map = {c.service_name: c for c in configs}',
    'config_map = {str(c.service_name): c for c in configs}'
)

# And fix `enabled=0` not assignable
text = text.replace('ServiceConfig(enabled=0)', 'ServiceConfig()')
# The type checker also complained about `config.enabled = enabled`
# In models/__init__.py, enabled is `Column(Integer, default=0)`. Pyright needs it typed properly.
# We added `# type: ignore` earlier but maybe it didn't stick or wasn't enough.

with open("src/app/main.py", "w") as f:
    f.write(text)

with open("src/app/models/__init__.py", "r") as f:
    text_models = f.read()

text_models = text_models.replace(
    'enabled = Column(Integer, default=0)',
    'enabled: int = Column(Integer, default=0) # type: ignore'
)
text_models = text_models.replace(
    'target_url = Column(String, nullable=True)',
    'target_url: str | None = Column(String, nullable=True) # type: ignore'
)
text_models = text_models.replace(
    'credential = Column(String, nullable=True)',
    'credential: str | None = Column(String, nullable=True) # type: ignore'
)

with open("src/app/models/__init__.py", "w") as f:
    f.write(text_models)
