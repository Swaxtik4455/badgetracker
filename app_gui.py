import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd

from scrapper import ProfileScraper
from storage import save_run
from analytics import (
    process_results_dataframe, 
    calculate_campaign_health, 
    generate_outreach_templates, 
    TARGET_BADGES
)

# Color Palette Constants
GOOGLE_BLUE = "#1A73E8"
GOOGLE_GREEN = "#0F9D58"
GOOGLE_YELLOW = "#F4B400"
GOOGLE_RED = "#DB4437"
DARK_TEXT = "#202124"
BG_MAIN = "#F8F9FA"
CARD_BG = "#FFFFFF"

# Priority Badge Colors
PRIO_COLOR_MAP = {
    "HIGH (Quick Win)": ("#FEF7E0", "#B06000"),
    "HIGH (Broken / Private)": ("#FCE8E6", "#C5221F"),
    "MEDIUM (Onboarding Needed)": ("#E8F0FE", "#1A73E8"),
    "MEDIUM (Encouragement Needed)": ("#E8F0FE", "#1A73E8"),
    "LOW (Completed)": ("#E6F4EA", "#137333")
}

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB Limit

class SkillTrackDesktopApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚡ SkillTrack — GDG Campaign Tracker")
        self.geometry("1150x750")
        self.minsize(950, 650)
        self.configure(bg=BG_MAIN)

        self.raw_df = None
        self.analysis_df = None
        self.csv_path = None

        self._configure_styles()
        self._build_ui()

    def _configure_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure(".", background=BG_MAIN, font=("Segoe UI", 10))

        self.style.configure("TFrame", background=BG_MAIN)
        self.style.configure("Header.TFrame", background=GOOGLE_BLUE)
        self.style.configure("Card.TFrame", background=CARD_BG, relief="flat", borderwidth=1)
        self.style.configure("TLabelframe", background=CARD_BG, bordercolor="#DADCE0", borderwidth=1, padding=12)
        self.style.configure("TLabelframe.Label", background=CARD_BG, foreground=GOOGLE_BLUE, font=("Segoe UI", 10, "bold"))

        self.style.configure("Primary.TButton", background=GOOGLE_BLUE, foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(14, 7))
        self.style.map("Primary.TButton", background=[("active", "#1557B0"), ("disabled", "#BDC1C6")])

        self.style.configure("Success.TButton", background=GOOGLE_GREEN, foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(14, 7))
        self.style.map("Success.TButton", background=[("active", "#0B8043"), ("disabled", "#BDC1C6")])

        self.style.configure("Secondary.TButton", background="#E8EAED", foreground=DARK_TEXT, font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(12, 6))
        self.style.map("Secondary.TButton", background=[("active", "#D2E3FC")])

        self.style.configure("TNotebook", background=BG_MAIN, borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#E8EAED", foreground=DARK_TEXT, font=("Segoe UI", 10, "bold"), padding=(16, 9))
        self.style.map("TNotebook.Tab", background=[("selected", CARD_BG), ("active", "#D2E3FC")], foreground=[("selected", GOOGLE_BLUE)])

        self.style.configure("Treeview", background=CARD_BG, fieldbackground=CARD_BG, foreground=DARK_TEXT, rowheight=30, font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", background="#E8F0FE", foreground=GOOGLE_BLUE, font=("Segoe UI", 9, "bold"), padding=8)
        self.style.map("Treeview", background=[("selected", "#D2E3FC")], foreground=[("selected", GOOGLE_BLUE)])

        self.style.configure("TProgressbar", thickness=6, troughcolor="#E8EAED", background=GOOGLE_GREEN)

    def _build_ui(self):
        top_bar = ttk.Frame(self, style="Header.TFrame", padding=15)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        title_label = tk.Label(top_bar, text="⚡ SkillTrack", font=("Segoe UI", 18, "bold"), bg=GOOGLE_BLUE, fg="white")
        title_label.pack(side=tk.LEFT, padx=(5, 5))

        subtitle_label = tk.Label(top_bar, text="GDG Campaign Manager", font=("Segoe UI", 10, "italic"), bg=GOOGLE_BLUE, fg="#D2E3FC")
        subtitle_label.pack(side=tk.LEFT, padx=(0, 20))

        self.btn_load_csv = ttk.Button(top_bar, text="📁 Load CSV File", style="Secondary.TButton", command=self.load_csv)
        self.btn_load_csv.pack(side=tk.LEFT, padx=5)

        self.btn_run_verification = ttk.Button(top_bar, text="▶ Run Verification", style="Success.TButton", command=self.run_verification, state=tk.DISABLED)
        self.btn_run_verification.pack(side=tk.LEFT, padx=5)

        self.btn_export_csv = ttk.Button(top_bar, text="📥 Export CSV Report", style="Secondary.TButton", command=self.export_csv, state=tk.DISABLED)
        self.btn_export_csv.pack(side=tk.RIGHT, padx=5)

        self.status_label = tk.Label(top_bar, text="Please load a candidate CSV file to begin.", font=("Segoe UI", 10, "italic"), bg=GOOGLE_BLUE, fg="#E8F0FE")
        self.status_label.pack(side=tk.LEFT, padx=15)

        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, mode='determinate', style="TProgressbar")
        self.progress.pack(fill=tk.X)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.tab_overview = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_overview, text="📊 Summary & Health")

        self.tab_action = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_action, text="🎯 Outreach Priority")

        self.tab_templates = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_templates, text="📢 Broadcast Templates")

        self.tab_gap = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_gap, text="🔍 Badge Gap Analyzer")

        self.tab_full_data = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_full_data, text="📑 Full Data View")

        self._setup_overview_tab()
        self._setup_action_tab()
        self._setup_templates_tab()
        self._setup_gap_tab()
        self._setup_full_data_tab()

    def _setup_overview_tab(self):
        self.health_card = tk.Frame(self.tab_overview, bg=CARD_BG, highlightbackground="#DADCE0", highlightthickness=1, padx=15, pady=12)
        self.health_card.pack(fill=tk.X, pady=(0, 15))

        self.lbl_health_status = tk.Label(
            self.health_card, 
            text="Status: Waiting for profile verification run...", 
            font=("Segoe UI", 11, "bold"),
            bg=CARD_BG,
            fg=GOOGLE_BLUE
        )
        self.lbl_health_status.pack(anchor="w")

        self.metrics_container = tk.Frame(self.tab_overview, bg=BG_MAIN)
        self.metrics_container.pack(fill=tk.X, pady=(0, 15))

        self.card_total = self._create_metric_card(self.metrics_container, "TOTAL PARTICIPANTS", "-", GOOGLE_BLUE)
        self.card_total.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.card_verified = self._create_metric_card(self.metrics_container, "VERIFIED PROFILES", "-", DARK_TEXT)
        self.card_verified.grid(row=0, column=1, padx=10, sticky="ew")

        self.card_completed = self._create_metric_card(self.metrics_container, "COMPLETED (10/10)", "-", GOOGLE_GREEN)
        self.card_completed.grid(row=0, column=2, padx=10, sticky="ew")

        self.card_almost = self._create_metric_card(self.metrics_container, "ALMOST DONE (8-9)", "-", GOOGLE_YELLOW)
        self.card_almost.grid(row=0, column=3, padx=(10, 0), sticky="ew")

        self.metrics_container.grid_columnconfigure(0, weight=1)
        self.metrics_container.grid_columnconfigure(1, weight=1)
        self.metrics_container.grid_columnconfigure(2, weight=1)
        self.metrics_container.grid_columnconfigure(3, weight=1)

    def _create_metric_card(self, parent, title, val_text, accent_color):
        card = tk.Frame(parent, bg=CARD_BG, highlightbackground="#DADCE0", highlightthickness=1, padx=15, pady=12)
        
        lbl_title = tk.Label(card, text=title, font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg="#5F6368")
        lbl_title.pack(anchor="w")

        lbl_val = tk.Label(card, text=val_text, font=("Segoe UI", 18, "bold"), bg=CARD_BG, fg=accent_color)
        lbl_val.pack(anchor="w", pady=(5, 0))
        
        card.lbl_val = lbl_val
        return card

    def _setup_action_tab(self):
        filter_frame = ttk.Frame(self.tab_action)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="Filter Priority Queue: ", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.combo_action_filter = ttk.Combobox(
            filter_frame, 
            values=["All", "HIGH (Quick Win)", "HIGH (Broken / Private)", "MEDIUM (Onboarding Needed)", "MEDIUM (Encouragement Needed)", "LOW (Completed)"],
            state="readonly",
            width=30
        )
        self.combo_action_filter.set("All")
        self.combo_action_filter.pack(side=tk.LEFT, padx=5)
        self.combo_action_filter.bind("<<ComboboxSelected>>", self._filter_action_table)

        self.tree_action = self._create_treeview(
            self.tab_action, 
            columns=("URL", "Priority", "Status", "Badges", "Recommended Action")
        )

    def _setup_templates_tab(self):
        self.txt_templates = tk.Text(
            self.tab_templates, 
            wrap=tk.WORD, 
            font=("Consolas", 10),
            bg="#FFFFFF",
            fg=DARK_TEXT,
            bd=1,
            relief="solid",
            padx=15,
            pady=15
        )
        vsb = ttk.Scrollbar(self.tab_templates, orient="vertical", command=self.txt_templates.yview)
        self.txt_templates.configure(yscrollcommand=vsb.set)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_templates.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _setup_gap_tab(self):
        gap_filter_frame = ttk.Frame(self.tab_gap)
        gap_filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(gap_filter_frame, text="Remaining Badges Filter: ", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.combo_gap_filter = ttk.Combobox(
            gap_filter_frame, 
            values=["All (1-10)", "1 Badge Remaining (9/10)", "2 Badges Remaining (8/10)", "3+ Badges Remaining"],
            state="readonly",
            width=30
        )
        self.combo_gap_filter.set("All (1-10)")
        self.combo_gap_filter.pack(side=tk.LEFT, padx=5)
        self.combo_gap_filter.bind("<<ComboboxSelected>>", self._filter_gap_table)

        self.tree_gap = self._create_treeview(
            self.tab_gap, 
            columns=("URL", "Priority", "Badges Earned", "Badges Remaining", "Campaign Status")
        )

    def _setup_full_data_tab(self):
        self.tree_full = self._create_treeview(
            self.tab_full_data,
            columns=("URL", "Status", "Earned", "Remaining", "Priority", "Category")
        )

    def _create_treeview(self, parent, columns):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=160, anchor="w")

        tree.tag_configure("even", background="#FFFFFF")
        tree.tag_configure("odd", background="#F8F9FA")

        for prio_name, (bg_color, fg_color) in PRIO_COLOR_MAP.items():
            tree.tag_configure(prio_name, background=bg_color, foreground=fg_color)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        return tree

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return

        # Security Check: Extension & File Size
        if not file_path.lower().endswith(".csv"):
            messagebox.showerror("Invalid File", "Only .csv files are supported.")
            return

        if os.path.getsize(file_path) > MAX_FILE_SIZE_BYTES:
            messagebox.showerror("File Too Large", "CSV file size exceeds maximum limit of 5 MB.")
            return

        try:
            df = pd.read_csv(file_path)
            url_col = "Google Skills Profile URL"
            if url_col not in df.columns:
                messagebox.showerror("Invalid CSV", f"Missing required column: '{url_col}'")
                return

            self.raw_df = df
            self.csv_path = file_path
            urls = df[url_col].dropna().unique().tolist()

            self.status_label.config(text=f"Loaded {len(urls)} profile URLs from {os.path.basename(file_path)}")
            self.btn_run_verification.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error Reading CSV", str(e))

    def run_verification(self):
        if self.raw_df is None:
            return

        url_col = "Google Skills Profile URL"
        urls = self.raw_df[url_col].dropna().unique().tolist()
        
        self.progress["value"] = 0
        self.progress["maximum"] = len(urls)
        
        scraper = ProfileScraper(delay_seconds=0.2)
        raw_results = []

        for idx, url in enumerate(urls, start=1):
            self.status_label.config(text=f"Verifying ({idx}/{len(urls)}): {url[:40]}...")
            self.update_idletasks()
            
            res = scraper.fetch_profile(url)
            raw_results.append(res)
            self.progress["value"] = idx

        save_run(raw_results)
        self.analysis_df = process_results_dataframe(raw_results)
        
        self._update_dashboards()
        self.btn_export_csv.config(state=tk.NORMAL)
        self.status_label.config(text="✓ Verification complete! All views updated.")
        messagebox.showinfo("Success", "Profile verification completed successfully!")

    def _update_dashboards(self):
        df = self.analysis_df
        if df is None:
            return

        health = calculate_campaign_health(df)
        self.lbl_health_status.config(text=f"Health Score: {health['health_score']}%  |  {health['health_status']}")

        self.card_total.lbl_val.config(text=str(health['total']))
        self.card_verified.lbl_val.config(text=str(len(df[df['Verification Status'] == 'Verified'])))
        self.card_completed.lbl_val.config(text=str(health['completed']))
        self.card_almost.lbl_val.config(text=str(health['almost']))

        templates = generate_outreach_templates(df)
        self.txt_templates.delete("1.0", tk.END)
        self.txt_templates.insert(tk.END, "=== GDG BROADCAST INTERVENTION TEMPLATES ===\n\n")
        for name, text in templates.items():
            self.txt_templates.insert(tk.END, f"📌 [{name}]\n{text}\n\n" + "-"*65 + "\n\n")

        self._filter_action_table()
        self._filter_gap_table()

        self.tree_full.delete(*self.tree_full.get_children())
        for idx, (_, row) in enumerate(df.iterrows()):
            prio = row["Outreach Priority"]
            tag = prio if prio in PRIO_COLOR_MAP else ("even" if idx % 2 == 0 else "odd")
            self.tree_full.insert("", tk.END, values=(
                row["Google Skills Profile URL"],
                row["Verification Status"],
                row["Badges Earned"],
                row["Badges Remaining"],
                row["Outreach Priority"],
                row["Campaign Status"]
            ), tags=(tag,))

    def _filter_action_table(self, event=None):
        if self.analysis_df is None:
            return

        priority = self.combo_action_filter.get()
        df = self.analysis_df
        filtered_df = df if priority == "All" else df[df["Outreach Priority"] == priority]

        self.tree_action.delete(*self.tree_action.get_children())
        for idx, (_, row) in enumerate(filtered_df.iterrows()):
            prio = row["Outreach Priority"]
            tag = prio if prio in PRIO_COLOR_MAP else ("even" if idx % 2 == 0 else "odd")
            self.tree_action.insert("", tk.END, values=(
                row["Google Skills Profile URL"],
                row["Outreach Priority"],
                row["Verification Status"],
                row["Badges Earned"],
                row["Recommended Action"]
            ), tags=(tag,))

    def _filter_gap_table(self, event=None):
        if self.analysis_df is None:
            return

        choice = self.combo_gap_filter.get()
        df = self.analysis_df[self.analysis_df["Verification Status"] == "Verified"].copy()
        df["Badges Remaining"] = pd.to_numeric(df["Badges Remaining"], errors="coerce").fillna(0)

        if "1 Badge Remaining" in choice:
            filtered_df = df[df["Badges Remaining"] == 1]
        elif "2 Badges Remaining" in choice:
            filtered_df = df[df["Badges Remaining"] == 2]
        elif "3+ Badges" in choice:
            filtered_df = df[df["Badges Remaining"] >= 3]
        else:
            filtered_df = df

        self.tree_gap.delete(*self.tree_gap.get_children())
        for idx, (_, row) in enumerate(filtered_df.iterrows()):
            prio = row["Outreach Priority"]
            tag = prio if prio in PRIO_COLOR_MAP else ("even" if idx % 2 == 0 else "odd")
            self.tree_gap.insert("", tk.END, values=(
                row["Google Skills Profile URL"],
                row["Outreach Priority"],
                row["Badges Earned"],
                int(row["Badges Remaining"]),
                row["Campaign Status"]
            ), tags=(tag,))

    def export_csv(self):
        if self.analysis_df is None:
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="gdg_skilltrack_desktop_report.csv"
        )
        if save_path:
            self.analysis_df.to_csv(save_path, index=False)
            messagebox.showinfo("Export Successful", f"Report saved to:\n{save_path}")

if __name__ == "__main__":
    app = SkillTrackDesktopApp()
    app.mainloop()