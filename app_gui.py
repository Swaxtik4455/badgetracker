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

class SkillTrackDesktopApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚡ SkillTrack — GDG Campaign Tracker (Desktop)")
        self.geometry("1100x700")  # Exact string formatting without spaces
        self.minsize(900, 600)

        # Application State
        self.raw_df = None
        self.analysis_df = None
        self.csv_path = None

        self._build_ui()

    def _build_ui(self):
        # --- Top Header & File Controls ---
        top_bar = ttk.Frame(self, padding=10)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        title_label = ttk.Label(
            top_bar, 
            text="⚡ SkillTrack Desktop", 
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=(0, 20))

        self.btn_load_csv = ttk.Button(top_bar, text="📁 Load CSV File", command=self.load_csv)
        self.btn_load_csv.pack(side=tk.LEFT, padx=5)

        self.btn_run_verification = ttk.Button(
            top_bar, text="▶ Run Verification", command=self.run_verification, state=tk.DISABLED
        )
        self.btn_run_verification.pack(side=tk.LEFT, padx=5)

        self.btn_export_csv = ttk.Button(
            top_bar, text="📥 Export Report CSV", command=self.export_csv, state=tk.DISABLED
        )
        self.btn_export_csv.pack(side=tk.RIGHT, padx=5)

        self.status_label = ttk.Label(top_bar, text="Please load a candidate CSV file to begin.", font=("Helvetica", 10, "italic"))
        self.status_label.pack(side=tk.LEFT, padx=15)

        # --- Progress Bar ---
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=(0, 5))

        # --- Tab Navigation Control ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Overview & Health Summary
        self.tab_overview = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_overview, text="📊 Summary & Health")

        # Tab 2: Smart Action & Outreach Priority
        self.tab_action = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_action, text="🎯 Outreach Priority")

        # Tab 3: Copy-Paste Broadcast Templates
        self.tab_templates = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_templates, text="📢 Broadcast Templates")

        # Tab 4: Badge Gap Analyzer
        self.tab_gap = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_gap, text="🔍 Badge Gap Analyzer")

        # Tab 5: Full Data View
        self.tab_full_data = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_full_data, text="📑 Full Data View")

        self._setup_overview_tab()
        self._setup_action_tab()
        self._setup_templates_tab()
        self._setup_gap_tab()
        self._setup_full_data_tab()

    def _setup_overview_tab(self):
        # Health Callout Box
        self.health_frame = ttk.LabelFrame(self.tab_overview, text=" Campaign Health Status ", padding=10)
        self.health_frame.pack(fill=tk.X, pady=(0, 10))

        self.lbl_health_status = ttk.Label(self.health_frame, text="Status: Waiting for verification run...", font=("Helvetica", 11, "bold"))
        self.lbl_health_status.pack(anchor="w")

        # Metrics Box
        self.metrics_frame = ttk.LabelFrame(self.tab_overview, text=" Performance Metrics ", padding=10)
        self.metrics_frame.pack(fill=tk.X, pady=(0, 10))

        self.lbl_metric_total = ttk.Label(self.metrics_frame, text="Total Participants: -", font=("Helvetica", 11, "bold"))
        self.lbl_metric_total.grid(row=0, column=0, padx=15, pady=5, sticky="w")

        self.lbl_metric_verified = ttk.Label(self.metrics_frame, text="Verified Profiles: -", font=("Helvetica", 11))
        self.lbl_metric_verified.grid(row=0, column=1, padx=15, pady=5, sticky="w")

        self.lbl_metric_completed = ttk.Label(self.metrics_frame, text="Completed (10/10): -", font=("Helvetica", 11))
        self.lbl_metric_completed.grid(row=0, column=2, padx=15, pady=5, sticky="w")

        self.lbl_metric_almost = ttk.Label(self.metrics_frame, text="Almost Completed (8-9): -", font=("Helvetica", 11))
        self.lbl_metric_almost.grid(row=0, column=3, padx=15, pady=5, sticky="w")

    def _setup_action_tab(self):
        filter_frame = ttk.Frame(self.tab_action)
        filter_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(filter_frame, text="Filter Priority: ").pack(side=tk.LEFT)
        self.combo_action_filter = ttk.Combobox(
            filter_frame, 
            values=["All", "HIGH (Quick Win)", "HIGH (Broken / Private)", "MEDIUM (Onboarding Needed)", "MEDIUM (Encouragement Needed)", "LOW (Completed)"],
            state="readonly"
        )
        self.combo_action_filter.set("All")
        self.combo_action_filter.pack(side=tk.LEFT, padx=5)
        self.combo_action_filter.bind("<<ComboboxSelected>>", self._filter_action_table)

        self.tree_action = self._create_treeview(
            self.tab_action, 
            columns=("URL", "Priority", "Status", "Badges", "Recommended Action")
        )

    def _setup_templates_tab(self):
        self.txt_templates = tk.Text(self.tab_templates, wrap=tk.WORD, font=("Consolas", 10))
        vsb = ttk.Scrollbar(self.tab_templates, orient="vertical", command=self.txt_templates.yview)
        self.txt_templates.configure(yscrollcommand=vsb.set)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_templates.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _setup_gap_tab(self):
        gap_filter_frame = ttk.Frame(self.tab_gap)
        gap_filter_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(gap_filter_frame, text="Remaining Badges Filter: ").pack(side=tk.LEFT)
        self.combo_gap_filter = ttk.Combobox(
            gap_filter_frame, 
            values=["All (1-10)", "1 Badge Remaining (9/10)", "2 Badges Remaining (8/10)", "3+ Badges Remaining"],
            state="readonly"
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

        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="w")

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
            self.status_label.config(text=f"Verifying ({idx}/{len(urls)}): {url[:45]}...")
            self.update_idletasks()
            
            res = scraper.fetch_profile(url)
            raw_results.append(res)
            self.progress["value"] = idx

        save_run(raw_results)  # Persist batch run into SQLite database
        self.analysis_df = process_results_dataframe(raw_results)
        
        self._update_dashboards()
        self.btn_export_csv.config(state=tk.NORMAL)
        self.status_label.config(text="✓ Verification complete! Results updated.")
        messagebox.showinfo("Success", "Profile verification completed successfully!")

    def _update_dashboards(self):
        df = self.analysis_df
        if df is None:
            return

        # 1. Health & Overview Metrics
        health = calculate_campaign_health(df)
        self.lbl_health_status.config(text=f"Health Score: {health['health_score']}%  |  {health['health_status']}")

        self.lbl_metric_total.config(text=f"Total Participants: {health['total']}")
        self.lbl_metric_verified.config(text=f"Verified Profiles: {len(df[df['Verification Status'] == 'Verified'])}")
        self.lbl_metric_completed.config(text=f"Completed (10/10): {health['completed']}")
        self.lbl_metric_almost.config(text=f"Almost Completed (8-9): {health['almost']}")

        # 2. Update Broadcast Templates Tab
        templates = generate_outreach_templates(df)
        self.txt_templates.delete("1.0", tk.END)
        self.txt_templates.insert(tk.END, "=== BROADCAST REMINDER TEMPLATES ===\n\n")
        for name, text in templates.items():
            self.txt_templates.insert(tk.END, f"[{name}]\n{text}\n\n" + "-"*60 + "\n\n")

        # 3. Populate Action & Gap Tables
        self._filter_action_table()
        self._filter_gap_table()

        # 4. Populate Full Data View Table
        self.tree_full.delete(*self.tree_full.get_children())
        for _, row in df.iterrows():
            self.tree_full.insert("", tk.END, values=(
                row["Google Skills Profile URL"],
                row["Verification Status"],
                row["Badges Earned"],
                row["Badges Remaining"],
                row["Outreach Priority"],
                row["Campaign Status"]
            ))

    def _filter_action_table(self, event=None):
        if self.analysis_df is None:
            return

        priority = self.combo_action_filter.get()
        df = self.analysis_df
        filtered_df = df if priority == "All" else df[df["Outreach Priority"] == priority]

        self.tree_action.delete(*self.tree_action.get_children())
        for _, row in filtered_df.iterrows():
            self.tree_action.insert("", tk.END, values=(
                row["Google Skills Profile URL"],
                row["Outreach Priority"],
                row["Verification Status"],
                row["Badges Earned"],
                row["Recommended Action"]
            ))

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
        for _, row in filtered_df.iterrows():
            self.tree_gap.insert("", tk.END, values=(
                row["Google Skills Profile URL"],
                row["Outreach Priority"],
                row["Badges Earned"],
                int(row["Badges Remaining"]),
                row["Campaign Status"]
            ))

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