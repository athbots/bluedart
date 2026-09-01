"""
Demo Video Generator for Smart Transit Intelligence System.
Assembles high-resolution walkthrough frames into an MP4 video with smooth crossfades and contextual title cards.
"""

import os
import cv2
import numpy as np

def generate_video():
    base_dir = r"C:\Users\aniru\.gemini\antigravity-ide\brain\3536386c-9d67-49bf-bd62-57c9c12b564b"
    output_mp4_name1 = r"c:\Users\aniru\bluedart\first demo.mp4"
    output_mp4_name2 = r"c:\Users\aniru\bluedart\first_demo.mp4"

    slides = [
        {
            "file": "tab1_command_center_1788241132165.png",
            "title": "Smart Transit Intelligence System — System Command Center",
            "subtitle": "Real-time Fleet KPIs • Active Anand Vihar - Modipuram Corridor • Truth Engine Status",
            "duration_sec": 3.5,
        },
        {
            "file": "tab2_fleet_radar_1788241141705.png",
            "title": "3D Transit Corridor — Anand Vihar to Modipuram Express",
            "subtitle": "21 Sequential Stops • Perspective Depth Rail • Elevated Nodes • Glowing Active Segment",
            "duration_sec": 4.0,
        },
        {
            "file": "follow_bus_mode_1788241149351.png",
            "title": "Follow Bus Camera Mode — Dynamic View Tracking",
            "subtitle": "Vehicle 101 Tracking • Real-time Headlight Cone • Progress Percentage & Live Telemetry",
            "duration_sec": 3.5,
        },
        {
            "file": "stop_details_drawer_check_1788241160259.png",
            "title": "Stop Details HUD Drawer & Target Stop Selection",
            "subtitle": "Distance (14.2 km) • Dynamic Arrival ETA (41 min) • Downstream AI Crowd Prediction",
            "duration_sec": 3.5,
        },
        {
            "file": "2d_radar_map_view_1788241184296.png",
            "title": "Alternative 2D GIS Radar Corridor View",
            "subtitle": "Seamless toggle between 3D Isometric View and 2D GIS Radar Matrix",
            "duration_sec": 3.0,
        },
        {
            "file": "meerut_south_liveboard_1788241211878.png",
            "title": "Stop Liveboard — Meerut South (STOP_10)",
            "subtitle": "Decision Engine: [FASTEST] vs [MOST COMFORTABLE] • Truth Provenance Hierarchy",
            "duration_sec": 4.5,
        },
        {
            "file": "tab5_eta_analytics_1788241220654.png",
            "title": "Model Validation — Baseline vs ML Regressor",
            "subtitle": "Empirical Verification: Baseline (108s MAE) vs ML (64s MAE) -> +40.7% Error Reduction",
            "duration_sec": 4.0,
        },
        {
            "file": "tab6_fleet_simulator_1788241232949.png",
            "title": "Fleet Simulator & Resilience Scenarios",
            "subtitle": "Deterministic Multi-Bus Physics Simulation • 11 Interactive Fault Scenarios (A to K)",
            "duration_sec": 3.5,
        },
        {
            "file": "scenario_f_executed_1788241246029.png",
            "title": "Scenario F Execution Confirmation",
            "subtitle": "3 Buses Approaching Meerut South: Bus 115-C (Fastest), Bus 108-B (Most Comfortable)",
            "duration_sec": 3.5,
        },
        {
            "file": "tab2_after_scenario_f_1788241255851.png",
            "title": "Real-time Telemetry & Live 3D Progression",
            "subtitle": "Continuous Monotonic Updates • Zero Latency Drift • Truth-Resolved Navigation",
            "duration_sec": 4.0,
        },
    ]

    target_w, target_h = 1920, 1080
    fps = 30
    temp_avi = os.path.join(base_dir, "temp_demo.avi")
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    out = cv2.VideoWriter(temp_avi, fourcc, fps, (target_w, target_h))

    def create_frame(img_path, title, subtitle):
        mat = cv2.imread(img_path)
        if mat is None:
            canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
            canvas[:] = (15, 23, 42)
            return canvas

        h, w, _ = mat.shape
        scale = min((target_h - 100) / h, target_w / w)
        nw, nh = int(w * scale), int(h * scale)
        resized = cv2.resize(mat, (nw, nh), interpolation=cv2.INTER_CUBIC)

        canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        canvas[:] = (11, 19, 43)  # Dark navy background

        # Place image
        y_off = 30 + (target_h - 110 - nh) // 2
        x_off = (target_w - nw) // 2
        canvas[y_off:y_off+nh, x_off:x_off+nw] = resized

        # Top Banner Overlay
        overlay = canvas.copy()
        cv2.rectangle(overlay, (0, 0), (target_w, 75), (7, 11, 20), -1)
        # Bottom Banner Overlay
        cv2.rectangle(overlay, (0, target_h - 60), (target_w, target_h), (7, 11, 20), -1)
        cv2.addWeighted(overlay, 0.88, canvas, 0.12, 0, canvas)

        # Title text
        cv2.putText(canvas, title, (40, 46), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 242, 254), 2, cv2.LINE_AA)
        # Subtitle text
        cv2.putText(canvas, subtitle, (40, target_h - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (203, 213, 225), 1, cv2.LINE_AA)
        # Watermark
        cv2.putText(canvas, "SMART TRANSIT INTELLIGENCE MVP", (target_w - 420, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (148, 163, 184), 1, cv2.LINE_AA)

        return canvas

    frames = []
    for item in slides:
        p = os.path.join(base_dir, item["file"])
        if os.path.exists(p):
            f = create_frame(p, item["title"], item["subtitle"])
            frames.append((f, int(item["duration_sec"] * fps)))

    # Write video with crossfades
    fade_frames = 15
    for i, (f, count) in enumerate(frames):
        # Main hold frames
        for _ in range(count - fade_frames):
            out.write(f)

        # Crossfade to next slide
        if i < len(frames) - 1:
            next_f, _ = frames[i + 1]
            for alpha_step in range(fade_frames):
                alpha = alpha_step / float(fade_frames)
                blended = cv2.addWeighted(f, 1.0 - alpha, next_f, alpha, 0)
                out.write(blended)
        else:
            for _ in range(fade_frames):
                out.write(f)

    out.release()
    print("Raw video rendered to:", temp_avi)

    # Transcode to H.264 MP4 using ffmpeg
    for out_target in [output_mp4_name1, output_mp4_name2]:
        cmd = f'ffmpeg -y -i "{temp_avi}" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart "{out_target}"'
        print("Executing:", cmd)
        os.system(cmd)

    print("Demo video successfully generated at:")
    print("1.", output_mp4_name1)
    print("2.", output_mp4_name2)

if __name__ == "__main__":
    generate_video()
