from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden, Http404, FileResponse
from django.conf import settings
from .models import Work, SubtitleEntry
from pathlib import Path
from django.db.models import Q

def index(request):
    return render(request, 'catalogue/index.html')

def search(request):
    anidb_id = request.GET.get('anidb')
    tmdb_tv_id = request.GET.get('tmdb_tv')
    tmdb_movie_id = request.GET.get('tmdb_movie')
    tvdb_id = request.GET.get('tvdb')
    title = request.GET.get('title')
    language = request.GET.get('language')
    release = request.GET.get('release')

    works = Work.objects.all()

    if anidb_id:
        works = works.filter(
            external_mappings__provider='anidb',
            external_mappings__external_id=anidb_id
        )
    if tmdb_tv_id:
        works = works.filter(
            external_mappings__provider='tmdb',
            external_mappings__media_kind='tv',
            external_mappings__external_id=tmdb_tv_id
        )
    if tmdb_movie_id:
        works = works.filter(
            external_mappings__provider='tmdb',
            external_mappings__media_kind='movie',
            external_mappings__external_id=tmdb_movie_id
        )
    if tvdb_id:
        works = works.filter(
            external_mappings__provider='tvdb',
            external_mappings__external_id=tvdb_id
        )

    if title:
        works = works.filter(title__icontains=title)

    if language or release:
        q_obj = Q()
        if language:
            q_obj &= Q(subtitle_entries__language__icontains=language)
        if release:
            q_obj &= Q(subtitle_entries__release_group__icontains=release)

        q_obj &= Q(subtitle_entries__status=SubtitleEntry.Status.PUBLISHED)
        works = works.filter(q_obj)

    works = works.distinct()

    return render(request, 'catalogue/search.html', {'works': works})

def work_detail(request, work_id):
    work = get_object_or_404(Work, id=work_id)
    entries = work.subtitle_entries.filter(status=SubtitleEntry.Status.PUBLISHED)
    return render(request, 'catalogue/work_detail.html', {'work': work, 'entries': entries})

def download(request, entry_id):
    entry = get_object_or_404(SubtitleEntry, id=entry_id)

    if entry.status != SubtitleEntry.Status.PUBLISHED:
        if not request.user.is_staff:
            return HttpResponseForbidden("This subtitle is pending review and not available for download.")

    managed_dir = Path(settings.MANAGED_MEDIA_ROOT).resolve()
    file_path = managed_dir / entry.blob.storage_key

    if not str(file_path.resolve()).startswith(str(managed_dir)):
        raise Http404("Invalid storage key")

    if not file_path.exists():
        raise Http404("File not found on disk")

    safe_filename = entry.original_filename.replace('"', '').replace('\n', '')

    # Use FileResponse for memory-safe streaming
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=safe_filename)
