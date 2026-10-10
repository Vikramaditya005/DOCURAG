import os
import threading
from django.http import JsonResponse, FileResponse
from django.views import View
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.conf import settings

from .models import Document, QueryLog
from .serializers import DocumentSerializer, QueryLogSerializer
from django.apps import apps

def get_pipeline():
    return apps.get_app_config('api').engine

@api_view(['POST'])
def document_upload(request):
    file_obj = request.FILES.get('file')
    if not file_obj:
        return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
    
    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext not in ['.pdf', '.png', '.jpg', '.jpeg', '.webp']:
        return Response({'error': 'Invalid file extension'}, status=status.HTTP_400_BAD_REQUEST)
    
    if file_obj.size > 50 * 1024 * 1024:
        return Response({'error': 'File size exceeds 50MB'}, status=status.HTTP_400_BAD_REQUEST)

    doc = Document.objects.create(
        filename=file_obj.name,
        file=file_obj,
        file_type=ext[1:] if ext else 'unknown',
        status='queued'
    )

    def background_ingest(doc_id):
        try:
            pipeline = get_pipeline()
            doc_instance = Document.objects.get(id=doc_id)
            file_path = doc_instance.file.path

            doc_instance.status = 'processing'
            doc_instance.save()

            # Purge existing indices and cache for this document to ensure freshness
            # The pipeline/store should provide a way to remove by doc_id
            # We use the document's filename or a derived ID for the store
            # For now, we assume the store handles this via remove_document
            # we need to make sure the pipeline passes this through.

            # If the pipeline has a reference to the store:
            if hasattr(pipeline, 'store'):
                pipeline.store.remove_document(str(doc_id))

            result = pipeline.ingest_file(file_path, document_id=str(doc_id))
            doc_instance.pages = result.get('pages')
            doc_instance.chunk_counts = {'total': result.get('chunks_indexed', 0)}
            if result.get('chunks_indexed', 0) == 0:
                doc_instance.status = 'failed'
                doc_instance.error = 'No text could be extracted (needs OCR or image captioning)'
            else:
                doc_instance.status = 'ready'
        except Exception as e:
            try:
                doc_instance = Document.objects.get(id=doc_id)
                doc_instance.status = 'failed'
                doc_instance.error = str(e)
            except:
                pass
        finally:
            try:
                doc_instance.save()
            except:
                pass

    threading.Thread(target=background_ingest, args=(doc.id,), daemon=True).start()
    
    return Response(DocumentSerializer(doc).data, status=status.HTTP_202_ACCEPTED)

@api_view(['GET'])
def document_list(request):
    docs = Document.objects.all().order_by('-uploaded_at')
    serializer = DocumentSerializer(docs, many=True)
    return Response(serializer.data)

@api_view(['GET', 'DELETE'])
def document_detail(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if request.method == 'DELETE':
        try:
            pipeline = get_pipeline()
            if hasattr(pipeline, 'store') and getattr(pipeline, 'store'):
                pipeline.store.remove_document(str(doc.id))
        except Exception as e:
            pass
        if doc.file:
            default_storage.delete(doc.file.name)
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    serializer = DocumentSerializer(doc)
    return Response(serializer.data)

@api_view(['GET'])
def document_page(request, pk, page_num):
    doc = get_object_or_404(Document, pk=pk)
    import re
    slug = re.sub(r'[^a-zA-Z0-9_]', '_', doc.filename)
    pages_dir = os.path.join(settings.MEDIA_ROOT, 'pages')
    if not os.path.exists(pages_dir):
        return Response({'error': 'Pages directory not found'}, status=status.HTTP_404_NOT_FOUND)
        
    for f in os.listdir(pages_dir):
        if f.endswith(f'_p{page_num}.png') and slug in f:
            return FileResponse(os.path.join(pages_dir, f))
            
    return Response({'error': 'Page image not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def query_ask(request):
    data = request.data
    question = data.get('question', '').strip()
    doc_ids = data.get('document_ids', [])
    content_types = data.get('content_types', [])
    history = data.get('history', [])
    mode = data.get('mode', 'rag')

    if not question:
        return Response({'error': 'Question is required'}, status=status.HTTP_400_BAD_REQUEST)

    clean_q = question.strip().lower().rstrip("!?. ")
    capability_phrases = ["what can you do", "who are you", "what are your features", "how does this work", "how do you work", "help me", "what is docurag", "can you help"]
    greeting_words = {"hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"}

    is_greeting = (
        clean_q in greeting_words
        or any(phrase in clean_q for phrase in capability_phrases)
        or (any(clean_q.startswith(w) for w in greeting_words) and len(clean_q.split()) <= 6)
    )
    
    # Handle conversational greetings / capability queries
    if is_greeting:
        docs = Document.objects.filter(status='ready')
        doc_count = docs.count()
        doc_names = ", ".join([f"`{d.filename}`" for d in docs[:3]]) if doc_count > 0 else "None yet"
        if doc_count > 3:
            doc_names += f" and {doc_count - 3} more"

        greeting_answer = (
            f"👋 **Hello! I am DocuRAG Studio**, your intelligent document analysis assistant.\n\n"
            f"I have direct access to your loaded document library (**{doc_count} ready document(s)**: {doc_names}).\n\n"
            f"### What I can help you with:\n"
            f"* 📝 **Executive Summaries:** Extract high-level briefings and key takeaways.\n"
            f"* ❓ **Study & Exam Questions:** Generate test questions or aptitude practice directly from materials.\n"
            f"* 📊 **Table & Metric Extraction:** Convert tabular figures and data into structured tables.\n"
            f"* 🔍 **Fact-Checking & Deep Retrieval:** Answer questions with verifiable source citations `[E#]` and page thumbnails.\n"
            f"* 📖 **Glossary & Concept Definitions:** Clarify technical terminology from your documents.\n\n"
            f"Feel free to ask any question or click one of the quick helping prompts below!"
        )

        return Response({
            'id': 0,
            'answer': greeting_answer,
            'answerable': True,
            'confidence': 1.0,
            'total_ms': 45,
            'timing': {'total_ms': 45, 'stages': {'retrieval': 0, 'generation': 45}},
            'sources': [],
            'agent_trace': []
        })

    instructions = None
    if history:
        # Build conversation history
        history_blocks = []
        for turn in history[-4:]:  # last 4 turns for context
            if turn.get('user') and turn.get('assistant'):
                history_blocks.append(f"User: {turn.get('user', '')}\nAssistant: {turn.get('assistant', '')}")
        if history_blocks:
            instructions = "Consider the conversation history below for context:\n" + "\n".join(history_blocks)

    pipeline = get_pipeline()
    result = pipeline.ask(question, document_ids=doc_ids, content_types=content_types, instructions=instructions)

    # Format sources with thumbnail image lookup if available
    formatted_sources = []
    pages_dir = os.path.join(settings.MEDIA_ROOT, 'pages')
    for s in result.sources:
        s_data = s.model_dump() if hasattr(s, 'model_dump') else dict(s)
        doc_name = s_data.get('document', '')
        page_num = s_data.get('page', 1)
        import re
        slug = re.sub(r'[^a-zA-Z0-9_]', '_', doc_name)
        thumb = None
        if os.path.exists(pages_dir):
            for f in os.listdir(pages_dir):
                if f.endswith(f'_p{page_num}.png') and slug in f:
                    thumb = f
                    break
        s_data['thumbnail_url'] = thumb
        formatted_sources.append(s_data)

    confidence_score = result.confidence.score if hasattr(result.confidence, 'score') else 0.0
    total_ms = result.timing.total_ms if hasattr(result.timing, 'total_ms') else 0
    timing_dict = result.timing.model_dump() if hasattr(result.timing, 'model_dump') else {}
    agent_trace_list = [t.model_dump() if hasattr(t, 'model_dump') else t for t in result.agent_trace]

    log = QueryLog.objects.create(
        question=question,
        answer=result.answer,
        answerable=result.answerable,
        confidence=confidence_score,
        total_ms=total_ms,
        timing=timing_dict,
        sources=formatted_sources,
        agent_trace=agent_trace_list
    )

    return Response({
        'id': log.id,
        'answer': log.answer,
        'answerable': log.answerable,
        'confidence': log.confidence,
        'total_ms': log.total_ms,
        'timing': log.timing,
        'sources': formatted_sources,
        'agent_trace': log.agent_trace
    })

@api_view(['GET'])
def query_history(request):
    logs = QueryLog.objects.all().order_by('-created_at')[:50]
    serializer = QueryLogSerializer(logs, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def health_check(request):
    pipeline = get_pipeline()
    return Response({
        'status': 'ok',
        'device': getattr(pipeline, 'device', 'cpu'),
        'model_flags': getattr(pipeline, 'model_flags', {}),
        'total_chunks': getattr(pipeline, 'total_chunks', 0)
    })
