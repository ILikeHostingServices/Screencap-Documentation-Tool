#!/usr/bin/env python3
#
# demo_wizard.py
# 2026-10-13
# Version: v1.0.0
#
# PURPOSE:
# A made-up "Example App" setup wizard used to make the store screenshots.
# It clicks and types into itself with real X input (xdotool), so the
# built-in recorder notes real clicks and keys. WIZARD_MANUAL=1 shows the
# license page and waits instead. The product key is fake.
import os
import subprocess
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Example App Setup")
root.geometry("820x560+230+70")
root.resizable(False, False)
style = ttk.Style(); style.theme_use("clam")
F = ("DejaVu Sans", 11); H = ("DejaVu Sans", 17, "bold")
side = tk.Frame(root, bg="#1f4e8c", width=190); side.pack(side="left", fill="y")
tk.Label(side, text="Example\nApp", fg="white", bg="#1f4e8c", font=("DejaVu Sans", 22, "bold"),
         justify="left").place(x=22, y=30)
body = tk.Frame(root, bg="white"); body.pack(side="left", fill="both", expand=True)
page = tk.Frame(body, bg="white"); page.place(x=28, y=24, width=580, height=430)
bar = tk.Frame(body, bg="#f0f0f0", height=64); bar.pack(side="bottom", fill="x")
btn_back = ttk.Button(bar, text="< Back", width=10); btn_back.place(x=250, y=16)
btn_next = ttk.Button(bar, text="Next >", width=10); btn_next.place(x=360, y=16)
btn_cancel = ttk.Button(bar, text="Cancel", width=10); btn_cancel.place(x=480, y=16)
v_accept = tk.IntVar(); v_short = tk.IntVar(value=0); v_launch = tk.IntVar(value=1)
w = {}

def clear():
    for c in page.winfo_children(): c.destroy()

def heading(t, sub):
    tk.Label(page, text=t, font=H, bg="white").place(x=0, y=0)
    tk.Label(page, text=sub, font=F, bg="white", fg="#444", wraplength=560, justify="left").place(x=0, y=40)

def p_welcome():
    clear(); heading("Welcome to the Example App Setup Wizard",
                     "This wizard installs Example App 4.2 on your computer. Close other programs before you continue, then click Next.")
def p_license():
    clear(); heading("License Agreement", "Read the following license agreement carefully.")
    t = tk.Text(page, font=("DejaVu Sans", 10), height=11, width=70, relief="solid", bd=1)
    t.insert("1.0", "EXAMPLE APP END USER LICENSE AGREEMENT\n\n1. You may install and use the software on any number of computers in your organization.\n2. The software is provided as is, without warranty of any kind.\n3. ...")
    t.configure(state="disabled"); t.place(x=0, y=80, width=560, height=230)
    w["accept"] = tk.Checkbutton(page, text="I accept the agreement", variable=v_accept, font=F, bg="white")
    w["accept"].place(x=0, y=330)
def p_key():
    clear(); heading("Product Key", "Enter the product key from your order confirmation.")
    tk.Label(page, text="Product key:", font=F, bg="white").place(x=0, y=112)
    w["key"] = ttk.Entry(page, font=("DejaVu Sans", 12)); w["key"].place(x=120, y=108, width=420)
    tk.Label(page, text="Organization:", font=F, bg="white").place(x=0, y=162)
    e = ttk.Entry(page, font=("DejaVu Sans", 12)); e.insert(0, "Example Corp IT"); e.place(x=120, y=158, width=420)
def p_location():
    clear(); heading("Select Destination Location", "Setup will install Example App into the following folder.")
    e = ttk.Entry(page, font=("DejaVu Sans", 12)); e.insert(0, "C:\\Program Files\\Example App"); e.place(x=0, y=100, width=440)
    ttk.Button(page, text="Browse...").place(x=455, y=98)
    tk.Label(page, text="At least 180 MB of free disk space is required.", font=F, bg="white", fg="#444").place(x=0, y=145)
    w["short"] = tk.Checkbutton(page, text="Create a desktop shortcut", variable=v_short, font=F, bg="white")
    w["short"].place(x=0, y=200)
def p_ready():
    clear(); heading("Ready to Install", "Setup is ready to install Example App. Click Install to continue.")
    tk.Label(page, text="Destination: C:\\Program Files\\Example App\nDesktop shortcut: yes", font=F, bg="white",
             justify="left").place(x=0, y=100)
    btn_next.configure(text="Install")
def p_installing():
    clear(); heading("Installing", "Please wait while Setup installs Example App.")
    pb = ttk.Progressbar(page, length=540, maximum=100); pb.place(x=0, y=110)
    lab = tk.Label(page, text="Copying files...", font=F, bg="white"); lab.place(x=0, y=145)
    btn_next.state(["disabled"]); btn_back.state(["disabled"])
    def step(n=0):
        pb["value"] = n
        if n < 100: root.after(40, step, n + 2)
        else: p_finish()
    step()
def p_finish():
    clear(); heading("Completing the Example App Setup Wizard", "Example App is installed. Click Finish to close Setup.")
    tk.Checkbutton(page, text="Launch Example App", variable=v_launch, font=F, bg="white").place(x=0, y=110)
    btn_next.state(["!disabled"]); btn_next.configure(text="Finish")

pages = [p_welcome, p_license, p_key, p_location, p_ready, p_installing]
state = {"i": 0}
def nxt():
    state["i"] += 1
    if state["i"] < len(pages): pages[state["i"]]()
    else: root.after(1500, root.destroy)
btn_next.configure(command=nxt)

def center(widget):
    root.update_idletasks()
    return widget.winfo_rootx() + widget.winfo_width() // 2, widget.winfo_rooty() + widget.winfo_height() // 2
def xdo(*a): subprocess.run(["xdotool", *a])
def click(widget, dx=0):
    x, y = center(widget); xdo("mousemove", str(x + dx), str(y)); root.after(450, lambda: xdo("click", "1"))

T = [(3.0, lambda: click(btn_next)),
     (6.0, lambda: click(w["accept"], -70)),
     (7.6, lambda: click(btn_next)),
     (10.5, lambda: click(w["key"])),
     (11.4, lambda: xdo("type", "--delay", "70", "EXMPL-7K2QD-9VX4M-PL8RT-3HZW6")),
     (15.0, lambda: click(btn_next)),
     (18.0, lambda: click(w["short"], -80)),
     (19.6, lambda: click(btn_next)),
     (22.5, lambda: click(btn_next)),
     (31.0, lambda: click(btn_next))]
if not os.environ.get('WIZARD_MANUAL'):
    for t, fn in T: root.after(int(t * 1000), fn)
else:
    root.after(500, nxt)
p_welcome()
root.mainloop()
