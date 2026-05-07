from django.db import models
from django.contrib.auth.models import User


class CV(models.Model):

    TEMPLATE_CHOICES = [
        ('modern',  'Modern'),
        ('classic', 'Classic'),
        ('minimal', 'Minimal'),
    ]

    FONT_CHOICES = [
        ('DM Sans',          'DM Sans'),
        ('Roboto',           'Roboto'),
        ('Open Sans',        'Open Sans'),
        ('Lato',             'Lato'),
        ('Montserrat',       'Montserrat'),
        ('Playfair Display', 'Playfair Display'),
        ('Raleway',          'Raleway'),
    ]

    FONT_SIZE_CHOICES = [
        ('small',  'Small (9pt)'),
        ('medium', 'Medium (10pt)'),
        ('large',  'Large (11pt)'),
    ]

    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cvs')
    title         = models.CharField(max_length=100, default='My CV')
    template      = models.CharField(max_length=20, choices=TEMPLATE_CHOICES, default='modern')

    # Personal info
    full_name     = models.CharField(max_length=100, blank=True)
    job_title     = models.CharField(max_length=100, blank=True)
    email         = models.EmailField(blank=True)
    phone         = models.CharField(max_length=20, blank=True)
    address       = models.CharField(max_length=255, blank=True)
    city          = models.CharField(max_length=100, blank=True)
    country       = models.CharField(max_length=100, blank=True)
    postal_code   = models.CharField(max_length=20, blank=True)
    linkedin      = models.URLField(blank=True)
    github        = models.URLField(blank=True)
    website       = models.URLField(blank=True)
    summary       = models.TextField(blank=True)
    profile_photo = models.ImageField(upload_to='cv_photos/', blank=True, null=True)

    # Customization
    primary_color   = models.CharField(max_length=7, default='#1a1a2e')
    secondary_color = models.CharField(max_length=7, default='#e63946')
    font_family     = models.CharField(max_length=50, choices=FONT_CHOICES, default='DM Sans')
    font_size       = models.CharField(max_length=10, choices=FONT_SIZE_CHOICES, default='medium')

    # Per-field typography overrides stored as JSON.
    # Structure: { "field_name": { "font_family": "...", "font_size": "14px",
    #              "font_weight": "400", "font_style": "normal", "color": "#000000" } }
    field_styles    = models.JSONField(default=dict, blank=True)

    # Progress
    current_step  = models.PositiveSmallIntegerField(default=1)
    is_complete   = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'CV'
        verbose_name_plural = 'CVs'

    def __str__(self):
        return f"{self.title} — {self.user.username}"

    def get_completion_percentage(self):
        return min(int((self.current_step / 5) * 100), 100)

    def get_font_size_pt(self):
        """Return actual pt value for PDF generation."""
        mapping = {'small': 9, 'medium': 10, 'large': 11}
        return mapping.get(self.font_size, 10)

    def get_font_size_px(self):
        """Return px value for live preview."""
        mapping = {'small': '13px', 'medium': '15px', 'large': '17px'}
        return mapping.get(self.font_size, '15px')

    def get_field_style(self, field_name):
        """Return inline CSS string for a given field name."""
        styles = self.field_styles or {}
        fs = styles.get(field_name, {})
        if not fs:
            return ''
        parts = []
        if fs.get('font_family'):
            parts.append(f"font-family:'{fs['font_family']}', sans-serif;")
        if fs.get('font_size'):
            parts.append(f"font-size:{fs['font_size']};")
        if fs.get('font_weight'):
            parts.append(f"font-weight:{fs['font_weight']};")
        if fs.get('font_style'):
            parts.append(f"font-style:{fs['font_style']};")
        if fs.get('color'):
            parts.append(f"color:{fs['color']};")
        return ' '.join(parts)

    def get_field_styles_json(self):
        """Return field_styles serialised as JSON for JavaScript."""
        import json
        return json.dumps(self.field_styles or {})


class Education(models.Model):
    DEGREE_CHOICES = [
        ('bac',       'Baccalauréat'),
        ('bac+2',     'Bac+2 / DUT / BTS'),
        ('licence',   'Licence / Bachelor'),
        ('master',    'Master'),
        ('ingenieur', "Diplôme d'Ingénieur"),
        ('doctorat',  'Doctorat / PhD'),
        ('other',     'Other'),
    ]
    cv                   = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='educations')
    degree               = models.CharField(max_length=20, choices=DEGREE_CHOICES)
    field_of_study       = models.CharField(max_length=100, blank=True)
    institution          = models.CharField(max_length=150)
    institution_location = models.CharField(max_length=100, blank=True)
    start_date           = models.DateField()
    end_date             = models.DateField(null=True, blank=True)
    is_current           = models.BooleanField(default=False)
    grade                = models.CharField(max_length=50, blank=True)
    description          = models.TextField(blank=True)
    order                = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', '-start_date']

    def __str__(self):
        return f"{self.get_degree_display()} at {self.institution}"

    @property
    def end_display(self):
        return 'Present' if self.is_current else (self.end_date.strftime('%b %Y') if self.end_date else '')


class Experience(models.Model):
    EMPLOYMENT_CHOICES = [
        ('full_time',  'Full-Time'),
        ('part_time',  'Part-Time'),
        ('internship', 'Internship / Stage'),
        ('freelance',  'Freelance / Contract'),
        ('volunteer',  'Volunteer'),
        ('apprentice', 'Apprenticeship'),
        ('other',      'Other'),
    ]
    cv               = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='experiences')
    position         = models.CharField(max_length=100)
    company          = models.CharField(max_length=100)
    company_location = models.CharField(max_length=100, blank=True)
    employment_type  = models.CharField(max_length=20, choices=EMPLOYMENT_CHOICES, default='full_time')
    start_date       = models.DateField()
    end_date         = models.DateField(null=True, blank=True)
    is_current       = models.BooleanField(default=False)
    description      = models.TextField(blank=True)
    order            = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', '-start_date']

    def __str__(self):
        return f"{self.position} at {self.company}"

    @property
    def end_display(self):
        return 'Present' if self.is_current else (self.end_date.strftime('%b %Y') if self.end_date else '')


class Skill(models.Model):
    CATEGORY_CHOICES = [
        ('technical', 'Technical'),
        ('soft',      'Soft Skill'),
        ('tool',      'Tool / Software'),
        ('other',     'Other'),
    ]
    PROFICIENCY_CHOICES = [
        (1, 'Beginner'),
        (2, 'Elementary'),
        (3, 'Intermediate'),
        (4, 'Advanced'),
        (5, 'Expert'),
    ]
    cv          = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='skills')
    name        = models.CharField(max_length=100)
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='technical')
    proficiency = models.PositiveSmallIntegerField(choices=PROFICIENCY_CHOICES, default=3)
    order       = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_proficiency_display()})"


class Language(models.Model):
    LEVEL_CHOICES = [
        ('A1', 'A1 – Beginner'), ('A2', 'A2 – Elementary'),
        ('B1', 'B1 – Intermediate'), ('B2', 'B2 – Upper Intermediate'),
        ('C1', 'C1 – Advanced'), ('C2', 'C2 – Proficient'),
        ('native', 'Native / Bilingual'),
    ]
    cv    = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='languages')
    name  = models.CharField(max_length=50)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"


class Interest(models.Model):
    cv    = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='interests')
    name  = models.CharField(max_length=100)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
