import pandas as pd
import json
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Step 1: Load session data
with open("timetable.json") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# Step 2: Define hourly slots and days
time_slots = [f"{h:02d}:00-{h+1:02d}:00" for h in range(7, 20)]  # 07:00–20:00
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Step 3: Convert 'Time' to hour-based slot
df["Time"] = pd.to_datetime(df["Time"], format="%H:%M")
df["Hour_Slot"] = df["Time"].dt.strftime("%H:00") + "-" + (df["Time"] + pd.Timedelta(hours=1)).dt.strftime("%H:00")

# Step 4: Initialize group-wise timetables
group_routines = defaultdict(pd.DataFrame)

for group_id, group_df in df.groupby("Group_ID"):
    timetable = pd.DataFrame(index=time_slots, columns=days)
    timetable[:] = ""  # Initialize all cells

    for _, row in group_df.iterrows():
        slot = row["Hour_Slot"]
        day = row["Day"]
        if day not in days:
            continue
        value = f"{row['Course_Name']}"  # Add instructor/room if needed
        timetable.at[slot, day] = value

    group_routines[group_id] = timetable

# Step 5: Export all timetables to a single PDF
pdf_file = "group_timetables.pdf"
with PdfPages(pdf_file) as pdf:
    for group_id, table in group_routines.items():
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.axis('off')
        ax.set_title(f"Routine for {group_id}", fontsize=16, weight='bold', pad=20)

        # Create the table
        tbl = ax.table(cellText=table.values,
                       rowLabels=table.index,
                       colLabels=table.columns,
                       cellLoc='center',
                       loc='center')

        tbl.auto_set_font_size(False)
        tbl.set_fontsize(8)
        tbl.scale(1.2, 1.2)

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

print(f"✅ PDF saved as '{pdf_file}'")
