from django.db import models


class Account(models.Model):
    """Simple account holder with contact credentials."""

    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    storage_quota_gb = models.PositiveSmallIntegerField(default=100)
    security_profile = models.CharField(max_length=50, default="256-bit AES")
    plan_name = models.CharField(max_length=60, default="Private Cloud")

    def __str__(self):
        return self.email


class Upload(models.Model):
    """Tracks files uploaded by a specific account."""

    class Visibility(models.TextChoices):
        PRIVATE = "private", "Private"
        TEAM = "team", "Team share"
        PUBLIC = "public", "Public link"

    class Status(models.TextChoices):
        SYNCED = "synced", "Synced"
        QUEUED = "queued", "Queued"
        PROCESSING = "processing", "Processing"

    account = models.ForeignKey(Account, related_name="uploads", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=64)
    visibility = models.CharField(max_length=16, choices=Visibility.choices, default=Visibility.PRIVATE)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    size_mb = models.PositiveIntegerField()
    synced_at = models.DateTimeField(null=True, blank=True)
    has_public_link = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def visibility_label(self):
        return self.Visibility(self.visibility).label

    def status_label(self):
        return self.Status(self.status).label

    def status_css_class(self):
        """Map status to the dashboard badge color."""
        return {
            self.Status.SYNCED: "success",
            self.Status.QUEUED: "warning",
        }.get(self.status, "processing")



