import os
import json
from typing import List, Dict
from datetime import datetime
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.cm as cm
import matplotlib.colors as mcolors

from src.entities.decoded_session import CourseSession
from src.encoder.quantum_time_system import QuantumTimeSystem

# Config values (used internally only)
from config.calendar_config import (
    EXCAL_QUANTUM_MINUTES,
    EXCAL_START_HOUR,
    EXCAL_END_HOUR,
    EXCAL_DEFAULT_OUTPUT_PDF,
)


def _get_time_schedule_format(
    qts: QuantumTimeSystem, quanta: List[int]
) -> Dict[str, List[Dict[str, str]]]:
    """Converts a list of quanta into the required schedule format.

    Args:
        qts (QuantumTimeSystem): The quantum time system instance for conversion.
        quanta (List[int]): List of time quanta to be converted.

    Returns:
        Dict[str, List[Dict[str, str]]]: Schedule in the format:
            {
                "Monday": [
                    {"start": "09:00", "end": "12:00"},
                    {"start": "14:00", "end": "17:00"}
                ]
            }
    """
    if not quanta:
        return {}
    return qts.decode_schedule(set(quanta))


def _save_schedule_as_json(
    schedule: List[CourseSession], output_path: str, qts: QuantumTimeSystem
) -> str:
    """Saves a list of CourseSession objects as a JSON file.

    Args:
        schedule (List[CourseSession]): Decoded sessions from final GA output.
        output_path (str): Output directory to store the JSON file.
        qts (QuantumTimeSystem): Quantum time system for converting quanta to day/time.

    Returns:
        str: Full path to the saved JSON file.

    Note:
        Creates the output directory if it doesn't exist.
        The JSON file will be named 'schedule.json'.
    """
    filename = "schedule.json"
    full_path = os.path.join(output_path, filename)
    os.makedirs(output_path, exist_ok=True)

    result = []
    for session in schedule:
        time_schedule = _get_time_schedule_format(qts, session.session_quanta)
        result.append(
            {
                "course_id": session.course_id,
                "instructor_id": session.instructor_id,
                "group_id": session.group_ids[0] if session.group_ids else None,
                "room_id": session.room_id,
                "time": time_schedule,
            }
        )

    with open(full_path, "w") as f:
        json.dump(result, f, indent=2)

    return full_path


def _save_json_schedule_as_pdf(
    json_path: str,
    output_pdf_path: str,
    quantum_minutes: int,
    start_hour: int,
    end_hour: int,
):
    """Converts a structured JSON schedule into a calendar-style PDF.

    Creates a multi-page PDF with one calendar page per group. Sessions are
    color-coded by course and merged when they are consecutive.

    Args:
        json_path (str): Path to the input JSON schedule file.
        output_pdf_path (str): Path where the PDF will be saved.
        quantum_minutes (int): Time granularity in minutes for merging sessions.
        start_hour (int): Earliest hour shown on the calendar (e.g., 7 for 07:00).
        end_hour (int): Latest hour shown on the calendar (e.g., 20 for 20:00).

    Note:
        - Uses matplotlib to generate calendar grids
        - Each course gets a unique color from the tab20 colormap
        - Sessions are automatically merged if they are consecutive
        - PDF contains one page per student group
    """

    DAYS = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]
    DAY_IDX = {day: i for i, day in enumerate(DAYS)}
    TIME_FORMAT = "%H:%M"

    def to_float(time_str):
        """Convert time string to float hours.

        Args:
            time_str (str): Time in HH:MM format.

        Returns:
            float: Time as decimal hours (e.g., 14:30 -> 14.5).
        """
        t = datetime.strptime(time_str, TIME_FORMAT)
        return t.hour + t.minute / 60.0

    def merge_sessions(sessions):
        """Merge consecutive sessions with the same label and day.

        Args:
            sessions (List[Dict]): List of session dictionaries.

        Returns:
            List[Dict]: Merged sessions list.
        """
        merged = []
        sessions.sort(key=lambda x: (x["day"], x["start"]))
        i = 0
        while i < len(sessions):
            s = sessions[i]
            j = i + 1
            while j < len(sessions):
                n = sessions[j]
                if (
                    n["label"] == s["label"]
                    and n["day"] == s["day"]
                    and abs(n["start"] - s["end"]) < (quantum_minutes / 60.0) + 1e-6
                ):
                    s["end"] = n["end"]
                    j += 1
                else:
                    break
            merged.append(s)
            i = j
        return merged

    def plot_schedule(sessions, group_name, pdf, color_map):
        """Plot a weekly schedule for a specific group.

        Args:
            sessions (List[Dict]): Sessions for this group.
            group_name (str): Name of the student group.
            pdf (PdfPages): PDF writer object.
            color_map (Dict[str, str]): Mapping of course IDs to hex colors.
        """
        sessions = merge_sessions(sessions)

        fig, ax = plt.subplots(figsize=(14, 10))
        ax.set_title(f"Routine for {group_name}", fontsize=16, pad=20)
        ax.set_xlim(0, len(DAYS))
        ax.set_ylim(end_hour, start_hour)
        ax.set_xticks(range(len(DAYS)))
        ax.set_xticklabels(DAYS, fontsize=10)
        ax.set_yticks(range(start_hour, end_hour + 1))
        ax.set_yticklabels([f"{h:02d}:00" for h in range(start_hour, end_hour + 1)])
        ax.grid(True, which="both", linestyle="--", linewidth=0.5)

        for session in sessions:
            day = session["day"]
            if day not in DAY_IDX:
                continue
            x = DAY_IDX[day]
            y = session["start"]
            height = session["end"] - session["start"]
            label = session["label"]
            color = color_map.get(label, "#CCCCCC")

            rect = plt.Rectangle(
                (x + 0.05, y),
                0.9,
                height,
                edgecolor="black",
                facecolor=color,
                linewidth=1.2,
            )
            ax.add_patch(rect)
            ax.text(
                x + 0.5,
                y + height / 2,
                label,
                ha="center",
                va="center",
                fontsize=8,
                wrap=True,
            )

        plt.tight_layout()
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    # Load JSON
    with open(json_path) as f:
        data = json.load(f)

    group_sessions = defaultdict(list)
    course_ids = set()

    for entry in data:
        group = entry["group_id"]
        course = entry["course_id"]
        course_ids.add(course)
        for day, times in entry["time"].items():
            for s in times:
                start = to_float(s["start"])
                end = to_float(s["end"])
                group_sessions[group].append(
                    {"day": day, "start": start, "end": end, "label": course}
                )

    # Assign unique color to each course
    course_list = sorted(course_ids)
    cmap = cm.get_cmap("tab20", len(course_list))
    color_map = {
        course: mcolors.to_hex(cmap(i)) for i, course in enumerate(course_list)
    }

    # Save PDF
    with PdfPages(output_pdf_path) as pdf:
        for group_id, sessions in group_sessions.items():
            plot_schedule(sessions, group_id, pdf, color_map)

    print(f"✅ PDF saved as '{output_pdf_path}'")


def export_everything(
    schedule: List[CourseSession],
    output_path: str,
    qts: QuantumTimeSystem,
):
    """Exports schedule as both JSON and PDF to a single directory.

    This is the main export function that combines JSON and PDF generation.
    It uses configuration values from calendar_config.py for PDF settings.

    Args:
        schedule (List[CourseSession]): Decoded sessions from genetic algorithm output.
        output_path (str): Output directory path. Will be created if it doesn't exist.
        qts (QuantumTimeSystem): Quantum time system instance for time conversion.

    Example:
        >>> from src.exporter.exporter import export_everything
        >>> export_everything(final_schedule, "./output", qts_instance)
        ✅ Schedule exported successfully!
        📄 JSON: ./output/schedule.json
        📊 PDF:  ./output/calendar_colored_merged.pdf

    Note:
        - Creates output directory if it doesn't exist
        - JSON file is always named 'schedule.json'
        - PDF filename comes from EXCAL_DEFAULT_OUTPUT_PDF config
        - PDF settings (hours, quantum minutes) come from calendar_config.py
    """
    os.makedirs(output_path, exist_ok=True)

    # Save JSON
    json_path = _save_schedule_as_json(schedule, output_path, qts)

    # Save PDF
    pdf_path = os.path.join(output_path, EXCAL_DEFAULT_OUTPUT_PDF)
    _save_json_schedule_as_pdf(
        json_path=json_path,
        output_pdf_path=pdf_path,
        quantum_minutes=EXCAL_QUANTUM_MINUTES,
        start_hour=EXCAL_START_HOUR,
        end_hour=EXCAL_END_HOUR,
    )

    print("✅ Schedule exported successfully!")
    print(f"📄 JSON: {json_path}")
    print(f"📊 PDF:  {pdf_path}")
