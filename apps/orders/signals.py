from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Order, OrderStatusHistory


@receiver(post_save, sender=OrderStatusHistory)
def sync_order_status_from_history(sender, instance, created, **kwargs):
    """When OrderStatusHistory is added, update order.status to latest status"""
    if created:
        latest = instance.order.status_history.first()
        if latest:
            Order.objects.filter(pk=instance.order_id).update(
                status=latest.status,
                updated_at=timezone.now(),
            )


@receiver(pre_save, sender=Order)
def create_status_history_on_status_change(sender, instance, **kwargs):
    """When order.status is changed directly, create a status history entry"""
    if instance.pk:
        try:
            old_order = Order.objects.get(pk=instance.pk)
            if old_order.status != instance.status:
                OrderStatusHistory.objects.create(
                    order=instance,
                    status=instance.status,
                    notes=f"Status changed to {instance.get_status_display()}",
                    changed_by=None,
                )
        except Order.DoesNotExist:
            pass
