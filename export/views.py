import io
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from cv.models import CV
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    HRFlowable, Table, TableStyle, KeepTogether,
    Frame, PageTemplate, BaseDocTemplate,
)
from reportlab.platypus.flowables import Flowable


# ── Colour helper ─────────────────────────────────────────────────────────────

def hex_col(hex_str, fallback='#1a1a2e'):
    try:
        h = hex_str.strip().lstrip('#')
        return colors.Color(int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255)
    except Exception:
        h = fallback.lstrip('#')
        return colors.Color(int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255)


# ── Rounded-rect background flowable (used by Modern sidebar) ─────────────────

class SidebarRect(Flowable):
    """Draws a filled rectangle — used as the Modern template sidebar."""
    def __init__(self, width, height, fill_color):
        super().__init__()
        self.width  = width
        self.height = height
        self._fill  = fill_color

    def draw(self):
        self.canv.setFillColor(self._fill)
        self.canv.rect(0, 0, self.width, self.height, stroke=0, fill=1)


class ColorBar(Flowable):
    """Left-edge accent bar for Minimal template."""
    def __init__(self, height, color, width=4):
        super().__init__()
        self.width  = width
        self.height = height
        self._color = color

    def draw(self):
        self.canv.setFillColor(self._color)
        self.canv.rect(0, 0, self.width, self.height, stroke=0, fill=1)


# ── Circular profile photo ───────────────────────────────────────────────────

class CircularPhoto(Flowable):
    """
    Draws a profile photo cropped to a perfect circle.
    - Saves/restores canvas state so the clip doesn't bleed into other content.
    - Scales the image to FILL the circle (cover behaviour), then clips.
    - Draws a subtle white ring border on top.
    """
    def __init__(self, path, diameter, border_color=None):
        super().__init__()
        self._path   = path
        self.width   = diameter
        self.height  = diameter
        self._border = border_color
        self._r      = diameter / 2

    def draw(self):
        c   = self.canv
        r   = self._r
        d   = self.width          # diameter in points
        c.saveState()
        try:
            from reportlab.lib.utils import ImageReader
            img    = ImageReader(self._path)
            iw, ih = img.getSize()

            # Cover: scale so the shorter side fills the diameter
            scale  = max(d / iw, d / ih)
            sw, sh = iw * scale, ih * scale

            # Centre the scaled image over the circle
            ox = (d - sw) / 2
            oy = (d - sh) / 2

            # Clip path — circle centred at (r, r)
            p = c.beginPath()
            p.circle(r, r, r)
            c.clipPath(p, stroke=0, fill=0)

            # Draw scaled image (fills circle, excess is clipped)
            c.drawImage(self._path, ox, oy, width=sw, height=sh, mask='auto')

        except Exception:
            # Fallback: semi-transparent white circle placeholder
            c.setFillColor(colors.Color(1, 1, 1, 0.15))
            c.circle(r, r, r, stroke=0, fill=1)

        c.restoreState()

        # Border ring drawn AFTER restoreState so it's not clipped
        if self._border:
            c.saveState()
            c.setStrokeColor(self._border)
            c.setLineWidth(1.8)
            c.circle(r, r, r - 0.9, stroke=1, fill=0)
            c.restoreState()


# ── Skill pill (inline box) ───────────────────────────────────────────────────

class PillFlowable(Flowable):
    """Draws a single rounded pill badge."""
    def __init__(self, text, text_color, bg_color, font='Helvetica', font_size=7.5):
        super().__init__()
        self._text  = text
        self._tc    = text_color
        self._bg    = bg_color
        self._font  = font
        self._fs    = font_size
        pad_h, pad_v = 6, 3
        from reportlab.pdfbase.pdfmetrics import stringWidth
        tw = stringWidth(text, font, font_size)
        self.width  = tw + pad_h * 2
        self.height = font_size + pad_v * 2
        self._pad_h = pad_h
        self._pad_v = pad_v

    def draw(self):
        c = self.canv
        r = self.height / 2
        c.setFillColor(self._bg)
        c.roundRect(0, 0, self.width, self.height, r, stroke=0, fill=1)
        c.setFillColor(self._tc)
        c.setFont(self._font, self._fs)
        c.drawString(self._pad_h, self._pad_v, self._text)


# ── Inline pill row builder ───────────────────────────────────────────────────

def pill_row(items, text_color, bg_color, font_size=7.5):
    """Return a Table containing PillFlowable items wrapped in rows."""
    if not items:
        return None
    pills = [PillFlowable(i, text_color, bg_color, font_size=font_size) for i in items]
    # Pack into rows of up to 3
    rows, row = [], []
    for p in pills:
        row.append(p)
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    # Pad last row
    while len(rows[-1]) < 3:
        rows[-1].append(Spacer(1,1))
    col_w = 58
    tbl = Table(rows, colWidths=[col_w]*3, hAlign='LEFT')
    tbl.setStyle(TableStyle([
        ('LEFTPADDING',   (0,0),(-1,-1), 2),
        ('RIGHTPADDING',  (0,0),(-1,-1), 2),
        ('TOPPADDING',    (0,0),(-1,-1), 2),
        ('BOTTOMPADDING', (0,0),(-1,-1), 2),
    ]))
    return tbl


# ═══════════════════════════════════════════════════════════════════════════════
#  MODERN TEMPLATE  (sidebar left, main right)
# ═══════════════════════════════════════════════════════════════════════════════

def build_modern(cv, experiences, educations, skills, languages, interests, buffer):
    PAGE_W, PAGE_H = A4
    SIDEBAR_W = 5.8 * cm
    MARGIN     = 0
    INNER_PAD  = 0.55 * cm

    primary   = hex_col(cv.primary_color,   '#1a1a2e')
    secondary = hex_col(cv.secondary_color, '#e63946')
    white     = colors.white
    muted     = colors.HexColor('#9ca3af')
    dark      = colors.HexColor('#374151')
    light_bg  = colors.HexColor('#f3f4f6')

    # ── Sidebar styles ────────────────────────────────────
    s_name = ParagraphStyle('SbName', fontSize=13, fontName='Helvetica-Bold',
                             textColor=white, leading=16, spaceAfter=2)
    s_role = ParagraphStyle('SbRole', fontSize=8, fontName='Helvetica',
                             textColor=colors.HexColor('#93c5fd'), spaceAfter=8)
    s_sec  = ParagraphStyle('SbSec',  fontSize=6.5, fontName='Helvetica-Bold',
                             textColor=secondary, spaceBefore=10, spaceAfter=3,
                             letterSpacing=1.2)
    s_contact = ParagraphStyle('SbContact', fontSize=7, fontName='Helvetica',
                                textColor=colors.HexColor('#d1d5db'), spaceAfter=3, leading=10)
    s_skill = ParagraphStyle('SbSkill', fontSize=7.5, fontName='Helvetica',
                              textColor=white, spaceAfter=3)

    # ── Main styles ───────────────────────────────────────
    m_name  = ParagraphStyle('MnName', fontSize=22, fontName='Helvetica-Bold',
                              textColor=primary, leading=26, spaceAfter=2)
    m_role  = ParagraphStyle('MnRole', fontSize=11, fontName='Helvetica',
                              textColor=secondary, spaceAfter=6)
    m_sec   = ParagraphStyle('MnSec',  fontSize=7, fontName='Helvetica-Bold',
                              textColor=secondary, spaceBefore=12, spaceAfter=3,
                              letterSpacing=1.5)
    m_etitle = ParagraphStyle('MnET', fontSize=9.5, fontName='Helvetica-Bold',
                               textColor=primary, spaceAfter=1)
    m_esub   = ParagraphStyle('MnES', fontSize=8, fontName='Helvetica-Oblique',
                               textColor=colors.HexColor('#6b7280'), spaceAfter=1)
    m_edate  = ParagraphStyle('MnED', fontSize=7.5, fontName='Helvetica',
                               textColor=secondary, alignment=TA_RIGHT)
    m_body   = ParagraphStyle('MnBd', fontSize=8.5, fontName='Helvetica',
                               textColor=dark, leading=13, spaceAfter=4)
    m_sum    = ParagraphStyle('MnSum', fontSize=9, fontName='Helvetica',
                               textColor=dark, leading=14, spaceAfter=6)

    # ── Build sidebar content ─────────────────────────────
    sb = []

    # Profile photo — large circle, centred, at the very top of the sidebar
    PHOTO_D      = 2.0 * cm          # matches preview sidebar circle size
    SIDEBAR_INNER = SIDEBAR_W - INNER_PAD * 2

    if cv.profile_photo:
        try:
            photo_cell = CircularPhoto(
                cv.profile_photo.path,
                PHOTO_D,
                border_color=colors.Color(1, 1, 1, 0.3)
            )
            photo_tbl = Table(
                [[photo_cell]],
                colWidths=[SIDEBAR_INNER]
            )
            photo_tbl.setStyle(TableStyle([
                ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
                ('LEFTPADDING',   (0, 0), (-1, -1), 0),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
                ('TOPPADDING',    (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            sb.append(photo_tbl)
        except Exception:
            pass  # photo missing or corrupt — skip silently

    # Contact
    sb.append(Paragraph('CONTACT', s_sec))
    sb.append(HRFlowable(width=SIDEBAR_W - INNER_PAD*2,
                         thickness=0.5, color=colors.Color(1,1,1,0.2), spaceAfter=4))
    contacts = []
    if cv.email:    contacts.append(('✉', cv.email))
    if cv.phone:    contacts.append(('☎', cv.phone))
    if cv.city:
        loc = cv.city + (f', {cv.country}' if cv.country else '')
        contacts.append(('⌂', loc))
    if cv.linkedin: contacts.append(('in', cv.linkedin))
    if cv.github:   contacts.append(('⌥', cv.github))
    if cv.website:  contacts.append(('⊕', cv.website))
    for icon, val in contacts:
        sb.append(Paragraph(f'<font size="6">{icon}</font>  {val}', s_contact))

    # Skills
    if skills:
        sb.append(Paragraph('SKILLS', s_sec))
        sb.append(HRFlowable(width=SIDEBAR_W - INNER_PAD*2,
                             thickness=0.5, color=colors.Color(1,1,1,0.2), spaceAfter=4))
        for sk in skills:
            sb.append(Paragraph(f'• {sk.name}', s_skill))

    # Languages
    if languages:
        sb.append(Paragraph('LANGUAGES', s_sec))
        sb.append(HRFlowable(width=SIDEBAR_W - INNER_PAD*2,
                             thickness=0.5, color=colors.Color(1,1,1,0.2), spaceAfter=4))
        for lg in languages:
            sb.append(Paragraph(f'{lg.name}  <font size="6.5" color="#9ca3af">{lg.get_level_display()}</font>', s_skill))

    # Interests
    if interests:
        sb.append(Paragraph('INTERESTS', s_sec))
        sb.append(HRFlowable(width=SIDEBAR_W - INNER_PAD*2,
                             thickness=0.5, color=colors.Color(1,1,1,0.2), spaceAfter=4))
        for it in interests:
            sb.append(Paragraph(f'• {it.name}', s_skill))

    # ── Build main content ────────────────────────────────
    mn = []

    # Name + role at top of main column (matches live preview layout)
    mn.append(Paragraph(cv.full_name or cv.title, m_name))
    if cv.job_title:
        mn.append(Paragraph(cv.job_title, m_role))
    mn.append(Spacer(1, 6))

    # Summary
    if cv.summary:
        mn.append(Paragraph('PROFILE', m_sec))
        mn.append(HRFlowable(width='100%', thickness=0.5,
                             color=colors.HexColor('#e5e7eb'), spaceAfter=5))
        mn.append(Paragraph(cv.summary, m_sum))

    def section_entries(title, entries_data):
        if not entries_data:
            return
        mn.append(Paragraph(title, m_sec))
        mn.append(HRFlowable(width='100%', thickness=0.5,
                             color=colors.HexColor('#e5e7eb'), spaceAfter=5))
        for (etitle, esub, edate, edesc) in entries_data:
            row = Table([[Paragraph(etitle, m_etitle),
                          Paragraph(edate,  m_edate)]],
                        colWidths=['68%', '32%'])
            row.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                                     ('LEFTPADDING',(0,0),(-1,-1),0),
                                     ('RIGHTPADDING',(0,0),(-1,-1),0)]))
            block = [row, Paragraph(esub, m_esub)]
            if edesc:
                block.append(Paragraph(edesc, m_body))
            block.append(Spacer(1, 5))
            mn.append(KeepTogether(block))

    exp_data = []
    for e in experiences:
        exp_data.append((
            f'<b>{e.position}</b>',
            f'{e.company}' + (f' · {e.company_location}' if e.company_location else '') +
            f' · <i>{e.get_employment_type_display()}</i>',
            f'{e.start_date.strftime("%b %Y")} — {e.end_display}',
            e.description or '',
        ))
    section_entries('EXPERIENCE', exp_data)

    edu_data = []
    for e in educations:
        deg = e.get_degree_display() + (f' — {e.field_of_study}' if e.field_of_study else '')
        sub = e.institution + (f' · {e.institution_location}' if e.institution_location else '')
        if e.grade: sub += f' · {e.grade}'
        edu_data.append((
            f'<b>{deg}</b>',
            sub,
            f'{e.start_date.strftime("%b %Y")} — {e.end_display}',
            e.description or '',
        ))
    section_entries('EDUCATION', edu_data)

    # ── Two-column layout via BaseDocTemplate ─────────────
    doc = BaseDocTemplate(buffer, pagesize=A4,
                          leftMargin=0, rightMargin=0,
                          topMargin=0, bottomMargin=0)

    main_x = SIDEBAR_W
    main_w = PAGE_W - SIDEBAR_W
    pad    = INNER_PAD

    sidebar_frame = Frame(0, 0, SIDEBAR_W, PAGE_H,
                          leftPadding=pad, rightPadding=pad,
                          topPadding=pad*1.5, bottomPadding=pad,
                          id='sidebar')
    main_frame    = Frame(main_x, 0, main_w, PAGE_H,
                          leftPadding=pad, rightPadding=pad,
                          topPadding=pad*1.5, bottomPadding=pad,
                          id='main')

    def draw_sidebar_bg(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(primary)
        canvas.rect(0, 0, SIDEBAR_W, PAGE_H, stroke=0, fill=1)
        canvas.restoreState()

    page_tmpl = PageTemplate(id='TwoCol',
                             frames=[sidebar_frame, main_frame],
                             onPage=draw_sidebar_bg)
    doc.addPageTemplates([page_tmpl])
    doc.build(sb + [FrameBreak()] + mn)


# ── FrameBreak flowable ───────────────────────────────────────────────────────
from reportlab.platypus import FrameBreak
try:
    from PIL import Image as PILImage
    _PIL_OK = True
except ImportError:
    _PIL_OK = False


# ═══════════════════════════════════════════════════════════════════════════════
#  CLASSIC TEMPLATE  (single column, bold underline header)
# ═══════════════════════════════════════════════════════════════════════════════

def build_classic(cv, experiences, educations, skills, languages, interests, buffer):
    primary   = hex_col(cv.primary_color,   '#1a1a2e')
    secondary = hex_col(cv.secondary_color, '#e63946')
    dark      = colors.HexColor('#374151')
    muted     = colors.HexColor('#6b7280')
    light     = colors.HexColor('#e5e7eb')

    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm,  bottomMargin=2*cm)
    W = doc.width

    # Styles
    s_name    = ParagraphStyle('CName', fontSize=26, fontName='Helvetica-Bold',
                                textColor=primary, spaceAfter=3, leading=30)
    s_role    = ParagraphStyle('CRole', fontSize=12, fontName='Helvetica',
                                textColor=secondary, spaceAfter=4)
    s_contact = ParagraphStyle('CCont', fontSize=8, fontName='Helvetica',
                                textColor=muted, spaceAfter=0, alignment=TA_CENTER)
    s_sec     = ParagraphStyle('CSec',  fontSize=8, fontName='Helvetica-Bold',
                                textColor=secondary, spaceBefore=14, spaceAfter=4,
                                letterSpacing=2)
    s_etitle  = ParagraphStyle('CET',   fontSize=10, fontName='Helvetica-Bold',
                                textColor=primary, spaceAfter=1)
    s_esub    = ParagraphStyle('CES',   fontSize=8.5, fontName='Helvetica-Oblique',
                                textColor=muted, spaceAfter=2)
    s_edate   = ParagraphStyle('CED',   fontSize=8, fontName='Helvetica',
                                textColor=secondary, alignment=TA_RIGHT)
    s_body    = ParagraphStyle('CBd',   fontSize=9, fontName='Helvetica',
                                textColor=dark, leading=14, spaceAfter=4)
    s_skill   = ParagraphStyle('CSk',   fontSize=8.5, fontName='Helvetica',
                                textColor=dark, spaceAfter=2)

    story = []

    # ── Header ────────────────────────────────────────────
    story.append(Paragraph(cv.full_name or cv.title, s_name))
    if cv.job_title:
        story.append(Paragraph(cv.job_title, s_role))

    # Contact row centred
    parts = []
    if cv.email:   parts.append(cv.email)
    if cv.phone:   parts.append(cv.phone)
    if cv.city:    parts.append(cv.city + (f', {cv.country}' if cv.country else ''))
    if cv.linkedin: parts.append(cv.linkedin)
    if cv.github:  parts.append(cv.github)
    if cv.website: parts.append(cv.website)
    if parts:
        story.append(Paragraph('  ·  '.join(parts), s_contact))

    story.append(HRFlowable(width='100%', thickness=3,
                            color=primary, spaceAfter=8, spaceBefore=6))

    def section(title, entries):
        story.append(Paragraph(title, s_sec))
        story.append(HRFlowable(width='100%', thickness=0.5,
                                color=light, spaceAfter=6))
        for (etitle, esub, edate, edesc) in entries:
            row = Table([[Paragraph(etitle, s_etitle),
                          Paragraph(edate,  s_edate)]],
                        colWidths=['72%','28%'])
            row.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                                     ('LEFTPADDING',(0,0),(-1,-1),0),
                                     ('RIGHTPADDING',(0,0),(-1,-1),0)]))
            block = [row, Paragraph(esub, s_esub)]
            if edesc:
                block.append(Paragraph(edesc, s_body))
            block.append(Spacer(1, 6))
            story.append(KeepTogether(block))

    # Summary
    if cv.summary:
        section('PROFILE', [('', '', '', cv.summary)])

    # Experience
    if experiences:
        exp_data = []
        for e in experiences:
            exp_data.append((
                f'<b>{e.position}</b>',
                f'{e.company}' + (f' · {e.company_location}' if e.company_location else '') +
                f' · <i>{e.get_employment_type_display()}</i>',
                f'{e.start_date.strftime("%b %Y")} — {e.end_display}',
                e.description or '',
            ))
        section('EXPERIENCE', exp_data)

    # Education
    if educations:
        edu_data = []
        for e in educations:
            deg = e.get_degree_display() + (f' — {e.field_of_study}' if e.field_of_study else '')
            sub = e.institution + (f' · {e.institution_location}' if e.institution_location else '')
            if e.grade: sub += f' · {e.grade}'
            edu_data.append((
                f'<b>{deg}</b>', sub,
                f'{e.start_date.strftime("%b %Y")} — {e.end_display}',
                e.description or '',
            ))
        section('EDUCATION', edu_data)

    # Skills / Languages / Interests — 3 columns
    cols = []
    if skills:
        col = [Paragraph('SKILLS', s_sec),
               HRFlowable(width='100%', thickness=0.5, color=light, spaceAfter=4)]
        for sk in skills:
            col.append(Paragraph(f'• {sk.name}', s_skill))
        cols.append(col)
    if languages:
        col = [Paragraph('LANGUAGES', s_sec),
               HRFlowable(width='100%', thickness=0.5, color=light, spaceAfter=4)]
        for lg in languages:
            col.append(Paragraph(f'{lg.name}  <font size="7" color="#6b7280">{lg.get_level_display()}</font>', s_skill))
        cols.append(col)
    if interests:
        col = [Paragraph('INTERESTS', s_sec),
               HRFlowable(width='100%', thickness=0.5, color=light, spaceAfter=4)]
        for it in interests:
            col.append(Paragraph(f'• {it.name}', s_skill))
        cols.append(col)
    if cols:
        while len(cols) < 3:
            cols.append([Spacer(1,1)])
        cw = W / 3
        tbl = Table([cols], colWidths=[cw]*3)
        tbl.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                                  ('LEFTPADDING',(0,0),(-1,-1),0),
                                  ('RIGHTPADDING',(0,0),(-1,-1),8)]))
        story.append(tbl)

    doc.build(story)


# ═══════════════════════════════════════════════════════════════════════════════
#  MINIMAL TEMPLATE  (accent left border, clean single column)
# ═══════════════════════════════════════════════════════════════════════════════

def build_minimal(cv, experiences, educations, skills, languages, interests, buffer):
    primary   = hex_col(cv.primary_color,   '#1a1a2e')
    secondary = hex_col(cv.secondary_color, '#e63946')
    dark      = colors.HexColor('#374151')
    muted     = colors.HexColor('#6b7280')
    light     = colors.HexColor('#e5e7eb')

    ACCENT_BAR = 4  # px left border width
    LM = 2.2*cm
    RM = 2*cm
    TM = 2*cm
    BM = 2*cm

    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=LM, rightMargin=RM,
                            topMargin=TM,  bottomMargin=BM)
    W = doc.width

    s_name   = ParagraphStyle('MiName', fontSize=24, fontName='Helvetica-Bold',
                               textColor=primary, spaceAfter=3, leading=28)
    s_role   = ParagraphStyle('MiRole', fontSize=11, fontName='Helvetica',
                               textColor=secondary, spaceAfter=4)
    s_cont   = ParagraphStyle('MiCont', fontSize=8, fontName='Helvetica',
                               textColor=muted, spaceAfter=6)
    s_sec    = ParagraphStyle('MiSec',  fontSize=7.5, fontName='Helvetica-Bold',
                               textColor=secondary, spaceBefore=14, spaceAfter=4,
                               letterSpacing=1.8)
    s_etitle = ParagraphStyle('MiET',  fontSize=10, fontName='Helvetica-Bold',
                               textColor=primary, spaceAfter=1)
    s_esub   = ParagraphStyle('MiES',  fontSize=8.5, fontName='Helvetica-Oblique',
                               textColor=muted, spaceAfter=2)
    s_edate  = ParagraphStyle('MiED',  fontSize=8, fontName='Helvetica',
                               textColor=secondary, alignment=TA_RIGHT)
    s_body   = ParagraphStyle('MiBd',  fontSize=9, fontName='Helvetica',
                               textColor=dark, leading=14, spaceAfter=4)
    s_skill  = ParagraphStyle('MiSk',  fontSize=8.5, fontName='Helvetica',
                               textColor=dark, spaceAfter=2)

    story = []

    # Header
    story.append(Paragraph(cv.full_name or cv.title, s_name))
    if cv.job_title:
        story.append(Paragraph(cv.job_title, s_role))

    parts = []
    if cv.email:   parts.append(cv.email)
    if cv.phone:   parts.append(cv.phone)
    if cv.city:    parts.append(cv.city + (f', {cv.country}' if cv.country else ''))
    if cv.linkedin: parts.append(cv.linkedin)
    if parts:
        story.append(Paragraph('  ·  '.join(parts), s_cont))

    story.append(HRFlowable(width='100%', thickness=0.8,
                            color=light, spaceAfter=4, spaceBefore=2))

    def section(title, entries):
        story.append(Paragraph(title, s_sec))
        story.append(HRFlowable(width='100%', thickness=0.5,
                                color=light, spaceAfter=5))
        for (etitle, esub, edate, edesc) in entries:
            row = Table([[Paragraph(etitle, s_etitle),
                          Paragraph(edate,  s_edate)]],
                        colWidths=['70%','30%'])
            row.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                                     ('LEFTPADDING',(0,0),(-1,-1),0),
                                     ('RIGHTPADDING',(0,0),(-1,-1),0)]))
            block = [row]
            if esub:
                block.append(Paragraph(esub, s_esub))
            if edesc:
                block.append(Paragraph(edesc, s_body))
            block.append(Spacer(1, 5))
            story.append(KeepTogether(block))

    if cv.summary:
        section('PROFILE', [('', '', '', cv.summary)])

    if experiences:
        exp_data = []
        for e in experiences:
            exp_data.append((
                f'<b>{e.position}</b>',
                f'{e.company}' + (f' · {e.company_location}' if e.company_location else ''),
                f'{e.start_date.strftime("%b %Y")} — {e.end_display}',
                e.description or '',
            ))
        section('EXPERIENCE', exp_data)

    if educations:
        edu_data = []
        for e in educations:
            deg = e.get_degree_display() + (f' — {e.field_of_study}' if e.field_of_study else '')
            sub = e.institution + (f' · {e.institution_location}' if e.institution_location else '')
            edu_data.append((f'<b>{deg}</b>', sub,
                             f'{e.start_date.strftime("%b %Y")} — {e.end_display}',
                             e.description or ''))
        section('EDUCATION', edu_data)

    # Bottom 3-col
    cols = []
    if skills:
        col = [Paragraph('SKILLS', s_sec),
               HRFlowable(width='100%', thickness=0.5, color=light, spaceAfter=4)]
        for sk in skills:
            col.append(Paragraph(f'• {sk.name}', s_skill))
        cols.append(col)
    if languages:
        col = [Paragraph('LANGUAGES', s_sec),
               HRFlowable(width='100%', thickness=0.5, color=light, spaceAfter=4)]
        for lg in languages:
            col.append(Paragraph(f'{lg.name}  <font size="7" color="#6b7280">{lg.get_level_display()}</font>', s_skill))
        cols.append(col)
    if interests:
        col = [Paragraph('INTERESTS', s_sec),
               HRFlowable(width='100%', thickness=0.5, color=light, spaceAfter=4)]
        for it in interests:
            col.append(Paragraph(f'• {it.name}', s_skill))
        cols.append(col)
    if cols:
        while len(cols) < 3:
            cols.append([Spacer(1,1)])
        cw = W / 3
        tbl = Table([cols], colWidths=[cw]*3)
        tbl.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                                  ('LEFTPADDING',(0,0),(-1,-1),0),
                                  ('RIGHTPADDING',(0,0),(-1,-1),8)]))
        story.append(tbl)

    def draw_accent_bar(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(secondary)
        canvas.rect(0, 0, ACCENT_BAR, A4[1], stroke=0, fill=1)
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_accent_bar, onLaterPages=draw_accent_bar)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN EXPORT VIEW
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def export_pdf(request, pk):
    cv = get_object_or_404(CV, pk=pk, user=request.user)

    experiences = list(cv.experiences.all())
    educations  = list(cv.educations.all())
    skills      = list(cv.skills.all())
    languages   = list(cv.languages.all())
    interests   = list(cv.interests.all())

    buffer = io.BytesIO()

    template = cv.template or 'modern'

    if template == 'classic':
        build_classic(cv, experiences, educations, skills, languages, interests, buffer)
    elif template == 'minimal':
        build_minimal(cv, experiences, educations, skills, languages, interests, buffer)
    else:
        build_modern(cv, experiences, educations, skills, languages, interests, buffer)

    buffer.seek(0)
    filename = f"{(cv.full_name or cv.title or 'CV').replace(' ', '_')}_CV.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response