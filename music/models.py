import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date


def validate_audio_file(value):
    """Validează că fișierul este audio (MP3 sau WAV)."""
    import os
    ext = os.path.splitext(value.name)[1].lower()
    allowed = ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a']
    if ext not in allowed:
        raise ValidationError(
            f'Tip de fișier invalid ({ext}). Extensii permise: {", ".join(allowed)}'
        )


class Genre(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nume gen")
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, default='🎵', verbose_name="Icon emoji")

    class Meta:
        verbose_name = "Gen muzical"
        verbose_name_plural = "Genuri muzicale"

    def __str__(self):
        return self.name


class Mood(models.Model):
    name = models.CharField(max_length=100, verbose_name="Stare/Mood")
    slug = models.SlugField(unique=True)
    color = models.CharField(max_length=20, default='#7c3aed', verbose_name="Culoare hex")

    class Meta:
        verbose_name = "Mood"
        verbose_name_plural = "Mood-uri"

    def __str__(self):
        return self.name


class Song(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titlu melodie")
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Gen")
    mood = models.ForeignKey(Mood, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Mood")
    audio_file = models.FileField(upload_to='songs/', validators=[validate_audio_file], verbose_name="Fișier audio (MP3/WAV)")
    cover_image = models.ImageField(upload_to='covers/', null=True, blank=True, verbose_name="Copertă")
    duration = models.PositiveIntegerField(default=0, verbose_name="Durată (secunde)")
    bpm = models.PositiveIntegerField(null=True, blank=True, verbose_name="BPM")
    is_active = models.BooleanField(default=True, verbose_name="Activ")
    is_featured = models.BooleanField(default=False, verbose_name="Recomandat")
    plays_count = models.PositiveIntegerField(default=0, verbose_name="Redări")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Melodie"
        verbose_name_plural = "Melodii"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def duration_display(self):
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02d}"


class Playlist(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nume playlist")
    description = models.TextField(blank=True, verbose_name="Descriere")
    songs = models.ManyToManyField(Song, blank=True, verbose_name="Melodii")
    cover_image = models.ImageField(upload_to='playlists/', null=True, blank=True)
    is_public = models.BooleanField(default=True, verbose_name="Public")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Utilizator", related_name='playlists')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Playlist"
        verbose_name_plural = "Playlist-uri"

    def __str__(self):
        if self.user:
            return f"{self.name} ({self.user.username})"
        return self.name


class ContactMessage(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nume")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Telefon")
    business = models.CharField(max_length=200, blank=True, verbose_name="Tip locație")
    message = models.TextField(verbose_name="Mesaj")
    is_read = models.BooleanField(default=False, verbose_name="Citit")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mesaj contact"
        verbose_name_plural = "Mesaje contact"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.email}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    subscription_start = models.DateField(null=True, blank=True, verbose_name="Început abonament")
    subscription_end = models.DateField(null=True, blank=True, verbose_name="Sfârșit abonament")
    notes = models.TextField(blank=True, verbose_name="Observații")
    plain_password = models.CharField(max_length=100, blank=True, default='', verbose_name="Parolă (text clar)")
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name="Token verificare")

    class Meta:
        verbose_name = "Profil utilizator"
        verbose_name_plural = "Profile utilizatori"

    def __str__(self):
        return f"Profil: {self.user.username}"

    def is_subscription_active(self):
        """Verifică dacă abonamentul este activ la data curentă."""
        if self.user.is_staff:
            return True
        if not self.subscription_start or not self.subscription_end:
            return False
        today = date.today()
        return self.subscription_start <= today <= self.subscription_end

    def days_remaining(self):
        """Returnează zilele rămase din abonament."""
        if not self.subscription_end:
            return 0
        remaining = (self.subscription_end - date.today()).days
        return max(0, remaining)

    def subscription_status(self):
        """Returnează statusul abonamentului."""
        if self.user.is_staff:
            return 'staff'
        if not self.subscription_start or not self.subscription_end:
            return 'no_subscription'
        today = date.today()
        if today < self.subscription_start:
            return 'not_started'
        if today > self.subscription_end:
            return 'expired'
        return 'active'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'În așteptare'),
        ('paid', 'Plătită'),
        ('cancelled', 'Anulată'),
    ]
    PAYMENT_TYPE_CHOICES = [
        ('normal', 'Normal'),
        ('barter', 'Barter'),
    ]
    PLAN_CHOICES = [
        ('standard', 'Standard'),
        ('starter', 'Starter'),
        ('business', 'Business'),
        ('enterprise', 'Enterprise'),
    ]
    BILLING_CHOICES = [
        ('monthly', 'Lunar'),
        ('annual', 'Anual'),
    ]

    reference = models.CharField(max_length=20, unique=True, verbose_name="Referință")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name="Utilizator")
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, verbose_name="Plan")
    billing = models.CharField(max_length=10, choices=BILLING_CHOICES, default='annual', verbose_name="Facturare")
    business_type = models.CharField(max_length=50, verbose_name="Tip afacere")
    business_size = models.CharField(max_length=50, verbose_name="Suprafață")
    price_monthly = models.IntegerField(verbose_name="Preț lunar (lei)")
    price_total = models.IntegerField(verbose_name="Preț total (lei)")

    # Company details
    company_name = models.CharField(max_length=200, verbose_name="Denumire firmă")
    brand_name = models.CharField(max_length=200, blank=True, verbose_name="Nume brand / locație")
    company_cui = models.CharField(max_length=20, verbose_name="CUI")
    company_address = models.TextField(verbose_name="Adresa firmei")
    venue_address = models.TextField(blank=True, verbose_name="Adresa locației")
    company_email = models.EmailField(verbose_name="Email firmă")
    company_phone = models.CharField(max_length=30, verbose_name="Telefon firmă")
    company_reg = models.CharField(max_length=30, blank=True, verbose_name="Nr. Reg. Comerț")
    company_representative = models.CharField(max_length=200, blank=True, verbose_name="Reprezentat de")
    company_representative_role = models.CharField(max_length=100, blank=True, verbose_name="Funcția")

    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES, default='normal', verbose_name="Tip plată")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    oblio_invoice = models.CharField(max_length=100, blank=True, verbose_name="Nr. factură Oblio")
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Data plată")

    class Meta:
        verbose_name = "Comandă"
        verbose_name_plural = "Comenzi"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference} - {self.company_name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"SF-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Creează automat un UserProfile la crearea unui User."""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Salvează profilul utilizatorului."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
