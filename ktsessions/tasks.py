from celery import shared_task
import time
from .models import Attachment


@shared_task
def process_attachment(attachment_id):
    """
    Process attachment: change status to processing, wait, then mark as finished
    """
    try:
        attachment = Attachment.objects.get(id=attachment_id)

        # Update status to processing
        print(f"Processing attachment {attachment_id}", flush=True)
        attachment.status = 'processing'

        attachment.save()
        print(f"Attachment {attachment_id} updated to processing", flush=True)

        # Simulate processing time (1 minute)
        time.sleep(10)
        attachment.transcript = 'demo transcript'
        attachment.summary = 'demo summary'
        # Update status to finished
        attachment.status = 'done'
        attachment.save()
        print(f"Attachment {attachment_id} updated to done")

        return f"Attachment {attachment_id} processed successfully"

    except Attachment.DoesNotExist:
        return f"Attachment {attachment_id} not found"
    except Exception as e:
        # If something goes wrong, you might want to set status to 'failed'
        try:
            attachment = Attachment.objects.get(id=attachment_id)
            attachment.status = 'failed'
            attachment.save()
        except:
            pass
        return f"Error processing attachment {attachment_id}: {str(e)}"