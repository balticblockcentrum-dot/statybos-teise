import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lex import config, corpus, draft, ingest, llm, update

BG = "#f4f6f8"
ACCENT = "#1f6feb"


class App:
    def __init__(self, root):
        self.root = root
        self.q = queue.Queue()
        self.running = False
        self.file_path = None
        self.out_pdf = None
        self.out_docx = None

        root.title(f"Statybos teisės asistentas v{update.VERSION}")
        root.geometry("900x680")
        root.configure(bg=BG)

        head = tk.Frame(root, bg=ACCENT)
        head.pack(fill="x")
        tk.Label(
            head, text="Statybos teisės asistentas", bg=ACCENT, fg="white",
            font=("Segoe UI", 16, "bold"), pady=10,
        ).pack(side="left", padx=16)
        tk.Label(
            head, text="UAB Baltic block centrum Šilalė", bg=ACCENT, fg="#dbe7ff",
            font=("Segoe UI", 10), pady=10,
        ).pack(side="right", padx=16)

        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        pick = tk.Frame(body, bg=BG)
        pick.pack(fill="x")
        self.pick_btn = tk.Button(
            pick, text="Pasirinkti dokumentą…", command=self.choose_file,
            font=("Segoe UI", 11), bg="white", relief="groove", padx=10, pady=6,
        )
        self.pick_btn.pack(side="left")
        self.file_lbl = tk.Label(
            pick, text="Dokumentas nepasirinktas (PDF, DOCX arba TXT)",
            bg=BG, fg="#555", font=("Segoe UI", 10), anchor="w",
        )
        self.file_lbl.pack(side="left", padx=12, fill="x", expand=True)

        actions = tk.Frame(body, bg=BG)
        actions.pack(fill="x", pady=10)
        self.analyze_btn = tk.Button(
            actions, text="Analizuoti", command=lambda: self.start("analyze"),
            font=("Segoe UI", 11, "bold"), bg=ACCENT, fg="white", padx=16, pady=8,
        )
        self.analyze_btn.pack(side="left")
        self.draft_btn = tk.Button(
            actions, text="Parengti siunčiamą dokumentą", command=lambda: self.start("draft"),
            font=("Segoe UI", 11), bg="white", relief="groove", padx=16, pady=8,
        )
        self.draft_btn.pack(side="left", padx=8)

        self.status = tk.Label(body, text="Pasirinkite dokumentą ir spauskite „Analizuoti“.", bg=BG, fg="#333", font=("Segoe UI", 10), anchor="w")
        self.status.pack(fill="x")

        text_frame = tk.Frame(body, bg=BG)
        text_frame.pack(fill="both", expand=True, pady=8)
        scroll = ttk.Scrollbar(text_frame)
        scroll.pack(side="right", fill="y")
        self.text = tk.Text(
            text_frame, wrap="word", font=("Segoe UI", 11), bg="white",
            relief="solid", borderwidth=1, yscrollcommand=scroll.set, padx=12, pady=10,
        )
        self.text.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.text.yview)
        self.text.insert("1.0", "Čia bus parodytas teisinės analizės atsakymas.\n\n Programa remiasi tik pateiktomis teisės normomis ir cituoja jas tiksliai. Galutinius teismui skirtus dokumentus turi peržiūrėti licencijuotas advokatas.")
        self.text.config(state="disabled")

        out = tk.Frame(body, bg=BG)
        out.pack(fill="x")
        self.pdf_btn = tk.Button(out, text="Atidaryti PDF", command=lambda: self.open_out("pdf"), font=("Segoe UI", 10), state="disabled", padx=10)
        self.pdf_btn.pack(side="left")
        self.docx_btn = tk.Button(out, text="Atidaryti Word", command=lambda: self.open_out("docx"), font=("Segoe UI", 10), state="disabled", padx=10)
        self.docx_btn.pack(side="left", padx=8)
        tk.Label(out, text="Atsakymai automatiškai išsaugomi šalia dokumento (TXT/Word/PDF).", bg=BG, fg="#777", font=("Segoe UI", 9)).pack(side="right")

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="Pasirinkite dokumentą",
            filetypes=[("Dokumentai", "*.pdf *.docx *.txt *.md"), ("Visi failai", "*.*")],
        )
        if path:
            self.file_path = path
            self.file_lbl.config(text=path, fg="#111")

    def set_busy(self, busy):
        self.running = busy
        state = "disabled" if busy else "normal"
        for b in (self.analyze_btn, self.draft_btn, self.pick_btn):
            b.config(state=state)

    def start(self, task):
        if not self.file_path:
            messagebox.showwarning("Nieko nėra", "Pirmiausia pasirinkite dokumentą.")
            return
        if not config.get_api_key():
            messagebox.showerror("Nėra API rakto", "Įrašykite LLM API raktą paleisdami setup_key.py.")
            return
        self.set_busy(True)
        self.pdf_btn.config(state="disabled")
        self.docx_btn.config(state="disabled")
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")
        self.status.config(text="Įkeliama dokumentą…")

        def work():
            try:
                text = ingest.extract_text(self.file_path)
                self.q.put(("status", "Ieškoma taikytinų teisės normų…"))
                provisions = corpus.retrieve(text, 6)
                self.q.put(("status", f"Rastos {len(provisions)} normos. Kreipiamasi į LLM (gali užtrukti)…"))
                answer = llm.analyze(text, provisions, task=task)
                base = Path(self.file_path).with_name(Path(self.file_path).stem + "-atsakymas")
                _txt, docx, pdf = draft.save_answer(answer, base)
                self.q.put(("done", answer, str(pdf), str(docx)))
            except Exception as e:  # noqa: BLE001 — rodome vartotojui bet kokią klaidą
                self.q.put(("error", str(e)))

        threading.Thread(target=work, daemon=True).start()
        self.poll()

    def poll(self):
        try:
            while True:
                msg = self.q.get_nowait()
                kind = msg[0]
                if kind == "status":
                    self.status.config(text=msg[1])
                elif kind == "done":
                    _, answer, pdf, docx = msg
                    self.out_pdf, self.out_docx = pdf, docx
                    self.text.config(state="normal")
                    self.text.delete("1.0", "end")
                    self.text.insert("1.0", answer)
                    self.text.config(state="disabled")
                    self.pdf_btn.config(state="normal")
                    self.docx_btn.config(state="normal")
                    self.status.config(text="Baigta. Atsakymas išsaugotas TXT/Word/PDF.")
                    self.set_busy(False)
                elif kind == "error":
                    self.text.config(state="normal")
                    self.text.delete("1.0", "end")
                    self.text.insert("1.0", "Klaida: " + msg[1])
                    self.text.config(state="disabled")
                    self.status.config(text="Įvyko klaida.")
                    self.set_busy(False)
        except queue.Empty:
            pass
        if self.running:
            self.root.after(100, self.poll)

    def open_out(self, kind):
        path = self.out_pdf if kind == "pdf" else self.out_docx
        if path and Path(path).exists():
            os.startfile(path)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()