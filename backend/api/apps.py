from django.apps import AppConfig
import docurag.pipeline as pipeline

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    engine = None

    def ready(self):
        # Lazy load engine singleton
        if not self.engine:
            try:
                # Use a wrapper class to maintain the .ask and .ingest_file interface
                class PipelineWrapper:
                    def __init__(self):
                        self.device = 'cpu'
                        self.model_flags = {}
                        self.total_chunks = 0

                    def ask(self, *args, **kwargs):
                        return pipeline.ask(*args, **kwargs)

                    def ingest_file(self, *args, **kwargs):
                        return pipeline.ingest_file(*args, **kwargs)

                self.engine = PipelineWrapper()
            except Exception as e:
                print(f"Error initializing Pipeline: {e}")
