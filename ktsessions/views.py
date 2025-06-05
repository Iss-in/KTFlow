import uuid
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.core.cache import cache  # Redis cache

from .models import KTSession, Attachment
from .serializers import (
    KTSessionSerializer,
    KTSessionCreateSerializer,
    KTSessionUpdateSerializer,
    SessionPublicSerializer
)
from .tasks import process_attachment

# Alternative function-based views (if you prefer)
@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def kt_session_list_create(request):
    """
    GET: List all KT sessions for the authenticated user
    POST: Create a new KT session
    """
    if request.method == 'GET':
        sessions = KTSession.objects.filter(created_by=request.user).order_by('-created_at')
        serializer = KTSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = KTSessionCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            session = serializer.save()
            response_serializer = KTSessionSerializer(session)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def kt_session_detail(request, pk):
    """
    GET: Retrieve a specific KT session
    PUT/PATCH: Update a KT session
    DELETE: Delete a KT session
    """
    session = get_object_or_404(KTSession, pk=pk, created_by=request.user)

    if request.method == 'GET':
        serializer = SessionPublicSerializer(session)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = KTSessionUpdateSerializer(session, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            response_serializer = KTSessionSerializer(session)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_sharing_url(request, pk):
    """
    GET: Retrieve sharable URL for a specific KT session
    """

    try:
        session = get_object_or_404(KTSession, pk=pk, created_by=request.user)
        existing_token = None
        for key in cache.iter_keys('*'):
            if cache.get(key) == session.id:
                existing_token = key
                break

        if existing_token:
            # Token exists in cache, return it
            token = existing_token
        else:
            # Generate a new token
            token = str(uuid.uuid4())
            session.share_token = token
            session.save(update_fields=['share_token'])
            cache.set(token, session.id, timeout=60 * 10 )  # 10 minutes TTL

        return Response({'share_url': f'/kt-sessions/get_by_url/{token}'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Additional view for sharing via share_token
@api_view(['GET'])
@authentication_classes([])  # Disables authentication
@permission_classes([])      # Disables permission checks
def kt_session_by_url(request, share_token):
    """
    GET: Retrieve a KT session by share token (public access)
    """
    try:
        session_id = cache.get(share_token)
        if not session_id:
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_404_NOT_FOUND)

        session = get_object_or_404(KTSession, id=session_id)
        serializer = SessionPublicSerializer(session)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

## attachment-based code
@api_view(['POST'])
def create_attachment(request):
    """Create a new attachment"""
    try:
        data = request.data

        # Validate required fields
        required_fields = ['session_id', 'file_type', 'file_url']
        for field in required_fields:
            if field not in data:
                return Response({'error': f'{field} is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate session exists
        try:
            session = KTSession.objects.get(id=data['session_id'])
        except KTSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        # Validate file_type
        valid_file_types = [choice[0] for choice in Attachment.FILE_TYPE_CHOICES]
        if data['file_type'] not in valid_file_types:
            return Response({
                'error': f'Invalid file_type. Must be one of: {valid_file_types}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create attachment (status is handled internally, always starts as 'pending')
        attachment = Attachment.objects.create(
            session=session,
            file_type=data['file_type'],
            file_url=data['file_url'],
            status='pending',  # Always set to pending initially
            transcript=data.get('transcript', ''),
            summary=data.get('summary', '')
        )


        process_attachment.delay(attachment.id)

        return Response({
            'id': attachment.id,
            'session': {
                'id': attachment.session.id,
                'title': attachment.session.title
            },
            'file_type': attachment.file_type,
            'file_url': attachment.file_url,
            'status': attachment.status,
            'transcript': attachment.transcript,
            'summary': attachment.summary,
            'created_at': attachment.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_attachments(request):
    """Get all attachments with optional filtering and pagination"""
    try:
        # Get query parameters (status filtering removed from public API)
        session_id = request.GET.get('session_id')
        file_type = request.GET.get('file_type')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))

        # Build queryset
        queryset = Attachment.objects.select_related('session').all()

        # Apply filters (status filtering removed)
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        if file_type:
            queryset = queryset.filter(file_type=file_type)

        # Order by creation date (newest first)
        queryset = queryset.order_by('-created_at')

        # Paginate
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)

        # Serialize data
        attachments = []
        for attachment in page_obj:
            attachments.append({
                'id': attachment.id,
                'session': {
                    'id': attachment.session.id,
                    'title': attachment.session.title
                },
                'file_type': attachment.file_type,
                'file_url': attachment.file_url,
                'status': attachment.status,
                'transcript': attachment.transcript,
                'summary': attachment.summary,
                'created_at': attachment.created_at.isoformat()
            })

        return Response({
            'attachments': attachments,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })

    except ValueError:
        return Response({'error': 'Invalid page or per_page parameter'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_attachment(request, attachment_id):
    """Get a single attachment by ID"""
    try:
        attachment = get_object_or_404(
            Attachment.objects.select_related('session'),
            id=attachment_id
        )

        return Response({
            'id': attachment.id,
            'session': {
                'id': attachment.session.id,
                'title': attachment.session.title
            },
            'file_type': attachment.file_type,
            'file_url': attachment.file_url,
            'status': attachment.status,
            'transcript': attachment.transcript,
            'summary': attachment.summary,
            'created_at': attachment.created_at.isoformat()
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
def update_attachment(request, attachment_id):
    """Update an attachment"""
    try:
        attachment = get_object_or_404(Attachment, id=attachment_id)
        data = request.data

        # Update allowed fields (status removed from public API)
        updatable_fields = ['file_type', 'file_url', 'transcript', 'summary']

        for field in updatable_fields:
            if field in data:
                if field == 'file_type':
                    valid_file_types = [choice[0] for choice in Attachment.FILE_TYPE_CHOICES]
                    if data[field] not in valid_file_types:
                        return Response({
                            'error': f'Invalid file_type. Must be one of: {valid_file_types}'
                        }, status=status.HTTP_400_BAD_REQUEST)

                setattr(attachment, field, data[field])

        # Handle session update if provided
        if 'session_id' in data:
            try:
                session = KTSession.objects.get(id=data['session_id'])
                attachment.session = session
            except KTSession.DoesNotExist:
                return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        attachment.save()

        return Response({
            'id': attachment.id,
            'session': {
                'id': attachment.session.id,
                'title': attachment.session.title
            },
            'file_type': attachment.file_type,
            'file_url': attachment.file_url,
            'status': attachment.status,
            'transcript': attachment.transcript,
            'summary': attachment.summary,
            'created_at': attachment.created_at.isoformat()
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def delete_attachment(request, attachment_id):
    """Delete an attachment"""
    try:
        attachment = get_object_or_404(Attachment, id=attachment_id)
        attachment.delete()

        return Response({'message': 'Attachment deleted successfully'})

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

