import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)

INTERNAL_TEAM_EMAIL = "vagailife234@gmail.com"


def send_internal_order_status_email(order, status_history_entry=None):
    """
    Send an email notification to the internal team when an order is placed
    or its status changes.
    """
    try:
        subject = f"Order Notification: #{order.order_number} - {order.get_status_display()}"
        
        context = {
            "order": order,
            "status": order.get_status_display(),
            "payment_status": order.get_payment_status_display(),
            "notes": status_history_entry.notes if status_history_entry else "",
        }
        
        text_body = render_to_string("emails/internal_order_notification.txt", context)
        html_body = render_to_string("emails/internal_order_notification.html", context)
        
        message = EmailMultiAlternatives(
            subject,
            text_body,
            settings.DEFAULT_FROM_EMAIL,
            [INTERNAL_TEAM_EMAIL],
        )
        message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)
        
        logger.info(f"Internal notification email sent for order {order.order_number}")
        return True
    except Exception as e:
        logger.exception(f"Failed to send internal order notification for {order.order_number}")
        return False
