"""
YatriQ — Engineering Monograph Presentation Deck Generator.
Generates a 7-slide publication-grade technical presentation
tailored specifically for PowerPoint, Google Slides, and Keynote.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def build_yatriq_pptx(output_path="YatriQ_Engineering_Monograph.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Executive & Engineering Palette
    C_BG_DARK       = RGBColor(11, 15, 25)       # #0B0F19 Deep Obsidian
    C_CARD_BG       = RGBColor(18, 25, 42)       # #12192A Slate Navy Card
    C_CARD_BORDER   = RGBColor(34, 48, 77)       # #22304D Card Stroke
    C_CYAN          = RGBColor(6, 182, 212)      # #06B6D4 Tech Cyan
    C_AMBER         = RGBColor(245, 158, 11)     # #F59E0B Warning / Highlighting
    C_EMERALD       = RGBColor(16, 185, 129)     # #10B981 Calm Verified Emerald
    C_BLUE          = RGBColor(59, 130, 246)     # #3B82F6 Primary Transit Blue
    C_WHITE         = RGBColor(248, 250, 252)    # #F8FAFC High-Contrast White
    C_MUTED         = RGBColor(148, 163, 184)    # #94A3B8 Technical Muted Slate
    C_CODE_BG       = RGBColor(6, 9, 16)         # #060910 Formula Black
    C_HIGHLIGHT     = RGBColor(253, 224, 71)     # #FDE047 Soft Gold

    def apply_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = C_BG_DARK
        bg.line.color.rgb = C_BG_DARK
        return bg

    def add_page_header(slide, page_num, chapter_roman, chapter_title, subtext):
        # Top Header Container
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(0.95))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p_ch = tf.paragraphs[0]
        p_ch.text = f"CHAPTER {chapter_roman} // TECHNICAL MONOGRAPH // YATRIQ TRANSIT INTELLIGENCE"
        p_ch.font.size = Pt(9.5)
        p_ch.font.bold = True
        p_ch.font.color.rgb = C_CYAN

        p_title = tf.add_paragraph()
        p_title.text = chapter_title
        p_title.font.size = Pt(21)
        p_title.font.bold = True
        p_title.font.color.rgb = C_WHITE

        p_sub = tf.add_paragraph()
        p_sub.text = subtext
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = C_MUTED

        # Page Number Badge
        pb = slide.shapes.add_textbox(Inches(10.8), Inches(0.4), Inches(1.733), Inches(0.4))
        ptf = pb.text_frame
        ptf.margin_right = ptf.margin_top = 0
        pp = ptf.paragraphs[0]
        pp.text = f"PAGE {page_num:02d} / 07"
        pp.alignment = PP_ALIGN.RIGHT
        pp.font.size = Pt(10.5)
        pp.font.bold = True
        pp.font.color.rgb = C_AMBER

        # Accent Rule
        rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.4), Inches(11.733), Inches(0.02))
        rule.fill.solid()
        rule.fill.fore_color.rgb = C_CARD_BORDER
        rule.line.color.rgb = C_CARD_BORDER

    def add_box(slide, left, top, width, height, title="", border_color=C_CARD_BORDER, fill_color=C_CARD_BG):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.2)
        if title:
            tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.12), width - Inches(0.4), Inches(0.35))
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_top = 0
            p = tf.paragraphs[0]
            p.text = title.upper()
            p.font.size = Pt(10)
            p.font.bold = True
            p.font.color.rgb = C_CYAN
        return shape

    # =========================================================================
    # SLIDE 1: FRONTISPIECE & TITLE TREATISE
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    apply_bg(s1)

    # Double Border Treatise Frame
    outer = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.45), Inches(12.333), Inches(6.6))
    outer.fill.solid()
    outer.fill.fore_color.rgb = RGBColor(14, 20, 34)
    outer.line.color.rgb = C_CYAN
    outer.line.width = Pt(1.5)

    inner = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.65), Inches(0.6), Inches(12.033), Inches(6.3))
    inner.fill.solid()
    inner.fill.fore_color.rgb = RGBColor(12, 17, 28)
    inner.line.color.rgb = C_CARD_BORDER
    inner.line.width = Pt(0.8)

    # Monograph Title Block
    tbox = s1.shapes.add_textbox(Inches(1.2), Inches(1.05), Inches(10.9), Inches(3.2))
    ttf = tbox.text_frame
    ttf.word_wrap = True

    p = ttf.paragraphs[0]
    p.text = "AUTONOMOUS TRANSIT MONOGRAPH // VOLUME I // 2026 EDITION"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_CYAN

    p = ttf.add_paragraph()
    p.text = "YatriQ"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = C_WHITE

    p = ttf.add_paragraph()
    p.text = "The Authoritative Transit Truth Layer & 3D Transit Corridor Progression Engine"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = C_AMBER

    p = ttf.add_paragraph()
    p.text = 'Core Operating Axiom: "Know Your Bus Before It Arrives"'
    p.font.size = Pt(13)
    p.font.italic = True
    p.font.color.rgb = C_MUTED

    # 3 Pillar Spec Blocks
    col_w = Inches(3.45)
    gap = Inches(0.35)
    left_base = Inches(1.2)
    top_base = Inches(4.35)
    card_h = Inches(2.2)

    # Pillar 1
    add_box(s1, left_base, top_base, col_w, card_h, "01. Operational Mandate", C_CYAN)
    tb1 = s1.shapes.add_textbox(left_base + Inches(0.2), top_base + Inches(0.48), col_w - Inches(0.4), Inches(1.5))
    f1 = tb1.text_frame
    f1.word_wrap = True
    p = f1.paragraphs[0]
    p.text = "Eradicating commuter crowd anxiety, 'ghost buses', and erratic arrival forecasts across dense Indian metropolitan bus networks (DTC, BMTC, BEST, UPSRTC)."
    p.font.size = Pt(9.5)
    p.font.color.rgb = C_WHITE

    # Pillar 2
    add_box(s1, left_base + col_w + gap, top_base, col_w, card_h, "02. Core Architecture", C_AMBER)
    tb2 = s1.shapes.add_textbox(left_base + col_w + gap + Inches(0.2), top_base + Inches(0.48), col_w - Inches(0.4), Inches(1.5))
    f2 = tb2.text_frame
    f2.word_wrap = True
    p = f2.paragraphs[0]
    p.text = "TRACK (Kalman & Map Matching) -> ESTIMATE (Onboard Edge-AI Computer Vision) -> PREDICT (Gradient Boosted Regressors) -> INFORM (Calm Commute UX)."
    p.font.size = Pt(9.5)
    p.font.color.rgb = C_WHITE

    # Pillar 3
    add_box(s1, left_base + (col_w + gap)*2, top_base, col_w, card_h, "03. Demonstration Corridor", C_EMERALD)
    tb3 = s1.shapes.add_textbox(left_base + (col_w + gap)*2 + Inches(0.2), top_base + Inches(0.48), col_w - Inches(0.4), Inches(1.5))
    f3 = tb3.text_frame
    f3.word_wrap = True
    p = f3.paragraphs[0]
    p.text = "Anand Vihar <-> Modipuram Rapid Transit Corridor (~58.2 km, 21 Verified Rapid Transit Stations, Full Monotonic Simulation & Real-World Geometries)."
    p.font.size = Pt(9.5)
    p.font.color.rgb = C_WHITE

    # =========================================================================
    # SLIDE 2: CHAPTER 1 - CYBER-PHYSICAL DILEMMA & AXIOMS
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    apply_bg(s2)
    add_page_header(s2, 2, "I", "The Physical-Cyber Transit Dilemma & System Axioms", "Why Legacy Fleet Trackers Fail and the TRACK -> ESTIMATE -> PREDICT -> INFORM Solution")

    # Left Card: 4 Failure Modes
    add_box(s2, Inches(0.8), Inches(1.65), Inches(5.6), Inches(5.25), "01. Four Failure Modes of Legacy Fleet Tracking", C_CARD_BORDER)
    tb_l = s2.shapes.add_textbox(Inches(1.0), Inches(2.15), Inches(5.2), Inches(4.6))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True

    failures = [
        ("1. Ghost Buses & Static ETA Collapse", "Timetable interpolations fail in mixed traffic. Commuters wait for stranded, cancelled, or deadheading vehicles that never arrive."),
        ("2. Commuter Crowd Anxiety & Door Mobbing", "Zero prior visibility into onboard passenger density causes desperate boarding stampedes while trailing, near-empty feeder buses pass unnoticed."),
        ("3. Black-Box Data Fabrication", "Conventional apps present raw ML predictions as live GPS fixes without disclosing source authenticity, confidence score, or observation age."),
        ("4. Cellular Dead-Zone Freezes", "Highway flyovers and underpasses create 4G/5G dropouts, dropping network polling, freezing vehicle blips, and failing commuter updates.")
    ]
    for i, (head, desc) in enumerate(failures):
        p_h = tf_l.paragraphs[0] if i == 0 else tf_l.add_paragraph()
        p_h.text = head
        p_h.font.size = Pt(10.5)
        p_h.font.bold = True
        p_h.font.color.rgb = C_AMBER

        p_d = tf_l.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9)
        p_d.font.color.rgb = C_MUTED
        if i < len(failures) - 1:
            p_sp = tf_l.add_paragraph()
            p_sp.text = ""
            p_sp.font.size = Pt(3)

    # Right Card: The 4 Remediation Stages
    add_box(s2, Inches(6.8), Inches(1.65), Inches(5.733), Inches(5.25), "02. The 4-Stage Remediation Engine", C_CYAN)
    tb_r = s2.shapes.add_textbox(Inches(7.0), Inches(2.15), Inches(5.333), Inches(4.6))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    stages = [
        ("STAGE 1: TRACK (Geospatial Kinematics)", "Continuous GPS telemetry ingestion. Enforces monotonic ordering, tolerates jitter via 55m cross-track snapping, and rejects stale/out-of-order pings."),
        ("STAGE 2: ESTIMATE (Onboard Edge Computer Vision)", "Runs locally on vehicle hardware (Jetson / Pi 4). Estimates passenger density via pixel contours & 3-stage temporal hysteresis without uploading faces or video."),
        ("STAGE 3: PREDICT (Hybrid Gradient Regressors)", "Forecasts dynamic segment travel times, dwell times, and downstream passenger boarding deltas using historical corridor traffic patterns."),
        ("STAGE 4: INFORM (Actionable Calm Commute UX)", "Presents commuters with clear FASTEST vs MOST COMFORTABLE decision cards, humanized crowd indicators, and transparent Data Provenance badges.")
    ]
    for i, (stg, dsc) in enumerate(stages):
        p_s = tf_r.paragraphs[0] if i == 0 else tf_r.add_paragraph()
        p_s.text = stg
        p_s.font.size = Pt(10.5)
        p_s.font.bold = True
        p_s.font.color.rgb = C_CYAN

        p_sd = tf_r.add_paragraph()
        p_sd.text = dsc
        p_sd.font.size = Pt(9)
        p_sd.font.color.rgb = C_WHITE
        if i < len(stages) - 1:
            p_sp = tf_r.add_paragraph()
            p_sp.text = ""
            p_sp.font.size = Pt(3)

    # =========================================================================
    # SLIDE 3: CHAPTER 2 - TRANSIT TRUTH LAYER
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    apply_bg(s3)
    add_page_header(s3, 3, "II", "The Authoritative Transit Truth Engine", "Monotonic Timestamp Sequencing, Conflict Arbitration & Strict Provenance Hierarchy")

    # Invariants Box Across Full Width
    add_box(s3, Inches(0.8), Inches(1.65), Inches(11.733), Inches(1.5), "Mathematical Invariants of the Truth Engine", C_CYAN)
    tb_inv = s3.shapes.add_textbox(Inches(1.0), Inches(2.05), Inches(11.3), Inches(1.0))
    tf_inv = tb_inv.text_frame
    tf_inv.word_wrap = True

    p = tf_inv.paragraphs[0]
    p.text = "INVARIANT I: Monotonic Device Time (t_device^(k) > t_device^(k-1)) -> Replayed out-of-order packets from blackspots are safely archived but NEVER overwrite live state.\nINVARIANT II: Sensor Primacy Rule -> Fresh physical observations (<30s) always take precedence over ML inferences; predictions never overwrite sensors.\nINVARIANT III: Idempotent Deduplication -> Telemetry ingestion applies composite hash keys {device_id, monotonic_seq, t_device} to eliminate duplicate packets."
    p.font.size = Pt(9.5)
    p.font.color.rgb = C_WHITE

    # Left: Location Truth Hierarchy
    add_box(s3, Inches(0.8), Inches(3.35), Inches(5.7), Inches(3.55), "Location Authority Hierarchy", C_EMERALD)
    tb_lh = s3.shapes.add_textbox(Inches(1.0), Inches(3.8), Inches(5.3), Inches(2.9))
    tf_lh = tb_lh.text_frame
    tf_lh.word_wrap = True

    loc_tiers = [
        ("Priority 1: Fresh Official GPS (<30s)", "State: LIVE | Confidence: 95-100% | Source: Direct transit authority ITS feed"),
        ("Priority 2: Fresh Edge Bus GPS (<30s)", "State: LIVE | Confidence: 85-95% | Source: Onboard IoT telemetry unit"),
        ("Priority 3: Recent Observation (30s-60s)", "State: OBSERVED | Confidence: 70-85% | Source: Cached recent position"),
        ("Priority 4: Stale Position (60s-300s)", "State: STALE | Flagged clearly on UI with reassuring 'Updating Soon' notice"),
        ("Priority 5: Deadhead / Disconnected (>300s)", "State: UNAVAILABLE | Vehicle marked unavailable to avoid ghost trips")
    ]
    for i, (tier, detail) in enumerate(loc_tiers):
        p_t = tf_lh.paragraphs[0] if i == 0 else tf_lh.add_paragraph()
        p_t.text = tier
        p_t.font.size = Pt(9.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_EMERALD

        p_td = tf_lh.add_paragraph()
        p_td.text = detail
        p_td.font.size = Pt(8.5)
        p_td.font.color.rgb = C_MUTED

    # Right: Crowd Density Hierarchy
    add_box(s3, Inches(6.8), Inches(3.35), Inches(5.733), Inches(3.55), "Crowd Density Authority Hierarchy", C_AMBER)
    tb_ch = s3.shapes.add_textbox(Inches(7.0), Inches(3.8), Inches(5.333), Inches(2.9))
    tf_ch = tb_ch.text_frame
    tf_ch.word_wrap = True

    crowd_tiers = [
        ("Tier 1: Live Edge Camera (<60s)", "State: LIVE ONBOARD | Confidence: 90-98% | Onboard OpenCV contour analysis"),
        ("Tier 2: Onboard Hardware Sensor (<60s)", "State: LIVE SENSOR | Confidence: 85-92% | Optical / Weight sensors"),
        ("Tier 3: Machine Learning Model", "State: SMART ESTIMATE | Confidence: 70-85% | Gradient Boosted Classifier"),
        ("Tier 4: Historical Baseline Table", "State: TYPICAL PATTERN | Confidence: 50-70% | Time-of-day stop averages"),
        ("Tier 5: Fallback / Unknown", "State: UNKNOWN | Confidence: 0% | Marked unverified to commuters")
    ]
    for i, (tier, detail) in enumerate(crowd_tiers):
        p_c = tf_ch.paragraphs[0] if i == 0 else tf_ch.add_paragraph()
        p_c.text = tier
        p_c.font.size = Pt(9.5)
        p_c.font.bold = True
        p_c.font.color.rgb = C_AMBER

        p_cd = tf_ch.add_paragraph()
        p_cd.text = detail
        p_cd.font.size = Pt(8.5)
        p_cd.font.color.rgb = C_MUTED

    # =========================================================================
    # SLIDE 4: CHAPTER 3 - EDGE-AI VISION & OFFLINE RESILIENCE
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    apply_bg(s4)
    add_page_header(s4, 4, "III", "Edge-AI Vision & Offline Resilience Engineering", "Privacy-Preserving Onboard Computer Vision and SQLite WAL Disconnection Tolerance")

    # Left: Computer Vision Pipeline & Hysteresis
    add_box(s4, Inches(0.8), Inches(1.65), Inches(5.7), Inches(5.25), "01. Onboard Computer Vision & Anti-Flicker", C_CYAN)
    tb_cv = s4.shapes.add_textbox(Inches(1.0), Inches(2.15), Inches(5.3), Inches(4.6))
    tf_cv = tb_cv.text_frame
    tf_cv.word_wrap = True

    cv_points = [
        ("1. Zero-Cloud Video Transmission", "Raw video frames NEVER leave the vehicle. All processing runs locally on Raspberry Pi 4 / Jetson Nano, guaranteeing 100% commuter privacy under Indian DPDP regulations."),
        ("2. Contour Pixel Density Metric", "Frames undergo Gaussian blur -> background subtraction -> contour bounding box area estimation to compute cabin occupancy ratio without face recognition."),
        ("3. 3-Point Temporal Hysteresis Filter", "Raw camera outputs fluctuate with passenger movement. A 3-window filter prevents UI label thrashing:\n  O_t = mode(c_{t-2}, c_{t-1}, c_t)\nOnly shifts category when confirmed across multiple consecutive sample windows."),
        ("4. Calm Humanized Density Labels", "  PLENTY OF SEATS (0-35% occupancy, all seated)\n  SEATS FILLING (36-70% occupancy, light aisle)\n  FEW SEATS LEFT (71-95% occupancy, dense aisle)\n  STANDING ROOM ONLY (>95% crush load)")
    ]
    for i, (h, d) in enumerate(cv_points):
        p_h = tf_cv.paragraphs[0] if i == 0 else tf_cv.add_paragraph()
        p_h.text = h
        p_h.font.size = Pt(10)
        p_h.font.bold = True
        p_h.font.color.rgb = C_CYAN

        p_d = tf_cv.add_paragraph()
        p_d.text = d
        p_d.font.size = Pt(8.5)
        p_d.font.color.rgb = C_WHITE
        if i < len(cv_points) - 1:
            p_s = tf_cv.add_paragraph()
            p_s.text = ""
            p_s.font.size = Pt(2.5)

    # Right: Offline Resilience Buffer
    add_box(s4, Inches(6.8), Inches(1.65), Inches(5.733), Inches(5.25), "02. SQLite WAL Offline Buffer Mechanics", C_AMBER)
    tb_buf = s4.shapes.add_textbox(Inches(7.0), Inches(2.15), Inches(5.333), Inches(4.6))
    tf_buf = tb_buf.text_frame
    tf_buf.word_wrap = True

    buf_points = [
        ("The Cellular Blackspot Challenge", "Buses traversing expressways, rural stretches, and underpasses routinely lose 4G/5G connectivity. Typical systems drop telemetry, creating phantom stalls on dispatch screens."),
        ("Edge SQLite WAL Local Storage", "During outages, the onboard daemon writes every GPS coordinate and crowd estimate to a local SQLite database configured with Write-Ahead Logging (WAL) for microsecond writes."),
        ("Atomic Multi-Record Replay", "When connectivity is restored, the agent pushes batches with explicit device_timestamp and server_received_timestamp to /api/v1/devices/buffer-sync."),
        ("Historical Audit Protection", "The backend preserves replayed pings for ML training but NEVER overrides current live vehicle positions with stale historical pings.")
    ]
    for i, (h, d) in enumerate(buf_points):
        p_h = tf_buf.paragraphs[0] if i == 0 else tf_buf.add_paragraph()
        p_h.text = h
        p_h.font.size = Pt(10)
        p_h.font.bold = True
        p_h.font.color.rgb = C_AMBER

        p_d = tf_buf.add_paragraph()
        p_d.text = d
        p_d.font.size = Pt(8.5)
        p_d.font.color.rgb = C_WHITE
        if i < len(buf_points) - 1:
            p_s = tf_buf.add_paragraph()
            p_s.text = ""
            p_s.font.size = Pt(2.5)

    # =========================================================================
    # SLIDE 5: CHAPTER 4 - SPATIAL CORRIDOR PROGRESSION
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    apply_bg(s5)
    add_page_header(s5, 5, "IV", "Spatial Kinematics & 3D Transit Corridor Mechanics", "The Anand Vihar <-> Modipuram Corridor (58.2 km, 21 Rapid Transit Stations)")

    # Spatial Formulas Box Across Top
    add_box(s5, Inches(0.8), Inches(1.65), Inches(11.733), Inches(1.75), "Geospatial Navigation & Projection Calculus", C_CYAN)
    tb_geo = s5.shapes.add_textbox(Inches(1.0), Inches(2.05), Inches(11.3), Inches(1.2))
    tf_geo = tb_geo.text_frame
    tf_geo.word_wrap = True

    p = tf_geo.paragraphs[0]
    p.text = "1. Haversine Distance: d = 2R * arcsin(sqrt(sin^2(dlat/2) + cos(lat1)*cos(lat2)*sin^2(dlng/2)))  |  Earth Radius R = 6,371 km\n2. Cross-Track Error (XTE): XTE = R * arcsin(sin(d_13/R) * sin(bearing_13 - bearing_12))  |  Road Snapping: epsilon <= 55m\n3. Corridor Progression Index: P = (Distance along polyline from Terminal A) / (Total Length L_total) in [0.000, 1.000]\n4. 3D Isometric Projection: (x_iso, y_iso) = ((x - y) * cos(30 deg), (x + y) * sin(30 deg) - z)"
    p.font.size = Pt(9.5)
    p.font.color.rgb = C_WHITE

    # Bottom Left: 21-Station Anand Vihar -> Modipuram Corridor
    add_box(s5, Inches(0.8), Inches(3.6), Inches(7.0), Inches(3.3), "21-Station Rapid Transit Corridor Sequence", C_CARD_BORDER)
    tb_seq = s5.shapes.add_textbox(Inches(1.0), Inches(4.05), Inches(6.6), Inches(2.7))
    tf_seq = tb_seq.text_frame
    tf_seq.word_wrap = True

    p = tf_seq.paragraphs[0]
    p.text = "TERMINAL 01: Anand Vihar ISBT (Lat 28.6469, Lng 77.3161) [Inter-State Hub / Metro / RRTS]\n  -> 02: Sahibabad -> 03: Ghaziabad Terminal -> 04: Guldhar -> 05: Duhai Interchange\n  -> 06: Duhai Depot -> 07: Muradnagar -> 08: Modi Nagar South -> 09: Modi Nagar North\n  -> 10: Meerut South Interchange -> 11: Partapur -> 12: Rithani -> 13: Shatabdi Nagar\n  -> 14: Brahmpuri -> 15: Meerut Central Terminal -> 16: Bhaisali Terminal -> 17: Begumpul\n  -> 18: MES Colony -> 19: Daurli -> 20: Meerut North Bypass\nTERMINAL 21: Modipuram Depot (Lat 29.0880, Lng 77.7180) [Northern Terminal]"
    p.font.size = Pt(8.5)
    p.font.color.rgb = C_MUTED

    # Bottom Right: 3D Visualization Engine Architecture
    add_box(s5, Inches(8.0), Inches(3.6), Inches(4.533), Inches(3.3), "3D Corridor Renderer Architecture", C_AMBER)
    tb_rend = s5.shapes.add_textbox(Inches(8.2), Inches(4.05), Inches(4.133), Inches(2.7))
    tf_rend = tb_rend.text_frame
    tf_rend.word_wrap = True

    p = tf_rend.paragraphs[0]
    p.text = "- HTML5 Canvas 3D Engine: Renders an isometric elevated transit track with real-time station nodes, track rails, and animated vehicle blips.\n- Interpolated Motion: Smooth 60 FPS transitions between discrete GPS telemetry updates.\n- Dynamic Heatmaps: Track segments glow based on passenger density (Green = Plenty of Seats, Amber = Moderate, Red = Full).\n- Interactive Station Focus: Clicking any station expands local liveboard arrivals and dwell queues."
    p.font.size = Pt(8.8)
    p.font.color.rgb = C_WHITE

    # =========================================================================
    # SLIDE 6: CHAPTER 5 - COMMUTER DECISION ENGINE & CALM UX
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    apply_bg(s6)
    add_page_header(s6, 6, "V", "Commuter Decision Engine & Calm UX Architecture", "Eliminating Commuter Anxiety with Hero Recommendations, Humanized Density & 2m Alerts")

    # Left Card: Dual-Path Recommendation Engine
    add_box(s6, Inches(0.8), Inches(1.65), Inches(5.7), Inches(5.25), "01. Active Corridor Load Balancing", C_CYAN)
    tb_rec = s6.shapes.add_textbox(Inches(1.0), Inches(2.15), Inches(5.3), Inches(4.6))
    tf_rec = tb_rec.text_frame
    tf_rec.word_wrap = True

    rec_points = [
        ("The 'Bunched Bus' Paradox in India", "Two buses on Route 101 frequently arrive 4 minutes apart. The first bus is severely overcrowded (98%), while the trailing bus is nearly empty (30%). Commuters instinctively mob the first bus, aggravating delays."),
        ("THE 'FASTEST' RECOMMENDATION", "Awarded to the vehicle with minimum ETA to the commuter's stop, provided crowd level does not exceed safety thresholds.\n  * Target Commuter: Time-critical passengers, daily office rush."),
        ("THE 'MOST COMFORTABLE' RECOMMENDATION", "Identifies a trailing vehicle arriving within a delta window (Delta t <= 10 min) with LOW or MEDIUM crowd occupancy.\n  * Target Commuter: Elderly, families, long-distance commuters desiring guaranteed seats."),
        ("Empirical Transit Impact", "Simulations demonstrate an 18-24% reduction in peak-door boarding delay by voluntarily distributing passengers across consecutive buses.")
    ]
    for i, (h, d) in enumerate(rec_points):
        p_h = tf_rec.paragraphs[0] if i == 0 else tf_rec.add_paragraph()
        p_h.text = h
        p_h.font.size = Pt(10)
        p_h.font.bold = True
        p_h.font.color.rgb = C_CYAN

        p_d = tf_rec.add_paragraph()
        p_d.text = d
        p_d.font.size = Pt(8.5)
        p_d.font.color.rgb = C_WHITE
        if i < len(rec_points) - 1:
            p_s = tf_rec.add_paragraph()
            p_s.text = ""
            p_s.font.size = Pt(2.5)

    # Right Card: Calm Commute UX Features
    add_box(s6, Inches(6.8), Inches(1.65), Inches(5.733), Inches(5.25), "02. Calm Commute UX Innovations", C_EMERALD)
    tb_calm = s6.shapes.add_textbox(Inches(7.0), Inches(2.15), Inches(5.333), Inches(4.6))
    tf_calm = tb_calm.text_frame
    tf_calm.word_wrap = True

    calm_points = [
        ("Hero 'Best Choice For You' Card", "Eliminates decision fatigue. A single prominent card at the top tells the passenger exactly which bus to take, arrival minutes, and seating comfort in under 2 seconds."),
        ("Friendly Humanized Crowd Indicators", "Replaces stressful percentages with clear human labels:\n  * 🟢 Plenty of Seats | 🟡 Seats Filling | 🟠 Few Seats Left | 🔵 Standing Room Only"),
        ("Peace-of-Mind 'Remind 2m Before' Ping", "Commuters click a friendly bell button to get an alert 2 minutes before the bus arrives, allowing them to pocket their phone and listen to music without staring at screens."),
        ("Offline Schedule & Route Reassurance", "Reassuring status badge informs commuters that corridor routes and schedules are saved offline so connectivity blackouts never cause uncertainty.")
    ]
    for i, (h, d) in enumerate(calm_points):
        p_h = tf_calm.paragraphs[0] if i == 0 else tf_calm.add_paragraph()
        p_h.text = h
        p_h.font.size = Pt(10)
        p_h.font.bold = True
        p_h.font.color.rgb = C_EMERALD

        p_d = tf_calm.add_paragraph()
        p_d.text = d
        p_d.font.size = Pt(8.5)
        p_d.font.color.rgb = C_WHITE
        if i < len(calm_points) - 1:
            p_s = tf_calm.add_paragraph()
            p_s.text = ""
            p_s.font.size = Pt(2.5)

    # =========================================================================
    # SLIDE 7: CHAPTER 6 - EMPIRICAL VERIFICATION & SPECIFICATIONS
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    apply_bg(s7)
    add_page_header(s7, 7, "VI", "Empirical Verification, Fault Tolerance & Bill of Materials", "13 Automated Verification Suites, ML Drift Circuit Breakers & Full System Specifications")

    # Left: Test Matrix & Chaos Verification
    add_box(s7, Inches(0.8), Inches(1.65), Inches(5.7), Inches(5.25), "01. Verification Test Matrix & Fault Tolerance", C_EMERALD)
    tb_tst = s7.shapes.add_textbox(Inches(1.0), Inches(2.15), Inches(5.3), Inches(4.6))
    tf_tst = tb_tst.text_frame
    tf_tst.word_wrap = True

    tests = [
        ("test_truth_engine.py", "Validates monotonic ordering, deduplication, and single authoritative state."),
        ("test_edge_offline.py", "Simulates 15-minute cellular blackout, verifies SQLite buffering & replay sync."),
        ("test_crowd.py & test_geo.py", "Verifies 3-point hysteresis thresholds, Haversine accuracy, and 55m XTE bounds."),
        ("test_model_drift_and_baseline.py", "Validates ML circuit breaker: falls back to baseline if error exceeds 3 sigma."),
        ("test_provenance_and_failures.py", "Rigorous chaos tests: dead camera feeds, out-of-order pings, clock skew tolerances.")
    ]
    for i, (tname, tdesc) in enumerate(tests):
        p_t = tf_tst.paragraphs[0] if i == 0 else tf_tst.add_paragraph()
        p_t.text = tname
        p_t.font.size = Pt(9.5)
        p_t.font.bold = True
        p_t.font.color.rgb = C_EMERALD

        p_td = tf_tst.add_paragraph()
        p_td.text = tdesc
        p_td.font.size = Pt(8.5)
        p_td.font.color.rgb = C_MUTED
        if i < len(tests) - 1:
            p_s = tf_tst.add_paragraph()
            p_s.text = ""
            p_s.font.size = Pt(2)

    # Right: Architectural Bill of Materials
    add_box(s7, Inches(6.8), Inches(1.65), Inches(5.733), Inches(5.25), "02. Architectural Bill of Materials (BOM)", C_CYAN)
    tb_spec = s7.shapes.add_textbox(Inches(7.0), Inches(2.15), Inches(5.333), Inches(4.6))
    tf_spec = tb_spec.text_frame
    tf_spec.word_wrap = True

    specs = [
        ("Core Cloud Backend", "Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2.0, PostgreSQL & SQLite"),
        ("Edge Compute Tier", "Raspberry Pi 4 (4GB) / NVIDIA Jetson Nano, RTSP IP Cabin Cameras"),
        ("Computer Vision Engine", "OpenCV 4.9 headless, local contour background subtraction, zero cloud video"),
        ("Machine Learning Models", "Scikit-learn 1.4 (RandomForest Classifier, GradientBoosting Regressor)"),
        ("Web Command Radar", "React 18, TypeScript, HTML5 Canvas 3D Isometric Engine, Vite"),
        ("Passenger Mobile App", "Flutter 3.x, Riverpod, Dio, WebSockets, English/Hindi localization"),
        ("DevOps & Messaging", "Docker Compose, Mosquitto MQTT, TimescaleDB / SQLite WAL, Pytest")
    ]
    for i, (sname, sdesc) in enumerate(specs):
        p_s = tf_spec.paragraphs[0] if i == 0 else tf_spec.add_paragraph()
        p_s.text = f"{sname}:"
        p_s.font.size = Pt(9.5)
        p_s.font.bold = True
        p_s.font.color.rgb = C_CYAN

        p_sd = tf_spec.add_paragraph()
        p_sd.text = f"  {sdesc}"
        p_sd.font.size = Pt(8.5)
        p_sd.font.color.rgb = C_WHITE
        if i < len(specs) - 1:
            p_sp = tf_spec.add_paragraph()
            p_sp.text = ""
            p_sp.font.size = Pt(2)

    prs.save(output_path)
    print(f"Successfully built high-craft YatriQ PPTX presentation: {output_path}")

if __name__ == "__main__":
    build_yatriq_pptx()
