"""
Generates a 7-slide Engineering Monograph PowerPoint presentation
for the Smart Transit Intelligence System.
"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_engineering_deck(output_path="Smart_Transit_Intelligence_Engineering_Monograph.pptx"):
    prs = Presentation()
    # 16:9 widescreen layout
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6] # Blank layout

    # Color Palette: Technical Engineering Treatise / Blueprint
    C_NAVY_DARK = RGBColor(11, 19, 43)       # #0B132B Deep Technical Navy
    C_SLATE_BG  = RGBColor(15, 23, 42)       # #0F172A Slate 900
    C_CARD_BG   = RGBColor(30, 41, 59)       # #1E293B Slate 800
    C_CARD_BORDER=RGBColor(51, 65, 85)       # #334155 Slate 700
    C_CYAN      = RGBColor(6, 182, 212)      # #06B6D4 Tech Cyan
    C_AMBER     = RGBColor(245, 158, 11)     # #F59E0B Engineering Amber
    C_EMERALD   = RGBColor(16, 185, 129)     # #10B981 Verified Emerald
    C_WHITE     = RGBColor(248, 250, 252)    # #F8FAFC Crisp White
    C_MUTED     = RGBColor(148, 163, 184)    # #94A3B8 Technical Muted Grey
    C_CODE_BG   = RGBColor(2, 6, 23)         # #020617 Terminal Black

    def set_slide_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = C_SLATE_BG
        bg.line.color.rgb = C_SLATE_BG
        return bg

    def add_header(slide, page_num, chapter_num, title, subtitle):
        # Top banner with chapter and technical metadata
        header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(0.9))
        tf = header_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p_ch = tf.paragraphs[0]
        p_ch.text = f"CHAPTER {chapter_num:02d} // TECHNICAL MONOGRAPH // TRANSIT INTELLIGENCE SYSTEMS"
        p_ch.font.size = Pt(9.5)
        p_ch.font.bold = True
        p_ch.font.color.rgb = C_CYAN
        
        p_title = tf.add_paragraph()
        p_title.text = title
        p_title.font.size = Pt(20)
        p_title.font.bold = True
        p_title.font.color.rgb = C_WHITE

        p_sub = tf.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = C_MUTED

        # Page index on top right
        pg_box = slide.shapes.add_textbox(Inches(11.0), Inches(0.4), Inches(1.5), Inches(0.5))
        ptf = pg_box.text_frame
        ptf.margin_right = ptf.margin_top = 0
        pp = ptf.paragraphs[0]
        pp.text = f"PAGE {page_num:02d} / 07"
        pp.alignment = PP_ALIGN.RIGHT
        pp.font.size = Pt(10)
        pp.font.bold = True
        pp.font.color.rgb = C_AMBER

        # Thin rule under header
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.35), Inches(11.733), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = C_CARD_BORDER
        line.line.color.rgb = C_CARD_BORDER

    def add_card(slide, left, top, width, height, title, border_color=C_CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD_BG
        card.line.color.rgb = border_color
        card.line.width = Pt(1.2)
        
        if title:
            tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), width - Inches(0.4), Inches(0.35))
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_top = 0
            p = tf.paragraphs[0]
            p.text = title.upper()
            p.font.size = Pt(10.5)
            p.font.bold = True
            p.font.color.rgb = C_CYAN
        return card

    # ==========================================
    # SLIDE 1: FRONTISPIECE / COVER
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)

    # Monograph Frame Border
    frame = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.5), Inches(12.333), Inches(6.5))
    frame.fill.solid()
    frame.fill.fore_color.rgb = C_NAVY_DARK
    frame.line.color.rgb = C_CYAN
    frame.line.width = Pt(1.5)

    # Title box
    tbox = s1.shapes.add_textbox(Inches(1.2), Inches(1.1), Inches(10.9), Inches(3.2))
    ttf = tbox.text_frame
    ttf.word_wrap = True
    
    p0 = ttf.paragraphs[0]
    p0.text = "ENGINEERING TREATISE & MONOGRAPH // VOL. 1"
    p0.font.size = Pt(12)
    p0.font.bold = True
    p0.font.color.rgb = C_CYAN

    p1 = ttf.add_paragraph()
    p1.text = "YatriQ"
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = C_WHITE

    p2 = ttf.add_paragraph()
    p2.text = "The Authoritative Transit Truth Layer & 3D Corridor Progression Engine"
    p2.font.size = Pt(17)
    p2.font.bold = True
    p2.font.color.rgb = C_AMBER

    p3 = ttf.add_paragraph()
    p3.text = 'Core Operating Axiom: "Know Your Bus Before It Arrives."'
    p3.font.size = Pt(13)
    p3.font.italic = True
    p3.font.color.rgb = C_MUTED

    # 3 Spec Columns at bottom of Slide 1
    col_w = Inches(3.4)
    gap = Inches(0.35)
    
    # Col 1: System Purpose
    add_card(s1, Inches(1.2), Inches(4.3), col_w, Inches(2.2), "01. Engineering Mandate", C_CYAN)
    tb1 = s1.shapes.add_textbox(Inches(1.35), Inches(4.8), col_w - Inches(0.3), Inches(1.6))
    f1 = tb1.text_frame
    f1.word_wrap = True
    p = f1.paragraphs[0]
    p.text = "Eliminating transit uncertainty, 'ghost buses', and crowd anxiety across high-density Indian urban & regional bus networks (DTC, BMTC, BEST, UPSRTC)."
    p.font.size = Pt(10)
    p.font.color.rgb = C_WHITE

    # Col 2: Architectural Thesis
    add_card(s1, Inches(1.2) + col_w + gap, Inches(4.3), col_w, Inches(2.2), "02. Core Architecture", C_AMBER)
    tb2 = s1.shapes.add_textbox(Inches(1.35) + col_w + gap, Inches(4.8), col_w - Inches(0.3), Inches(1.6))
    f2 = tb2.text_frame
    f2.word_wrap = True
    p = f2.paragraphs[0]
    p.text = "TRACK (Kalman/Map-Match) -> ESTIMATE (Edge-AI OpenCV Density) -> PREDICT (Gradient Boosted ETAs) -> INFORM (Authoritative Decision UX)."
    p.font.size = Pt(10)
    p.font.color.rgb = C_WHITE

    # Col 3: Reference Corridor
    add_card(s1, Inches(1.2) + (col_w + gap)*2, Inches(4.3), col_w, Inches(2.2), "03. Demonstration Corridor", C_EMERALD)
    tb3 = s1.shapes.add_textbox(Inches(1.35) + (col_w + gap)*2, Inches(4.8), col_w - Inches(0.3), Inches(1.6))
    f3 = tb3.text_frame
    f3.word_wrap = True
    p = f3.paragraphs[0]
    p.text = "Anand Vihar <-> Modipuram Corridor (58.2 km, 21 Rapid Transit Stations, Full Monotonic Simulation & Real-World Geometries)."
    p.font.size = Pt(10)
    p.font.color.rgb = C_WHITE

    # ==========================================
    # SLIDE 2: CHAPTER 1 - PROBLEM CONTEXT & AXIOMS
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, 2, 1, "The Physical-Cyber Transit Dilemma & System Axioms", "Why Traditional Fleet Tracking Fails and the TRACK -> ESTIMATE -> PREDICT -> INFORM Pipeline")

    # Left: 4 Fundamental Failures of Current Systems
    add_card(s2, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3), "Deficiencies in Legacy Transit Tracking Systems", C_CARD_BORDER)
    tb = s2.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.2), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True

    failures = [
        ("1. Ghost Buses & ETA Mirage", "Static schedule interpolations fail in mixed Indian traffic. Commuters wait for buses that are already stranded, deadheading, or cancelled."),
        ("2. Commuter Crowd Anxiety", "Passengers face zero prior visibility into onboard crowding. Overcrowded buses are mobbed while near-empty trailing buses run unnoticed."),
        ("3. Black-Box Data Fabrication", "Conventional apps present raw ML predictions as real-time GPS fixes without source transparency, timestamps, or confidence metrics."),
        ("4. Cellular Dead-Zone Dropouts", "Arterial highway underpasses and rural sections trigger 4G/5G signal drops, freezing vehicle radars and dropping commuter updates.")
    ]
    for i, (head, desc) in enumerate(failures):
        p_h = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p_h.text = head
        p_h.font.size = Pt(11)
        p_h.font.bold = True
        p_h.font.color.rgb = C_AMBER
        
        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = C_MUTED
        if i < len(failures) - 1:
            p_space = tf.add_paragraph()
            p_space.text = ""
            p_space.font.size = Pt(4)

    # Right: The 4-Stage Operating Pipeline
    add_card(s2, Inches(6.7), Inches(1.6), Inches(5.8), Inches(5.3), "The 4-Stage Remediation Pipeline", C_CYAN)
    tb_r = s2.shapes.add_textbox(Inches(6.9), Inches(2.1), Inches(5.4), Inches(4.6))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    stages = [
        ("STAGE 1: TRACK (Geospatial Position)", "Continuous high-precision GPS telemetry. Rejects stale coordinates (>60s) and out-of-order pings. Snaps coordinates within 55m cross-track error bounds."),
        ("STAGE 2: ESTIMATE (Onboard Privacy-Preserving Vision)", "Edge-AI computer vision runs directly on bus cabin hardware. Estimates occupancy via pixel density & 3-stage temporal hysteresis without uploading faces or video."),
        ("STAGE 3: PREDICT (Hybrid Gradient Regressors)", "Forecasts dynamic segment travel times, dwell durations, and downstream crowd changes based on corridor traffic patterns and temporal baselines."),
        ("STAGE 4: INFORM (Actionable Commuter Decision UX)", "Presents clean decision cards: FASTEST vs. MOST COMFORTABLE with transparent Data Provenance (LIVE CCTV, PREDICTED, HISTORICAL).")
    ]
    for i, (stg, dsc) in enumerate(stages):
        p_s = tf_r.paragraphs[0] if i == 0 else tf_r.add_paragraph()
        p_s.text = stg
        p_s.font.size = Pt(11)
        p_s.font.bold = True
        p_s.font.color.rgb = C_CYAN
        
        p_sd = tf_r.add_paragraph()
        p_sd.text = dsc
        p_sd.font.size = Pt(9.5)
        p_sd.font.color.rgb = C_WHITE
        if i < len(stages) - 1:
            p_space = tf_r.add_paragraph()
            p_space.text = ""
            p_space.font.size = Pt(4)

    # ==========================================
    # SLIDE 3: CHAPTER 2 - TRANSIT TRUTH LAYER
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, 3, 2, "The Authoritative Transit Truth Engine", "Monotonic Timestamp Sequencing, Conflict Arbitration & Strict Provenance Hierarchy")

    # 3 Horizontal Panels
    # Top Panel: System Invariant Formulations
    add_card(s3, Inches(0.8), Inches(1.6), Inches(11.733), Inches(1.5), "Core Mathematical Invariants of the Truth Engine", C_CYAN)
    tb_inv = s3.shapes.add_textbox(Inches(1.0), Inches(2.05), Inches(11.3), Inches(0.9))
    tf_inv = tb_inv.text_frame
    tf_inv.word_wrap = True
    
    p = tf_inv.paragraphs[0]
    p.text = "INVARIANT I: Monotonic Time (t_device^(k) > t_device^(k-1)) - Out-of-order delayed packets are stored for audit but NEVER overwrite active state.\nINVARIANT II: Sensor Primacy - Real-time physical observation ALWAYS supercedes ML inference; ML predictions never overwrite live telemetry.\nINVARIANT III: Idempotent Deduplication - Ingestion uses composite UUIDs & monotonic cache barriers to prevent replay corruption."
    p.font.size = Pt(9.5)
    p.font.color.rgb = C_WHITE

    # Bottom Left: Location Truth Hierarchy
    add_card(s3, Inches(0.8), Inches(3.3), Inches(5.7), Inches(3.6), "Location Authority Hierarchy", C_EMERALD)
    tb_lh = s3.shapes.add_textbox(Inches(1.0), Inches(3.8), Inches(5.3), Inches(2.9))
    tf_lh = tb_lh.text_frame
    tf_lh.word_wrap = True

    loc_tiers = [
        ("Priority 1: Fresh Official GPS (<30s)", "State: LIVE | Confidence: 95-100% | Source: Direct ITS hardware"),
        ("Priority 2: Fresh Edge Bus GPS (<30s)", "State: LIVE | Confidence: 85-95% | Source: Onboard IoT telemetry"),
        ("Priority 3: Recent Observation (30s-60s)", "State: OBSERVED | Confidence: 70-85% | Source: Cached telemetry"),
        ("Priority 4: Stale Position (60s-300s)", "State: STALE | Confidence: 40-60% | Provenance flag: Stale degraded"),
        ("Priority 5: Fallback / Deadhead (>300s)", "State: UNAVAILABLE | UI: Grayed radar blip with alert warning")
    ]
    for i, (tier, detail) in enumerate(loc_tiers):
        p_t = tf_lh.paragraphs[0] if i == 0 else tf_lh.add_paragraph()
        p_t.text = tier
        p_t.font.size = Pt(10)
        p_t.font.bold = True
        p_t.font.color.rgb = C_EMERALD
        p_td = tf_lh.add_paragraph()
        p_td.text = detail
        p_td.font.size = Pt(8.5)
        p_td.font.color.rgb = C_MUTED

    # Bottom Right: Crowd Truth Hierarchy
    add_card(s3, Inches(6.8), Inches(3.3), Inches(5.733), Inches(3.6), "Crowd Density Authority Hierarchy", C_AMBER)
    tb_ch = s3.shapes.add_textbox(Inches(7.0), Inches(3.8), Inches(5.3), Inches(2.9))
    tf_ch = tb_ch.text_frame
    tf_ch.word_wrap = True

    crowd_tiers = [
        ("Tier 1: Live Edge Camera (<60s)", "State: LIVE CCTV | Confidence: 90-98% | Local OpenCV Contour Analysis"),
        ("Tier 2: Onboard Hardware Sensor (<60s)", "State: LIVE SENSOR | Confidence: 85-92% | Optical / Weight telemetry"),
        ("Tier 3: Machine Learning Model", "State: PREDICTED | Confidence: 70-85% | Gradient Boosted Classifier"),
        ("Tier 4: Historical Baseline", "State: HISTORICAL | Confidence: 50-70% | Time-of-day stop averages"),
        ("Tier 5: Fallback / Unknown", "State: UNKNOWN | Confidence: 0% | Marked unverified to commuter")
    ]
    for i, (tier, detail) in enumerate(crowd_tiers):
        p_c = tf_ch.paragraphs[0] if i == 0 else tf_ch.add_paragraph()
        p_c.text = tier
        p_c.font.size = Pt(10)
        p_c.font.bold = True
        p_c.font.color.rgb = C_AMBER
        p_cd = tf_ch.add_paragraph()
        p_cd.text = detail
        p_cd.font.size = Pt(8.5)
        p_cd.font.color.rgb = C_MUTED

    # ==========================================
    # SLIDE 4: CHAPTER 3 - EDGE-AI VISION & RESILIENCE
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, 4, 3, "Edge-AI Computer Vision & Offline Resilience", "Privacy-Preserving On-Vehicle Cabin Analytics and SQLite WAL Disconnection Tolerance")

    # Left: Computer Vision Pipeline & Hysteresis
    add_card(s4, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.3), "Edge Computer Vision & Anti-Flicker Filter", C_CYAN)
    tb_cv = s4.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.3), Inches(4.6))
    tf_cv = tb_cv.text_frame
    tf_cv.word_wrap = True

    cv_points = [
        ("1. Zero-Cloud Video Transmission", "Raw camera streams NEVER leave the bus. Frame processing is executed locally on edge hardware (Jetson / Pi 4), ensuring 100% commuter privacy under DPDP act."),
        ("2. Contour Pixel Density Metric", "Frames are converted to grayscale -> Gaussian blur -> background subtraction -> contour bounding box area estimation to compute cabin occupancy ratio."),
        ("3. 3-Point Temporal Hysteresis Filter", "Raw camera outputs fluctuate with passenger movement. A 3-window temporal filter prevents UI label thrashing:\n  O_t = mode(c_{t-2}, c_{t-1}, c_t)\nOnly changes category if confirmed across multiple consecutive sample windows."),
        ("4. Density Categorization Thresholds", "  LOW: 0-35% occupancy (<21 seated / no standees)\n  MEDIUM: 36-70% occupancy (full seats, light aisle)\n  HIGH: 71-95% occupancy (dense standing)\n  VERY HIGH: >95% (crush load / boarding delayed)")
    ]
    for i, (h, d) in enumerate(cv_points):
        p_h = tf_cv.paragraphs[0] if i == 0 else tf_cv.add_paragraph()
        p_h.text = h
        p_h.font.size = Pt(10.5)
        p_h.font.bold = True
        p_h.font.color.rgb = C_CYAN
        p_d = tf_cv.add_paragraph()
        p_d.text = d
        p_d.font.size = Pt(9)
        p_d.font.color.rgb = C_WHITE
        if i < len(cv_points) - 1:
            p_s = tf_cv.add_paragraph()
            p_s.text = ""
            p_s.font.size = Pt(3)

    # Right: Offline Resilience Buffer Architecture
    add_card(s4, Inches(6.8), Inches(1.6), Inches(5.733), Inches(5.3), "Offline-First SQLite Buffer Mechanics", C_AMBER)
    tb_buf = s4.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.6))
    tf_buf = tb_buf.text_frame
    tf_buf.word_wrap = True

    buf_points = [
        ("The Cellular Blackspot Dilemma", "Buses traversing expressways, rural stretches, and underpasses routinely lose 4G/5G connectivity. Typical systems drop telemetry, creating phantom stalls on dispatch screens."),
        ("Edge SQLite WAL Local Storage", "During outages, the onboard daemon writes every GPS coordinate and crowd estimate to a local SQLite database configured with Write-Ahead Logging (WAL) for microsecond writes."),
        ("Atomic Multi-Record Replay", "When connectivity is restored, the agent pushes batches with explicit device_timestamp and server_received_timestamp to /api/v1/devices/buffer-sync."),
        ("Truth Engine Out-of-Order Ingestion", "The backend inserts buffered data into historical telemetry tables for ML training and model audits, but NEVER overrides current live vehicle positions with stale historical pings.")
    ]
    for i, (h, d) in enumerate(buf_points):
        p_h = tf_buf.paragraphs[0] if i == 0 else tf_buf.add_paragraph()
        p_h.text = h
        p_h.font.size = Pt(10.5)
        p_h.font.bold = True
        p_h.font.color.rgb = C_AMBER
        p_d = tf_buf.add_paragraph()
        p_d.text = d
        p_d.font.size = Pt(9)
        p_d.font.color.rgb = C_WHITE
        if i < len(buf_points) - 1:
            p_s = tf_buf.add_paragraph()
            p_s.text = ""
            p_s.font.size = Pt(3)

    # ==========================================
    # SLIDE 5: CHAPTER 4 - SPATIAL CORRIDOR PROGRESSION
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, 5, 4, "Spatial Kinematics & 3D Transit Corridor Mechanics", "The Anand Vihar <-> Modipuram Corridor (58.2 km, 21 Rapid Transit Stations)")

    # Top: Spatial Equations & Polyline Snapping
    add_card(s5, Inches(0.8), Inches(1.6), Inches(11.733), Inches(1.8), "Geospatial Snapping & Corridor Progression Formulas", C_CYAN)
    tb_geo = s5.shapes.add_textbox(Inches(1.0), Inches(2.05), Inches(11.3), Inches(1.2))
    tf_geo = tb_geo.text_frame
    tf_geo.word_wrap = True

    p = tf_geo.paragraphs[0]
    p.text = "1. Haversine Distance: d = 2R * arcsin(sqrt(sin^2(dlat/2) + cos(lat1)*cos(lat2)*sin^2(dlng/2)))  |  Earth Radius R = 6,371 km\n2. Cross-Track Error (XTE): XTE = R * arcsin(sin(d_13/R) * sin(bearing_13 - bearing_12))  |  Snapping Threshold: epsilon <= 55m\n3. Corridor Progression Index: P = (Distance from Terminal A) / (Total Corridor Length L_total) in [0.000, 1.000]\n4. 3D Isometric Projection: (x_iso, y_iso) = ((x - y) * cos(30 deg), (x + y) * sin(30 deg) - z)"
    p.font.size = Pt(9.5)
    p.font.color.rgb = C_WHITE

    # Bottom Left: 21-Station Anand Vihar -> Modipuram Corridor
    add_card(s5, Inches(0.8), Inches(3.6), Inches(7.0), Inches(3.3), "21-Station Rapid Transit Corridor Sequence", C_CARD_BORDER)
    tb_seq = s5.shapes.add_textbox(Inches(1.0), Inches(4.05), Inches(6.6), Inches(2.7))
    tf_seq = tb_seq.text_frame
    tf_seq.word_wrap = True

    p = tf_seq.paragraphs[0]
    p.text = "TERMINAL 01: Anand Vihar ISBT (Lat 28.6469, Lng 77.3161) [Inter-State Hub / Metro / RRTS]\n  -> 02: Sahibabad -> 03: Ghaziabad Terminal -> 04: Guldhar -> 05: Duhai Interchange\n  -> 06: Duhai Depot -> 07: Muradnagar -> 08: Modi Nagar South -> 09: Modi Nagar North\n  -> 10: Meerut South Interchange -> 11: Partapur -> 12: Rithani -> 13: Shatabdi Nagar\n  -> 14: Brahmpuri -> 15: Meerut Central Terminal -> 16: Bhaisali Terminal -> 17: Begumpul\n  -> 18: MES Colony -> 19: Daurli -> 20: Meerut North Bypass\nTERMINAL 21: Modipuram Depot (Lat 29.0880, Lng 77.7180) [Northern Terminal]"
    p.font.size = Pt(8.5)
    p.font.color.rgb = C_MUTED

    # Bottom Right: 3D Visualization Engine Architecture
    add_card(s5, Inches(8.0), Inches(3.6), Inches(4.533), Inches(3.3), "3D Corridor Renderer Architecture", C_AMBER)
    tb_rend = s5.shapes.add_textbox(Inches(8.2), Inches(4.05), Inches(4.1), Inches(2.7))
    tf_rend = tb_rend.text_frame
    tf_rend.word_wrap = True

    p = tf_rend.paragraphs[0]
    p.text = "- HTML5 Canvas 3D Engine: Renders an isometric elevated transit track with real-time station nodes, track rails, and animated vehicle blips.\n- Interpolated Motion: Smooth 60 FPS transitions between discrete GPS telemetry updates.\n- Dynamic Heatmaps: Track segments glow based on passenger density (Green = Low, Amber = Med, Red = High).\n- Interactive Station Focus: Clicking any station expands local liveboard arrivals and dwell queues."
    p.font.size = Pt(9)
    p.font.color.rgb = C_WHITE

    # ==========================================
    # SLIDE 6: CHAPTER 5 - COMMUTER DECISION ENGINE
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, 6, 5, "Commuter Decision Engine & Transparent UX", "Load-Balancing Commuters via FASTEST vs. COMFORTABLE Recommendations & Provenance Badges")

    # Left: Dual-Path Recommendation Engine
    add_card(s6, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.3), "Dynamic Commuter Recommendation Logic", C_CYAN)
    tb_rec = s6.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.3), Inches(4.6))
    tf_rec = tb_rec.text_frame
    tf_rec.word_wrap = True

    rec_points = [
        ("The 'Bunched Bus' Paradox in India", "Two buses on Route 101 frequently arrive 4 minutes apart. The first bus is severely overcrowded (95%+), while the trailing bus is nearly empty (30%). Commuters instinctively mob the first bus, aggravating delays."),
        ("THE 'FASTEST' RECOMMENDATION", "Awarded to the vehicle with minimum ETA to the commuter's stop, provided crowd level does not exceed safety thresholds.\n  * Badge: FASTEST ARRIVAL\n  * Commuter Profile: Time-critical passengers, daily office rush."),
        ("THE 'MOST COMFORTABLE' RECOMMENDATION", "Identifies a trailing vehicle arriving within a delta window (Delta t <= 10 min) with LOW or MEDIUM crowd occupancy.\n  * Badge: MOST COMFORTABLE (Guaranteed Seat)\n  * Commuter Profile: Elderly, families, long-distance commuters."),
        ("Active Corridor Load Balancing", "Simulations demonstrate an 18-24% reduction in peak-door boarding delay by voluntarily distributing passengers to trailing buses.")
    ]
    for i, (h, d) in enumerate(rec_points):
        p_h = tf_rec.paragraphs[0] if i == 0 else tf_rec.add_paragraph()
        p_h.text = h
        p_h.font.size = Pt(10.5)
        p_h.font.bold = True
        p_h.font.color.rgb = C_CYAN
        p_d = tf_rec.add_paragraph()
        p_d.text = d
        p_d.font.size = Pt(9)
        p_d.font.color.rgb = C_WHITE
        if i < len(rec_points) - 1:
            p_s = tf_rec.add_paragraph()
            p_s.text = ""
            p_s.font.size = Pt(3)

    # Right: Provenance Tagging & Cross-Platform UX
    add_card(s6, Inches(6.8), Inches(1.6), Inches(5.733), Inches(5.3), "Transparent Data Provenance & Client Stack", C_AMBER)
    tb_prv = s6.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.6))
    tf_prv = tb_prv.text_frame
    tf_prv.word_wrap = True

    prv_points = [
        ("Commuter Trust Through Full Provenance", "Every arrival card displays explicit provenance metadata:\n  - LIVE CCTV: Onboard edge camera verified (<60s)\n  - PREDICTED: Machine Learning regressor forecast\n  - HISTORICAL: Deterministic time-of-day fallback\n  - Age tag: 'Updated 14s ago' | Confidence score: 94%"),
        ("Flutter Cross-Platform Mobile Client", "Built with Dart / Flutter Riverpod with bilingual localization:\n  - English & Hindi UI ('अपनी बस को आने से पहले जानें')\n  - Rapid-transit train-style progression line\n  - Offline caching of stop schedules and corridor routes"),
        ("Real-Time WebSocket Ingestion", "Sub-second liveboard updates over binary WebSockets with zero battery-draining HTTP polling.")
    ]
    for i, (h, d) in enumerate(prv_points):
        p_h = tf_prv.paragraphs[0] if i == 0 else tf_prv.add_paragraph()
        p_h.text = h
        p_h.font.size = Pt(10.5)
        p_h.font.bold = True
        p_h.font.color.rgb = C_AMBER
        p_d = tf_prv.add_paragraph()
        p_d.text = d
        p_d.font.size = Pt(9)
        p_d.font.color.rgb = C_WHITE
        if i < len(prv_points) - 1:
            p_s = tf_prv.add_paragraph()
            p_s.text = ""
            p_s.font.size = Pt(3)

    # ==========================================
    # SLIDE 7: CHAPTER 6 - EMPIRICAL VERIFICATION & SPECS
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, 7, 6, "Empirical Verification, Fault Tolerance & Specifications", "13 Automated Verification Suites, ML Drift Guardrails & Technical Architecture Specifications")

    # Left: Automated Testing & Fault Tolerance Matrix
    add_card(s7, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.3), "Verification Test Matrix & Fault Tolerance", C_EMERALD)
    tb_tst = s7.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.3), Inches(4.6))
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
        p_t.font.size = Pt(10)
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

    # Right: Bill of Materials & System Specifications
    add_card(s7, Inches(6.8), Inches(1.6), Inches(5.733), Inches(5.3), "Engineering System Specifications", C_CYAN)
    tb_spec = s7.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.6))
    tf_spec = tb_spec.text_frame
    tf_spec.word_wrap = True

    specs = [
        ("Core Backend", "FastAPI, Python 3.12, Uvicorn, SQLAlchemy 2.0, PostgreSQL / SQLite"),
        ("Edge Compute Tier", "Raspberry Pi 4 (4GB) / NVIDIA Jetson Nano, RTSP IP Cabin Camera"),
        ("Computer Vision", "OpenCV 4.9 headless, local contour background subtractor, zero cloud video"),
        ("Machine Learning", "Scikit-learn 1.4 (RandomForest Classifier, GradientBoosting Regressor)"),
        ("Frontend Web Radar", "React 18, TypeScript, HTML5 Canvas 3D Isometric Engine, Vite"),
        ("Mobile Passenger App", "Flutter 3.x, Riverpod, Dio, WebSockets, English/Hindi localization"),
        ("Deployment & Telemetry", "Docker Compose, Mosquitto MQTT, TimescaleDB / SQLite WAL, Pytest")
    ]
    for i, (sname, sdesc) in enumerate(specs):
        p_s = tf_spec.paragraphs[0] if i == 0 else tf_spec.add_paragraph()
        p_s.text = f"{sname}:"
        p_s.font.size = Pt(10)
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
    print(f"Successfully generated 7-page Engineering Monograph presentation: {output_path}")

if __name__ == "__main__":
    create_engineering_deck()
