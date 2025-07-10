from dotenv import load_dotenv
load_dotenv()
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
import json
import os

OMDB_API_KEY = os.getenv("OMDB_API_KEY", "")
DATA_FILE = "watchlist.json"

def load_watchlist():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def save_watchlist():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(watchlist, f, indent=2)

watchlist = load_watchlist()

def fetch_poster(title, category):
    try:
        r = requests.get("http://www.omdbapi.com/", params={"t": title, "apikey": OMDB_API_KEY})
        data = r.json()
        if data.get("Response") == "True" and data.get("Poster") not in (None, "N/A"):
            return data["Poster"]
    except:
        pass
    if category.lower() == "anime":
        try:
            jr = requests.get("https://api.jikan.moe/v4/anime", params={"q": title, "limit": 1})
            jdata = jr.json().get("data") or []
            if jdata:
                return jdata[0]["images"]["jpg"]["image_url"]
        except:
            pass
    return ""

def add_or_update(editing=False):
    sel_item = tree.focus()
    idx = tree.index(sel_item) if sel_item else None

    entry = {
        "title": title_var.get().strip(),
        "category": category_var.get(),
        "status": status_var.get(),
        "rating": rating_var.get(),
        "episodes": episodes_var.get() if status_var.get() == "Watching" else "",
        "notes": notes_text.get("1.0", tk.END).strip(),
        "image": fetch_poster(title_var.get().strip(), category_var.get())
    }

    if not entry["title"] or not entry["category"]:
        messagebox.showerror("Error", "Title and Category are required.")
        return

    if editing and idx is not None:
        watchlist[idx] = entry
    else:
        watchlist.append(entry)

    save_watchlist()
    refresh_list()
    clear_form()
    messagebox.showinfo("Saved", f"'{entry['title']}' has been saved.")

def delete_entry():
    sel = tree.focus()
    if not sel:
        messagebox.showerror("Error", "Select an item first.")
        return
    idx = tree.index(sel)
    watchlist.pop(idx)
    save_watchlist()
    refresh_list()
    clear_form()
    messagebox.showinfo("Deleted", "Item removed.")

def refresh_list():
    tree.delete(*tree.get_children())
    for item in watchlist:
        tree.insert("", "end", values=(item["title"], item["category"], item["status"], item["rating"]))

def clear_form():
    title_var.set("")
    category_var.set("")
    status_var.set("Plan to Watch")
    rating_var.set(0)
    episodes_var.set(0)
    notes_text.delete("1.0", tk.END)
    toggle_episode_field()

def view_selected(event=None):
    sel = tree.focus()
    if not sel:
        return
    idx = tree.index(sel)
    entry = watchlist[idx]

    title_var.set(entry["title"])
    category_var.set(entry["category"])
    status_var.set(entry["status"])
    rating_var.set(entry["rating"])
    episodes_var.set(entry.get("episodes", 0))
    notes_text.delete("1.0", tk.END)
    notes_text.insert("1.0", entry.get("notes", ""))
    toggle_episode_field()

    detail_title.config(text=entry["title"])
    detail_category.config(text=entry["category"]) # type: ignore
    detail_status.config(text=entry["status"])     # type: ignore
    detail_rating.config(text=f"{entry['rating']} / 5") # type: ignore
    detail_episodes.config(text=f"Episodes watched: {entry.get('episodes','0')}")  # type: ignore
    detail_notes.config(text=entry.get("notes", "") or "-")   # type: ignore

    try:
        if entry["image"]:
            resp = requests.get(entry["image"])
            img = Image.open(BytesIO(resp.content))
            img.thumbnail((150, 225))
            tkimg = ImageTk.PhotoImage(img)
            detail_image.config(image=tkimg)
            detail_image.image = tkimg
        else:
            detail_image.config(image="", text="No image")
    except:
        detail_image.config(image="", text="Error loading image")

def toggle_episode_field(*args):
    if status_var.get() == "Watching":
        episodes_label.pack(anchor="w", pady=(5, 0))
        episodes_spin.pack(anchor="w")
    else:
        episodes_label.pack_forget()
        episodes_spin.pack_forget()

# GUI Setup
root = tk.Tk()
root.title("🎬 WatchList Tracker")
root.geometry("1080x700")
root.configure(bg="#f3f3f3")

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'))
style.configure("TButton", font=('Segoe UI', 10))
style.configure("TLabel", font=('Segoe UI', 10))

title_var = tk.StringVar()
category_var = tk.StringVar()
status_var = tk.StringVar(value="Plan to Watch")
rating_var = tk.IntVar()
episodes_var = tk.IntVar()

status_var.trace("w", toggle_episode_field)

form_frame = tk.LabelFrame(root, text="🎥 Add / Edit Entry", padx=10, pady=10, font=('Segoe UI', 11, 'bold'))
form_frame.pack(side="left", fill="y", padx=10, pady=10)

tk.Label(form_frame, text="Title *").pack(anchor="w")
tk.Entry(form_frame, textvariable=title_var, font=('Segoe UI', 10)).pack(fill="x")

tk.Label(form_frame, text="Category *").pack(anchor="w", pady=(5,0))
ttk.Combobox(form_frame, textvariable=category_var,
             values=["Movie", "Anime", "TV Show", "Documentary", "Other"],
             font=('Segoe UI', 10)).pack(fill="x")

tk.Label(form_frame, text="Status").pack(anchor="w", pady=(5,0))
ttk.Combobox(form_frame, textvariable=status_var,
             values=["Watched", "Watching", "Plan to Watch"],
             font=('Segoe UI', 10)).pack(fill="x")

tk.Label(form_frame, text="Rating (0–5)").pack(anchor="w", pady=(5,0))
tk.Spinbox(form_frame, from_=0, to=5, textvariable=rating_var, width=5, font=('Segoe UI', 10)).pack(anchor="w")

episodes_label = tk.Label(form_frame, text="Episodes Watched", font=('Segoe UI', 10))
episodes_spin = tk.Spinbox(form_frame, from_=0, to=1000, textvariable=episodes_var, width=5, font=('Segoe UI', 10))

tk.Label(form_frame, text="Notes").pack(anchor="w", pady=(5,0))
notes_text = tk.Text(form_frame, height=5, font=('Segoe UI', 10))
notes_text.pack(fill="both", pady=(0,5))

tk.Button(form_frame, text="➕ Add New", command=lambda: add_or_update(editing=False), bg="#4CAF50", fg="white").pack(fill="x", pady=2)
tk.Button(form_frame, text="✏️ Edit Selected", command=lambda: add_or_update(editing=True), bg="#2196F3", fg="white").pack(fill="x", pady=2)
tk.Button(form_frame, text="❌ Delete Selected", command=delete_entry, bg="#f44336", fg="white").pack(fill="x", pady=2)

right_frame = tk.Frame(root, bg="#f3f3f3")
right_frame.pack(side="right", expand=True, fill="both", padx=10, pady=10)

tree = ttk.Treeview(right_frame, columns=("Title", "Category", "Status", "Rating"), show="headings", height=12)
for col in ("Title", "Category", "Status", "Rating"):
    tree.heading(col, text=col)
    tree.column(col, width=150)
tree.pack(fill="x", pady=5)
tree.bind("<<TreeviewSelect>>", view_selected)

detail_frame = tk.LabelFrame(right_frame, text="📋 Details", padx=10, pady=10, font=('Segoe UI', 11, 'bold'))
detail_frame.pack(fill="both", expand=True, pady=10)

detail_image = tk.Label(detail_frame, text="No image")
detail_image.pack(side="left", padx=10)

info_frame = tk.Frame(detail_frame, bg="#f3f3f3")
info_frame.pack(side="right", fill="both", expand=True)

detail_title = tk.Label(info_frame, text="Title", font=("Segoe UI", 14, "bold"), bg="#f3f3f3")
detail_title.pack(anchor="w", pady=(0, 5))

for label_text, var_name in [
    ("Category:", "detail_category"),
    ("Status:", "detail_status"),
    ("Rating:", "detail_rating"),
    ("Episodes:", "detail_episodes"),
    ("Notes:", "detail_notes")
]:
    tk.Label(info_frame, text=label_text, font=('Segoe UI', 10, 'bold'), bg="#f3f3f3").pack(anchor="w")
    globals()[var_name] = tk.Label(info_frame, text="-", wraplength=400, justify="left", bg="#f3f3f3", font=('Segoe UI', 10))
    globals()[var_name].pack(anchor="w", pady=(0, 5))

refresh_list()
root.mainloop()
