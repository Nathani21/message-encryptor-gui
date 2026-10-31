"""Message Encryptor: a small educational GUI for classic encodings.

Caesar, Reverse and Base64 are NOT secure encryption. The output stores the
algorithm and Caesar shift next to the message, so anyone can decode it.
"""

import base64, json, qrcode
from math import ceil

import customtkinter as ctk
from tkinter import filedialog, messagebox

# ---------------- Utility functions ---------------- #

def caesar_encrypt(message, shift):
    result = []
    for ch in message:
        if ch.isalpha() and ch.isascii():
            ascii_offset = ord("a") if ch.islower() else ord("A")
            result.append(chr((ord(ch) - ascii_offset + shift) % 26 + ascii_offset))
        else:
            result.append(ch)
    return "".join(result)


def caesar_decrypt(message, shift):
    return caesar_encrypt(message, -shift)


def reverse_encrypt(message):
    return message[::-1]


def reverse_decrypt(message):
    return message[::-1]


def base64_encrypt(message):
    return base64.b64encode(message.encode()).decode()


def base64_decrypt(message):
    try:
        return base64.b64decode(message.encode()).decode()
    except Exception:
        return None


# Strength heuristic (very simple)
def encryption_strength(message, algorithm, shift=None):
    # base score from length
    length = len(message)
    score = min(30, length)  # up to 30

    # character variety
    types = 0
    if any(c.islower() for c in message):
        types += 1
    if any(c.isupper() for c in message):
        types += 1
    if any(c.isdigit() for c in message):
        types += 1
    if any(not c.isalnum() for c in message):
        types += 1
    score += types * 10  # up to +40

    # algorithm bonus
    alg_bonus = {"Caesar": 10, "Reverse": 5, "Base64": 5}
    score += alg_bonus.get(algorithm, 0)

    # shift effect for Caesar (slightly)
    if algorithm == "Caesar" and shift is not None:
        score += min(10, abs(shift) % 26)

    # clamp to 0..100
    score = max(0, min(100, score))
    return score

def encrypt_message(message, algorithm, shift=None):
    """Return the Base64 JSON package for a message. Raises ValueError on bad input."""
    if algorithm == "Caesar":
        if shift is None:
            raise ValueError("Shift must be an integer")
        result = caesar_encrypt(message, shift)
        meta = {"alg": "Caesar", "shift": shift}
    elif algorithm == "Reverse":
        result = reverse_encrypt(message)
        meta = {"alg": "Reverse"}
    elif algorithm == "Base64":
        result = base64_encrypt(message)
        meta = {"alg": "Base64"}
    else:
        raise ValueError("Unknown algorithm selected")

    package = json.dumps({"msg": result, "meta": meta})
    return base64.b64encode(package.encode()).decode()


def decrypt_package(package_b64):
    """Return (text, algorithm, shift) from a package. Raises ValueError on bad input."""
    try:
        data = json.loads(base64.b64decode(package_b64).decode())
        enc_msg = data["msg"]
        meta = data.get("meta", {})
        if not isinstance(enc_msg, str) or not isinstance(meta, dict):
            raise ValueError
    except Exception:
        raise ValueError("Invalid encrypted package format")

    alg = meta.get("alg")
    shift = None
    if alg == "Caesar":
        try:
            shift = int(meta.get("shift", 0))
        except (TypeError, ValueError):
            raise ValueError("Package has an invalid Caesar shift")
        decrypted = caesar_decrypt(enc_msg, shift)
    elif alg == "Reverse":
        decrypted = reverse_decrypt(enc_msg)
    elif alg == "Base64":
        decrypted = base64_decrypt(enc_msg)
        if decrypted is None:
            raise ValueError("Package looks like Base64 but failed to decode")
    else:
        raise ValueError(f"Unknown algorithm in package: {alg}")
    return decrypted, alg, shift

# ---------------- GUI ---------------- #

ctk.set_appearance_mode("System")  # can be "Dark" or "Light" or "System"
ctk.set_default_color_theme("blue")

class MessageEncryptorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Message Encryptor")
        self.geometry("860x620")
        self.minsize(800, 590)

        # main frames
        self.header_frame = ctk.CTkFrame(self, corner_radius=8)
        self.header_frame.pack(padx=16, pady=(16, 8), fill="x")

        self.body_frame = ctk.CTkFrame(self, corner_radius=8)
        self.body_frame.pack(padx=16, pady=8, fill="both", expand=True)

        # header content
        self.title_label = ctk.CTkLabel(self.header_frame, text="Message Encryptor", font=ctk.CTkFont(size=22, weight="bold"))
        self.title_label.grid(row=0, column=0, sticky="w", padx=12, pady=12)

        self.appearance_option = ctk.CTkOptionMenu(self.header_frame, values=["System", "Light", "Dark"], command=self.change_appearance)
        self.appearance_option.set("System")
        self.appearance_option.grid(row=0, column=1, sticky="e", padx=8)

        # body layout: left (input) | right (controls + output)
        self.left_frame = ctk.CTkFrame(self.body_frame, corner_radius=6)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(12, 6), pady=12)

        self.right_frame = ctk.CTkFrame(self.body_frame, corner_radius=6, width=300)
        self.right_frame.pack(side="right", fill="y", padx=(6, 12), pady=12)

        # Input area
        self.input_label = ctk.CTkLabel(self.left_frame, text="Input:")
        self.input_label.pack(anchor="w", padx=8, pady=(8, 0))

        self.input_box = ctk.CTkTextbox(self.left_frame, width=420, height=140)
        self.input_box.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        # small buttons under input
        self.input_buttons_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.input_buttons_frame.pack(fill="x", padx=8)

        self.clear_input_btn = ctk.CTkButton(self.input_buttons_frame, text="Clear Input", width=120, command=self.clear_input)
        self.clear_input_btn.pack(side="left", padx=6, pady=6)

        # Controls (algorithm etc.)
        self.alg_label = ctk.CTkLabel(self.right_frame, text="Algorithm:")
        self.alg_label.pack(anchor="w", padx=12, pady=(12, 6))

        self.alg_option = ctk.CTkOptionMenu(self.right_frame, values=["Caesar", "Reverse", "Base64"], command=self.alg_changed)
        self.alg_option.set("Caesar")
        self.alg_option.pack(fill="x", padx=12)

        # shift control for Caesar
        self.shift_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.shift_frame.pack(fill="x", padx=12, pady=(8, 0))

        self.shift_label = ctk.CTkLabel(self.shift_frame, text="Shift (Caesar):")
        self.shift_label.pack(side="left")

        self.shift_spin = ctk.CTkEntry(self.shift_frame, width=80)
        self.shift_spin.insert(0, "3")
        self.shift_spin.pack(side="left", padx=8)

        # Encrypt / Decrypt buttons
        self.action_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=12, pady=(14, 0))

        self.encrypt_btn = ctk.CTkButton(self.action_frame, text="Encrypt", command=self.action_encrypt)
        self.encrypt_btn.pack(fill="x", pady=6)

        self.decrypt_btn = ctk.CTkButton(
            self.action_frame,
            text="Decrypt",
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90"),
            command=self.action_decrypt,
        )
        self.decrypt_btn.pack(fill="x", pady=(0, 6))

        # Output area
        self.output_label = ctk.CTkLabel(self.left_frame, text="Output:")
        self.output_label.pack(anchor="w", padx=8, pady=(12, 0))

        self.output_box = ctk.CTkTextbox(self.left_frame, width=420, height=140)
        self.output_box.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        # small buttons under output
        self.output_buttons_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.output_buttons_frame.pack(fill="x", padx=8)

        self.copy_btn = ctk.CTkButton(self.output_buttons_frame, text="Copy Output", width=120, command=self.copy_output)
        self.copy_btn.pack(side="left", padx=6, pady=6)

        self.clear_output_btn = ctk.CTkButton(self.output_buttons_frame, text="Clear Output", width=120, command=self.clear_output)
        self.clear_output_btn.pack(side="left", padx=6, pady=6)

        self.qr_btn = ctk.CTkButton(self.output_buttons_frame, text="Show QR", width=120, command=self.show_qr)
        self.qr_btn.pack(side="left", padx=6, pady=6)

        # Strength meter and log inside right frame
        self.strength_label = ctk.CTkLabel(self.right_frame, text="Complexity score (not real security):")
        self.strength_label.pack(anchor="w", padx=12, pady=(12, 6))

        self.strength_bar = ctk.CTkProgressBar(self.right_frame, width=240)
        self.strength_bar.set(0)
        self.strength_bar.pack(padx=12)

        self.strength_text = ctk.CTkLabel(self.right_frame, text="—")
        self.strength_text.pack(anchor="w", padx=12, pady=(6, 12))

        # Log box
        self.log_label = ctk.CTkLabel(self.right_frame, text="Log:")
        self.log_label.pack(anchor="w", padx=12)

        self.log_box = ctk.CTkTextbox(self.right_frame, height=110, width=260, state="normal")
        self.log_box.insert("0.0", "Ready.\n")
        self.log_box.configure(state="disabled")
        self.log_box.pack(padx=12, pady=(4, 12))

        # initial state
        self.alg_changed("Caesar")

    # ---------------- UI helper methods ---------------- #
    def change_appearance(self, choice):
        # choice will be one of System/Light/Dark
        ctk.set_appearance_mode(choice)

    def clear_input(self):
        self.input_box.delete("0.0", "end")

    def clear_output(self):
        self.output_box.delete("0.0", "end")

    def copy_output(self):
        txt = self.output_box.get("0.0", "end").strip()
        if not txt:
            messagebox.showinfo("Info", "Output is empty")
            return
        self.clipboard_clear()
        self.clipboard_append(txt)
        messagebox.showinfo("Copied", "Output copied to clipboard")

    def log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ---------------- Algorithm control ---------------- #
    def alg_changed(self, val):
        is_caesar = val == "Caesar"
        self.shift_spin.configure(state="normal" if is_caesar else "disabled")
        self.shift_label.configure(
            text_color=("gray10", "gray90") if is_caesar else ("gray60", "gray40")
        )

    # ---------------- Core actions ---------------- #
    def action_encrypt(self):
        raw = self.input_box.get("0.0", "end").rstrip('\n')
        if not raw.strip():
            messagebox.showerror("Error", "Please enter a message to encrypt")
            return

        algorithm = self.alg_option.get()
        shift = None
        if algorithm == "Caesar":
            try:
                shift = int(self.shift_spin.get())
            except ValueError:
                messagebox.showerror("Error", "Shift must be an integer")
                return

        try:
            package_b64 = encrypt_message(raw, algorithm, shift)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        self.output_box.delete("0.0", "end")
        self.output_box.insert("0.0", package_b64)

        # update strength meter
        try:
            strength = encryption_strength(raw, algorithm, shift)
        except Exception:
            strength = 0
        self.strength_bar.set(strength / 100.0)
        self.strength_text.configure(text=f"{ceil(strength)} / 100")

        # log
        self.log(f"Encrypted (alg={algorithm}) — {len(raw)} chars")

    def action_decrypt(self):
        package_b64 = self.input_box.get("0.0", "end").strip()
        if not package_b64:
            messagebox.showerror("Error", "Please paste an encrypted package into the input box")
            return

        try:
            decrypted, alg, shift = decrypt_package(package_b64)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        self.output_box.delete("0.0", "end")
        self.output_box.insert("0.0", decrypted)

        # update strength (based on decrypted text and algorithm)
        try:
            strength = encryption_strength(decrypted, alg, shift)
        except Exception:
            strength = 0
        self.strength_bar.set(strength / 100.0)
        self.strength_text.configure(text=f"{ceil(strength)} / 100")

        self.log(f"Decrypted (alg={alg}) — {len(decrypted)} chars")

    def show_qr(self):
        text = self.output_box.get("0.0", "end").strip()
        if not text:
            messagebox.showinfo("Info", "No output to convert to QR")
            return

        try:
            qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q)
            qr.add_data(text)
            qr.make(fit=True)
        except Exception:
            messagebox.showerror("Error", "Output is too long to fit in a QR code")
            return

        full_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        preview = full_img.copy()
        preview.thumbnail((400, 400))

        top = ctk.CTkToplevel(self)
        top.title("Encrypted QR Code")
        top.geometry(f"{preview.width + 40}x{preview.height + 100}")
        top.resizable(False, False)
        top.transient(self)

        ctk_img = ctk.CTkImage(light_image=preview, dark_image=preview, size=preview.size)
        ctk.CTkLabel(top, text="", image=ctk_img).pack(pady=10)

        def save_qr():
            path = filedialog.asksaveasfilename(
                parent=top,
                defaultextension=".png",
                initialfile="encrypted_qr.png",
                filetypes=[("PNG image", "*.png")],
            )
            if not path:
                return
            try:
                full_img.save(path)
                messagebox.showinfo("Saved", f"QR saved to {path}", parent=top)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save QR: {e}", parent=top)

        ctk.CTkButton(top, text="Save QR as PNG", command=save_qr).pack(pady=(8, 12))


if __name__ == '__main__':
    app = MessageEncryptorApp()
    app.mainloop()