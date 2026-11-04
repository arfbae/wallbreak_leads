import os
import re
import shutil
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk


class ModernPhotoTriageApp:
    """Offline desktop photo triage application with reversible file actions."""

    IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff")
    WINDOWS_RESERVED_NAMES = {
        "CON", "PRN", "AUX", "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Instant Photo Triage Studio")
        self.root.geometry("1100x800")
        self.root.configure(bg="#1e1e2e")

        self.folder_path = ""
        self.history = []
        self.temp_dir = tempfile.mkdtemp(prefix="triage_trash_")

        self.setup_styles()
        self.create_layout()

        self.root.bind("<Control-z>", lambda event: self.undo_last_action())
        self.root.bind("<Control-Z>", lambda event: self.undo_last_action())
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        # Linux Tk uses Button-4/Button-5 instead of MouseWheel.
        self.root.bind_all("<Button-4>", lambda event: self._scroll_canvas(-1))
        self.root.bind_all("<Button-5>", lambda event: self._scroll_canvas(1))
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _scroll_canvas(self, amount):
        if self.canvas.winfo_exists():
            self.canvas.yview_scroll(amount, "units")

    def _on_mousewheel(self, event):
        # Windows/macOS report a delta; guard against platforms that do not.
        delta = getattr(event, "delta", 0)
        if delta:
            self._scroll_canvas(int(-delta / 120) or (-1 if delta > 0 else 1))

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(".", background="#1e1e2e", foreground="#ffffff")
        self.style.configure("TFrame", background="#1e1e2e")
        self.style.configure("Card.TFrame", background="#252538", borderwidth=1, relief="solid")
        self.style.configure("Header.TFrame", background="#11111b")

    def create_layout(self):
        header = ttk.Frame(self.root, style="Header.TFrame", padding=15)
        header.pack(fill=tk.X, side=tk.TOP)

        btn_open = tk.Button(
            header, text="📁 Open Photo Folder", font=("Segoe UI", 11, "bold"),
            bg="#89b4fa", fg="#11111b", activebackground="#b4befe", relief="flat",
            padx=15, pady=6, cursor="hand2", command=self.select_folder,
        )
        btn_open.pack(side=tk.LEFT, padx=5)

        self.lbl_status = ttk.Label(
            header, text="No directory selected", font=("Segoe UI", 10, "italic"),
            background="#11111b", foreground="#a6adc8",
        )
        self.lbl_status.pack(side=tk.LEFT, padx=15)

        btn_undo = tk.Button(
            header, text="↩️ Undo Action (Ctrl+Z)", font=("Segoe UI", 10),
            bg="#313244", fg="#cdd6f4", activebackground="#45475a", relief="flat",
            padx=12, pady=6, cursor="hand2", command=self.undo_last_action,
        )
        btn_undo.pack(side=tk.RIGHT, padx=5)

        self.canvas = tk.Canvas(self.root, bg="#1e1e2e", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.grid_frame = ttk.Frame(self.canvas)
        self.grid_frame.bind(
            "<Configure>",
            lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        self.scrollbar.pack(side="right", fill="y")

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if not folder_selected:
            return
        self.folder_path = folder_selected
        self.lbl_status.config(text=f"Active Folder: {os.path.basename(self.folder_path)}")
        self.refresh_grid()

    def refresh_grid(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        if not self.folder_path:
            return

        try:
            files = sorted(
                (name for name in os.listdir(self.folder_path)
                 if name.lower().endswith(self.IMAGE_EXTENSIONS)),
                key=str.casefold,
            )
        except (OSError, UnicodeError) as error:
            messagebox.showerror("Folder Error", f"Could not read folder:\n{error}")
            return

        if not files:
            ttk.Label(
                self.grid_frame, text="🎉 Workspace Clear! No remaining images found.",
                font=("Segoe UI", 14), foreground="#a6adc8",
            ).pack(pady=50, padx=50)
            return

        for index, file_name in enumerate(files):
            self.create_image_card(file_name, index // 4, index % 4)

    def create_image_card(self, file_name, row, col):
        full_path = os.path.join(self.folder_path, file_name)
        name_without_ext, ext = os.path.splitext(file_name)

        card = ttk.Frame(self.grid_frame, style="Card.TFrame", padding=10)
        card.grid(row=row, column=col, padx=12, pady=12)

        img_label = tk.Label(card, bg="#252538", activebackground="#252538", cursor="hand2")
        try:
            with Image.open(full_path) as source_image:
                preview = source_image.copy()
            preview.thumbnail((180, 180))
            tk_img = ImageTk.PhotoImage(preview)
            img_label.config(image=tk_img)
            img_label.image = tk_img
        except (OSError, ValueError, TypeError):
            img_label.config(
                text="⚠️ Error Opening Image\nFile may be corrupted", fg="#f38ba8",
                font=("Segoe UI", 9), bg="#252538", width=20, height=10,
            )
        img_label.pack(pady=4)

        name_entry = tk.Entry(
            card, width=20, font=("Segoe UI", 10), justify="center",
            bg="#1e1e2e", fg="#cdd6f4", insertbackground="#ffffff", relief="flat",
            highlightthickness=1, highlightbackground="#45475a", highlightcolor="#89b4fa",
        )
        name_entry.insert(0, name_without_ext)
        name_entry.pack(pady=8, ipady=3)
        name_entry.bind(
            "<Return>",
            lambda event, f=file_name, entry=name_entry, extension=ext, c=card:
            self.instant_rename(f, entry, extension, c),
        )

        btn_frame = ttk.Frame(card)
        btn_frame.pack(fill=tk.X, pady=2)

        btn_cross = tk.Button(
            btn_frame, text="❌ Delete", font=("Segoe UI", 9, "bold"),
            bg="#f38ba8", fg="#11111b", activebackground="#e06c75", relief="flat",
            width=8, pady=3, cursor="hand2",
            command=lambda: self.instant_delete(file_name, card),
        )
        btn_cross.pack(side=tk.LEFT, padx=4)

        btn_tick = tk.Button(
            btn_frame, text="✔️ Save", font=("Segoe UI", 9, "bold"),
            bg="#a6e3a1", fg="#11111b", activebackground="#98c379", relief="flat",
            width=8, pady=3, cursor="hand2",
            command=lambda: self.instant_rename(file_name, name_entry, ext, card),
        )
        btn_tick.pack(side=tk.RIGHT, padx=4)

        drag_data = {"start_x": 0}

        def on_drag_start(event):
            drag_data["start_x"] = event.x

        def on_drag_release(event):
            delta_x = event.x - drag_data["start_x"]
            if delta_x > 50:
                self.instant_rename(file_name, name_entry, ext, card)
            elif delta_x < -50:
                self.instant_delete(file_name, card)

        img_label.bind("<Button-1>", on_drag_start)
        img_label.bind("<ButtonRelease-1>", on_drag_release)

    @classmethod
    def _valid_base_name(cls, name):
        """Return whether a base name is safe on both Windows and POSIX systems."""
        if not name or name in {".", ".."}:
            return False
        if os.path.basename(name) != name or "/" in name or "\\" in name:
            return False
        if any(ord(char) < 32 for char in name):
            return False
        if re.search(r'[<>:"|?*]', name):
            return False
        if name.endswith((".", " ")):
            return False
        if name.split(".", 1)[0].upper() in cls.WINDOWS_RESERVED_NAMES:
            return False
        return True

    def instant_rename(self, old_file_name, entry_widget, ext, card_frame):
        old_path = os.path.join(self.folder_path, old_file_name)
        new_base_name = entry_widget.get().strip()
        if not self._valid_base_name(new_base_name):
            messagebox.showwarning(
                "Invalid Name",
                "Use a non-empty filename without path separators or characters invalid on Windows.",
            )
            return

        new_file_name = f"{new_base_name}{ext}"
        new_path = os.path.join(self.folder_path, new_file_name)
        if old_file_name != new_file_name and os.path.abspath(old_path) != os.path.abspath(new_path):
            if os.path.exists(new_path):
                messagebox.showerror("Name Conflict", f"A file named '{new_file_name}' already exists in this folder.")
                return
            try:
                os.rename(old_path, new_path)
            except FileNotFoundError:
                messagebox.showerror("File Missing", f"'{old_file_name}' is no longer available.")
                return
            except PermissionError:
                messagebox.showerror("File in Use", f"Could not rename '{old_file_name}'. Ensure it's not open in another program.")
                return
            except OSError as error:
                messagebox.showerror("Error", f"Could not rename file:\n{error}")
                return
            self.history.append({"type": "rename", "old_path": old_path, "new_path": new_path})
        card_frame.destroy()

    def instant_delete(self, file_name, card_frame):
        src_path = os.path.join(self.folder_path, file_name)
        dest_path = os.path.join(self.temp_dir, file_name)
        if os.path.exists(dest_path):
            stem, extension = os.path.splitext(file_name)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(self.temp_dir, f"{stem}__{counter}{extension}")
                counter += 1
        try:
            shutil.move(src_path, dest_path)
        except FileNotFoundError:
            messagebox.showerror("File Missing", f"'{file_name}' is no longer available.")
            return
        except PermissionError:
            messagebox.showerror("File in Use", f"Could not move '{file_name}'. Ensure it's not open in another program.")
            return
        except OSError as error:
            messagebox.showerror("Error", f"Could not move file to trash:\n{error}")
            return
        self.history.append({"type": "delete", "original_path": src_path, "cached_path": dest_path})
        card_frame.destroy()

    def undo_last_action(self):
        if not self.history:
            return

        last_action = self.history[-1]
        try:
            if last_action["type"] == "delete":
                if os.path.exists(last_action["original_path"]):
                    raise FileExistsError("A file with the original name already exists.")
                shutil.move(last_action["cached_path"], last_action["original_path"])
            elif last_action["type"] == "rename":
                if os.path.exists(last_action["old_path"]):
                    raise FileExistsError("The original filename is already in use.")
                os.rename(last_action["new_path"], last_action["old_path"])
            else:
                raise ValueError("Unknown history action")
        except (FileNotFoundError, FileExistsError, PermissionError, OSError, ValueError) as error:
            messagebox.showerror("Undo Error", f"Could not restore the last action:\n{error}")
            return

        self.history.pop()
        self.refresh_grid()

    def on_closing(self):
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        finally:
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ModernPhotoTriageApp(root)
    root.mainloop()
