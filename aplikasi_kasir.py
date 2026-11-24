import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import os

FILE_DATA = "data_barang.json"

# 1. TUPLE: Data konstanta yang tidak berubah (Kategori Barang & Aturan Diskon)
KATEGORI_BARANG = ("Sembako", "Makanan & Minuman", "ATK", "Elektronik", "Lainnya")
# Format tuple: (minimal_belanja, persentase_diskon)
ATURAN_DISKON = (100000, 0.10)  # Diskon 10% jika belanja >= Rp 100.000


def muat_data_dari_file():
    """Membaca data barang dari file JSON. Jika belum ada, buat file JSON kosong."""
    if os.path.exists(FILE_DATA):
        try:
            with open(FILE_DATA, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    # Buat file data_barang.json baru dengan isi kosong []
    simpan_data_ke_file([])
    return []


def simpan_data_ke_file(data):
    """Menyimpan perubahan list daftar_barang ke file JSON secara otomatis."""
    try:
        with open(FILE_DATA, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        messagebox.showerror("Gagal Menyimpan", f"Tidak dapat menyimpan data ke file: {e}")


# 2. LIST berisi DICTIONARY: Memuat master data barang dari penyimpanan lokal
daftar_barang = muat_data_dari_file()

# List berisi Dictionary untuk keranjang belanja kasir saat ini
keranjang_belanja = []


def format_rupiah(nominal):
    """Mengubah angka integer menjadi format mata uang Rupiah."""
    return f"Rp {int(nominal):,}".replace(",", ".")


def cari_indeks_barang(data, kode):
    """Mencari posisi indeks barang berdasarkan kode. Mengembalikan -1 jika tidak ada."""
    for indeks, barang in enumerate(data):
        if barang["kode"].lower() == kode.lower():
            return indeks
    return -1


def validasi_data_barang(kode, nama, kategori, harga_str, stok_str):
    """
    Pengkondisian & Error Handling: Memastikan input barang valid sebelum disimpan.
    """
    if not kode or not nama or not kategori:
        raise ValueError("Kode, Nama Barang, dan Kategori wajib diisi!")

    try:
        harga = int(harga_str)
        stok = int(stok_str)
    except ValueError:
        raise ValueError("Harga dan Stok harus berupa angka bulat!")

    if harga <= 0:
        raise ValueError("Harga barang harus lebih dari Rp 0!")
    if stok < 0:
        raise ValueError("Stok barang tidak boleh bernilai negatif!")

    return harga, stok


# --- FUNGSI 1: Menambah Data Barang ---
def tambah_barang(data, kode, nama, kategori, harga_str, stok_str):
    """Menambahkan item baru ke dalam list daftar_barang."""
    harga, stok = validasi_data_barang(kode, nama, kategori, harga_str, stok_str)

    if cari_indeks_barang(data, kode) != -1:
        raise ValueError(f"Kode barang '{kode.upper()}' sudah terdaftar!")

    data.append({
        "kode": kode.upper(),
        "nama": nama,
        "kategori": kategori,
        "harga": harga,
        "stok": stok
    })
    simpan_data_ke_file(data)


# --- FUNGSI 2: Mengubah Data Barang ---
def ubah_barang(data, kode_lama, kode_baru, nama, kategori, harga_str, stok_str):
    """Memperbarui data barang yang dipilih di daftar_barang."""
    harga, stok = validasi_data_barang(kode_baru, nama, kategori, harga_str, stok_str)

    indeks = cari_indeks_barang(data, kode_lama)
    if indeks == -1:
        raise ValueError("Barang yang akan diubah tidak ditemukan!")

    if kode_baru.lower() != kode_lama.lower() and cari_indeks_barang(data, kode_baru) != -1:
        raise ValueError(f"Kode barang '{kode_baru.upper()}' sudah digunakan barang lain!")

    data[indeks] = {
        "kode": kode_baru.upper(),
        "nama": nama,
        "kategori": kategori,
        "harga": harga,
        "stok": stok
    }
    simpan_data_ke_file(data)


# --- FUNGSI 3: Menghapus Data Barang ---
def hapus_barang(data, kode):
    """Menghapus data barang dari daftar_barang."""
    indeks = cari_indeks_barang(data, kode)
    if indeks == -1:
        raise ValueError("Pilih barang yang valid untuk dihapus!")
    data.pop(indeks)
    simpan_data_ke_file(data)


# --- FUNGSI 4: Menghitung Total, Diskon, dan Kembalian ---
def hitung_ringkasan_transaksi(keranjang):
    """
    Menghitung subtotal, diskon otomatis (menggunakan TUPLE ATURAN_DISKON),
    dan total akhir yang harus dibayar pembeli.
    """
    subtotal = sum(item["subtotal"] for item in keranjang)
    min_belanja, persen_diskon = ATURAN_DISKON  # Unpacking tuple

    # Pengkondisian untuk pemberian diskon
    if subtotal >= min_belanja:
        diskon = int(subtotal * persen_diskon)
    else:
        diskon = 0

    total_akhir = subtotal - diskon
    return subtotal, diskon, total_akhir


# --- FUNGSI 5: Menambah ke Keranjang & Sinkronisasi Stok ---
def tambah_ke_keranjang(data_master, keranjang, kode, jumlah_str):
    """Memvalidasi stok barang dan memasukkannya ke keranjang belanja."""
    if not kode:
        raise ValueError("Pilih barang terlebih dahulu!")

    try:
        jumlah = int(jumlah_str)
    except ValueError:
        raise ValueError("Jumlah beli harus berupa angka bulat!")

    if jumlah <= 0:
        raise ValueError("Jumlah beli minimal 1 unit!")

    indeks_master = cari_indeks_barang(data_master, kode)
    if indeks_master == -1:
        raise ValueError("Data barang tidak ditemukan!")

    barang = data_master[indeks_master]

    # Cek jumlah yang sudah ada di keranjang agar tidak melebihi stok master
    indeks_keranjang = cari_indeks_barang(keranjang, kode)
    jumlah_di_keranjang = keranjang[indeks_keranjang]["jumlah"] if indeks_keranjang != -1 else 0

    if jumlah + jumlah_di_keranjang > barang["stok"]:
        sisa = barang["stok"] - jumlah_di_keranjang
        raise ValueError(f"Stok tidak mencukupi! Sisa stok tersedia: {sisa}")

    if indeks_keranjang != -1:
        keranjang[indeks_keranjang]["jumlah"] += jumlah
        keranjang[indeks_keranjang]["subtotal"] = (
            keranjang[indeks_keranjang]["jumlah"] * barang["harga"]
        )
    else:
        keranjang.append({
            "kode": barang["kode"],
            "nama": barang["nama"],
            "harga": barang["harga"],
            "jumlah": jumlah,
            "subtotal": barang["harga"] * jumlah
        })


# -- ANTARMUKA PENGGUNA (GUI TKINTER) --

class AplikasiKasir:
    def __init__(self, root):
        self.root = root
        self.root.title("Kasir Sederhana")
        self.root.geometry("980x780")
        self.root.minsize(900, 620)

        # Palet warna modern
        self.warna = {
            "bg": "#F1F5F9",
            "kartu": "#FFFFFF",
            "header": "#0F172A",
            "aksen": "#2563EB",
            "aksen_hover": "#1D4ED8",
            "sukses": "#10B981",
            "sukses_hover": "#059669",
            "peringatan": "#F59E0B",
            "peringatan_hover": "#D97706",
            "bahaya": "#EF4444",
            "bahaya_hover": "#DC2626",
            "netral": "#64748B",
            "netral_hover": "#475569",
            "border": "#CBD5E1",
            "teks": "#1E293B"
        }

        self.root.configure(bg=self.warna["bg"])
        self.atur_tema()
        self.buat_header()
        self.buat_tabs()
        self.muat_ulang_semua_data()

    def atur_tema(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TNotebook", background=self.warna["bg"], borderwidth=0)
        style.configure("TNotebook.Tab",
                        background="#E2E8F0",
                        foreground=self.warna["teks"],
                        padding=[18, 8],
                        font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", self.warna["aksen"])],
                  foreground=[("selected", "#FFFFFF")])

        style.configure("Kartu.TLabelframe",
                        background=self.warna["kartu"],
                        bordercolor=self.warna["border"],
                        relief="solid",
                        borderwidth=1)
        style.configure("Kartu.TLabelframe.Label",
                        background=self.warna["kartu"],
                        foreground=self.warna["header"],
                        font=("Segoe UI", 10, "bold"))

        style.configure("Kartu.TLabel",
                        background=self.warna["kartu"],
                        foreground="#475569",
                        font=("Segoe UI", 9, "bold"))

        style.configure("Treeview",
                        background="#FFFFFF",
                        foreground=self.warna["teks"],
                        rowheight=28,
                        fieldbackground="#FFFFFF",
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                        background=self.warna["header"],
                        foreground="#FFFFFF",
                        padding=6,
                        font=("Segoe UI", 9, "bold"))
        style.map("Treeview",
                  background=[("selected", "#DBEAFE")],
                  foreground=[("selected", self.warna["header"])])

    def buat_tombol(self, parent, teks, perintah, bg, hover):
        btn = tk.Button(
            parent, text=teks, command=perintah,
            bg=bg, fg="#FFFFFF", activebackground=hover, activeforeground="#FFFFFF",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", padx=14, pady=6
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=hover))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    def buat_header(self):
        header = tk.Frame(self.root, bg=self.warna["header"], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="🛒  SISTEM KASIR & INVENTARIS TOKO",
            bg=self.warna["header"], fg="#FFFFFF", font=("Segoe UI", 14, "bold")
        ).pack(side="left", padx=20)

        tk.Label(
            header, text="Data Barang",
            bg=self.warna["header"], fg="#94A3B8", font=("Segoe UI", 9)
        ).pack(side="right", padx=20)

    def buat_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=12)

        self.tab_kasir = tk.Frame(self.notebook, bg=self.warna["bg"])
        self.tab_barang = tk.Frame(self.notebook, bg=self.warna["bg"])

        # Tab Kasir diletakkan pertama agar langsung siap transaksi
        self.notebook.add(self.tab_kasir, text="  💳 Kasir Transaksi  ")
        self.notebook.add(self.tab_barang, text="  📦 Data Barang  ")

        self.bangun_ui_kasir()
        self.bangun_ui_barang()

    # -- UI KASIR TRANSAKSI --
    def bangun_ui_kasir(self):
        # Panel Atas: Pilih Barang & Jumlah
        panel_pilih = ttk.LabelFrame(self.tab_kasir, text="  Input Transaksi Penjualan  ", style="Kartu.TLabelframe")
        panel_pilih.pack(fill="x", padx=5, pady=(8, 6))

        self.var_pilih_barang = tk.StringVar()
        self.var_jumlah_beli = tk.StringVar(value="1")

        ttk.Label(panel_pilih, text="Pilih Barang (Kode - Nama | Stok):", style="Kartu.TLabel").grid(
            row=0, column=0, padx=10, pady=(10, 2), sticky="w")
        self.combo_barang = ttk.Combobox(
            panel_pilih, textvariable=self.var_pilih_barang, state="readonly", width=45, font=("Segoe UI", 9)
        )
        self.combo_barang.grid(row=1, column=0, padx=10, pady=(0, 12))

        ttk.Label(panel_pilih, text="Jumlah Beli:", style="Kartu.TLabel").grid(
            row=0, column=1, padx=10, pady=(10, 2), sticky="w")
        ttk.Entry(panel_pilih, textvariable=self.var_jumlah_beli, width=12, font=("Segoe UI", 9)).grid(
            row=1, column=1, padx=10, pady=(0, 12))

        self.buat_tombol(
            panel_pilih, "Tambah ke Keranjang", self.aksi_tambah_keranjang,
            self.warna["aksen"], self.warna["aksen_hover"]
        ).grid(row=1, column=2, padx=10, pady=(0, 12))

        self.buat_tombol(
            panel_pilih, "Hapus Item", self.aksi_hapus_item_keranjang,
            self.warna["bahaya"], self.warna["bahaya_hover"]
        ).grid(row=1, column=3, padx=5, pady=(0, 12))

        # Panel Tengah: Tabel Keranjang Belanja
        frame_tabel = tk.Frame(self.tab_kasir, bg=self.warna["kartu"], highlightbackground=self.warna["border"], highlightthickness=1)
        frame_tabel.pack(fill="both", expand=True, padx=5, pady=6)

        kolom_keranjang = ("Kode", "Nama Barang", "Harga Satuan", "Jumlah", "Subtotal")
        self.tabel_keranjang = ttk.Treeview(frame_tabel, columns=kolom_keranjang, show="headings", selectmode="browse")

        lebar_k = {"Kode": 90, "Nama Barang": 280, "Harga Satuan": 150, "Jumlah": 90, "Subtotal": 160}
        for k in kolom_keranjang:
            self.tabel_keranjang.heading(k, text=k)
            anchor = "center" if k in ("Kode", "Jumlah") else ("e" if k in ("Harga Satuan", "Subtotal") else "w")
            self.tabel_keranjang.column(k, width=lebar_k[k], anchor=anchor)

        scroll_k = ttk.Scrollbar(frame_tabel, orient="vertical", command=self.tabel_keranjang.yview)
        self.tabel_keranjang.configure(yscrollcommand=scroll_k.set)
        self.tabel_keranjang.pack(side="left", fill="both", expand=True)
        scroll_k.pack(side="right", fill="y")

        # Panel Bawah: Ringkasan Total & Pembayaran
        panel_bayar = ttk.LabelFrame(self.tab_kasir, text="  Ringkasan & Pembayaran  ", style="Kartu.TLabelframe")
        panel_bayar.pack(fill="x", padx=5, pady=(6, 5))

        # Kiri: Rincian Subtotal, Diskon, Total
        frame_rincian = tk.Frame(panel_bayar, bg=self.warna["kartu"])
        frame_rincian.pack(side="left", padx=15, pady=10)

        self.lbl_subtotal = tk.Label(frame_rincian, text="Subtotal : Rp 0", bg=self.warna["kartu"], fg="#475569", font=("Segoe UI", 10))
        self.lbl_subtotal.pack(anchor="w")

        self.lbl_diskon = tk.Label(frame_rincian, text="Diskon (10% min. Rp 100.000) : Rp 0", bg=self.warna["kartu"], fg=self.warna["sukses"], font=("Segoe UI", 10, "bold"))
        self.lbl_diskon.pack(anchor="w", pady=2)

        self.lbl_total = tk.Label(frame_rincian, text="TOTAL BAYAR : Rp 0", bg=self.warna["kartu"], fg=self.warna["header"], font=("Segoe UI", 14, "bold"))
        self.lbl_total.pack(anchor="w", pady=(4, 0))

        # Kanan: Input Uang Tunai & Tombol Bayar
        frame_tunai = tk.Frame(panel_bayar, bg=self.warna["kartu"])
        frame_tunai.pack(side="right", padx=15, pady=10)

        tk.Label(frame_tunai, text="Uang Tunai (Rp):", bg=self.warna["kartu"], fg="#475569", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=5)

        self.var_uang_bayar = tk.StringVar()
        ttk.Entry(frame_tunai, textvariable=self.var_uang_bayar, width=20, font=("Segoe UI", 11)).grid(
            row=1, column=0, padx=5, pady=5)

        self.buat_tombol(
            frame_tunai, "✅ Proses Bayar & Cetak Struk", self.aksi_proses_bayar,
            self.warna["sukses"], self.warna["sukses_hover"]
        ).grid(row=1, column=1, padx=8, pady=5)

        self.buat_tombol(
            frame_tunai, "🔄 Reset Keranjang", self.aksi_reset_keranjang,
            self.warna["netral"], self.warna["netral_hover"]
        ).grid(row=1, column=2, padx=5, pady=5)

    # -- UI DATA MASTER BARANG --
    def bangun_ui_barang(self):
        panel_form = ttk.LabelFrame(self.tab_barang, text="  Kelola Data Barang  ", style="Kartu.TLabelframe")
        panel_form.pack(fill="x", padx=5, pady=(8, 6))

        self.var_kode = tk.StringVar()
        self.var_nama = tk.StringVar()
        self.var_kategori = tk.StringVar(value=KATEGORI_BARANG[0])
        self.var_harga = tk.StringVar()
        self.var_stok = tk.StringVar()

        ttk.Label(panel_form, text="Kode Barang", style="Kartu.TLabel").grid(row=0, column=0, padx=8, pady=(8, 2), sticky="w")
        ttk.Entry(panel_form, textvariable=self.var_kode, width=14).grid(row=1, column=0, padx=8, pady=(0, 10))

        ttk.Label(panel_form, text="Nama Barang", style="Kartu.TLabel").grid(row=0, column=1, padx=8, pady=(8, 2), sticky="w")
        ttk.Entry(panel_form, textvariable=self.var_nama, width=28).grid(row=1, column=1, padx=8, pady=(0, 10))

        ttk.Label(panel_form, text="Kategori", style="Kartu.TLabel").grid(row=0, column=2, padx=8, pady=(8, 2), sticky="w")
        ttk.Combobox(panel_form, textvariable=self.var_kategori, values=KATEGORI_BARANG,
                     state="readonly", width=18).grid(row=1, column=2, padx=8, pady=(0, 10))

        ttk.Label(panel_form, text="Harga Jual (Rp)", style="Kartu.TLabel").grid(row=0, column=3, padx=8, pady=(8, 2), sticky="w")
        ttk.Entry(panel_form, textvariable=self.var_harga, width=16).grid(row=1, column=3, padx=8, pady=(0, 10))

        ttk.Label(panel_form, text="Stok Tersedia", style="Kartu.TLabel").grid(row=0, column=4, padx=8, pady=(8, 2), sticky="w")
        ttk.Entry(panel_form, textvariable=self.var_stok, width=12).grid(row=1, column=4, padx=8, pady=(0, 10))

        frame_btn = tk.Frame(panel_form, bg=self.warna["kartu"])
        frame_btn.grid(row=2, column=0, columnspan=5, pady=(0, 12))

        self.buat_tombol(frame_btn, "Tambah Barang", self.aksi_tambah_barang, self.warna["sukses"], self.warna["sukses_hover"]).pack(side="left", padx=5)
        self.buat_tombol(frame_btn, "Ubah Data", self.aksi_ubah_barang, self.warna["peringatan"], self.warna["peringatan_hover"]).pack(side="left", padx=5)
        self.buat_tombol(frame_btn, "Hapus Barang", self.aksi_hapus_barang, self.warna["bahaya"], self.warna["bahaya_hover"]).pack(side="left", padx=5)
        self.buat_tombol(frame_btn, "Bersihkan Form", self.bersihkan_form_barang, self.warna["netral"], self.warna["netral_hover"]).pack(side="left", padx=5)

        # Tabel Master Barang
        frame_tabel_b = tk.Frame(self.tab_barang, bg=self.warna["kartu"], highlightbackground=self.warna["border"], highlightthickness=1)
        frame_tabel_b.pack(fill="both", expand=True, padx=5, pady=6)

        kolom_b = ("Kode", "Nama Barang", "Kategori", "Harga", "Stok")
        self.tabel_barang = ttk.Treeview(frame_tabel_b, columns=kolom_b, show="headings", selectmode="browse")

        lebar_b = {"Kode": 90, "Nama Barang": 280, "Kategori": 170, "Harga": 150, "Stok": 90}
        for k in kolom_b:
            self.tabel_barang.heading(k, text=k)
            anchor = "center" if k in ("Kode", "Stok") else ("e" if k == "Harga" else "w")
            self.tabel_barang.column(k, width=lebar_b[k], anchor=anchor)

        scroll_b = ttk.Scrollbar(frame_tabel_b, orient="vertical", command=self.tabel_barang.yview)
        self.tabel_barang.configure(yscrollcommand=scroll_b.set)
        self.tabel_barang.pack(side="left", fill="both", expand=True)
        scroll_b.pack(side="right", fill="y")

        self.tabel_barang.bind("<<TreeviewSelect>>", self.pilih_baris_barang)

        # Status Bar Inventaris
        self.lbl_status_barang = tk.Label(
            self.tab_barang, anchor="w", bg=self.warna["header"], fg="#FFFFFF",
            font=("Segoe UI", 9, "bold"), padx=12, pady=7
        )
        self.lbl_status_barang.pack(fill="x", padx=5, pady=(2, 5))

    # -- SINKRONISASI DATA ANTARA TABEL BARANG & KASIR --
    def muat_ulang_semua_data(self):
        """Memperbarui tabel barang, dropdown kasir, dan tabel keranjang secara bersamaan."""
        # 1. Refresh Tabel Master Barang
        for item in self.tabel_barang.get_children():
            self.tabel_barang.delete(item)

        pilihan_dropdown = []
        for b in daftar_barang:
            self.tabel_barang.insert("", "end", iid=b["kode"], values=(
                b["kode"], b["nama"], b["kategori"], format_rupiah(b["harga"]), b["stok"]
            ))
            # Hanya tampilkan di dropdown kasir jika stok > 0
            if b["stok"] > 0:
                pilihan_dropdown.append(
                    f"{b['kode']} - {b['nama']} ({format_rupiah(b['harga'])} | Stok: {b['stok']})"
                )

        # 2. Update Dropdown di Tab Kasir agar selalu sinkron dengan Data Barang
        self.combo_barang["values"] = pilihan_dropdown
        if pilihan_dropdown:
            self.combo_barang.current(0)
        else:
            self.var_pilih_barang.set("")

        # Update status bar inventaris
        total_jenis = len(daftar_barang)
        total_stok = sum(b["stok"] for b in daftar_barang)
        total_aset = sum(b["harga"] * b["stok"] for b in daftar_barang)
        self.lbl_status_barang.config(
            text=f"Jenis Barang: {total_jenis}   |   Total Stok Gudang: {total_stok}   |   "
                 f"Total Nilai Aset: {format_rupiah(total_aset)}"
        )

        # 3. Refresh Tabel Keranjang Kasir
        for item in self.tabel_keranjang.get_children():
            self.tabel_keranjang.delete(item)

        for k in keranjang_belanja:
            self.tabel_keranjang.insert("", "end", iid=k["kode"], values=(k["kode"], k["nama"], format_rupiah(k["harga"]), k["jumlah"], format_rupiah(k["subtotal"])))

        subtotal, diskon, total_akhir = hitung_ringkasan_transaksi(keranjang_belanja)
        self.lbl_subtotal.config(text=f"Subtotal : {format_rupiah(subtotal)}")
        self.lbl_diskon.config(text=f"Diskon (10% min. Rp 100.000) : -{format_rupiah(diskon)}")
        self.lbl_total.config(text=f"TOTAL BAYAR : {format_rupiah(total_akhir)}")

    # -- TOMBOL AKSI PADA DATA BARANG --
    def bersihkan_form_barang(self):
        self.var_kode.set("")
        self.var_nama.set("")
        self.var_kategori.set(KATEGORI_BARANG[0])
        self.var_harga.set("")
        self.var_stok.set("")
        self.tabel_barang.selection_remove(self.tabel_barang.selection())

    def pilih_baris_barang(self, event=None):
        terpilih = self.tabel_barang.selection()
        if not terpilih:
            return
        indeks = cari_indeks_barang(daftar_barang, terpilih[0])
        if indeks != -1:
            b = daftar_barang[indeks]
            self.var_kode.set(b["kode"])
            self.var_nama.set(b["nama"])
            self.var_kategori.set(b["kategori"])
            self.var_harga.set(b["harga"])
            self.var_stok.set(b["stok"])

    def aksi_tambah_barang(self):
        try:
            tambah_barang(
                daftar_barang,
                self.var_kode.get().strip(),
                self.var_nama.get().strip(),
                self.var_kategori.get().strip(),
                self.var_harga.get().strip(),
                self.var_stok.get().strip()
            )
            self.bersihkan_form_barang()
            self.muat_ulang_semua_data()
            messagebox.showinfo("Berhasil", "Data barang berhasil ditambahkan")
        except ValueError as e:
            messagebox.showerror("Input Tidak Valid", str(e))

    def aksi_ubah_barang(self):
        terpilih = self.tabel_barang.selection()
        if not terpilih:
            messagebox.showwarning("Peringatan", "Pilih baris barang pada tabel terlebih dahulu!")
            return
        try:
            ubah_barang(
                daftar_barang,
                terpilih[0],
                self.var_kode.get().strip(),
                self.var_nama.get().strip(),
                self.var_kategori.get().strip(),
                self.var_harga.get().strip(),
                self.var_stok.get().strip()
            )
            self.bersihkan_form_barang()
            self.muat_ulang_semua_data()
            messagebox.showinfo("Sukses", "Data barang berhasil diperbarui!")
        except ValueError as e:
            messagebox.showerror("Input Tidak Valid", str(e))

    def aksi_hapus_barang(self):
        terpilih = self.tabel_barang.selection()
        if not terpilih:
            messagebox.showwarning("Peringatan", "Pilih barang yang akan dihapus!")
            return
        kode = terpilih[0]
        if messagebox.askyesno("Konfirmasi Hapus", f"Yakin ingin menghapus barang '{kode}'?"):
            try:
                hapus_barang(daftar_barang, kode)
                self.bersihkan_form_barang()
                self.muat_ulang_semua_data()
            except ValueError as e:
                messagebox.showerror("Error", str(e))

    # -- TOMBOL AKSI PADA KASIR TRANSAKSI --
    def aksi_tambah_keranjang(self):
        pilihan = self.var_pilih_barang.get()
        if not pilihan:
            messagebox.showwarning("Stok Kosong", "Tidak ada barang yang tersedia untuk dijual.")
            return

        # Mengambil kode barang dari format "B001 - Beras 5 Kg (...)"
        kode_barang = pilihan.split(" - ")[0].strip()

        try:
            tambah_ke_keranjang(daftar_barang, keranjang_belanja, kode_barang, self.var_jumlah_beli.get().strip())
            self.var_jumlah_beli.set("1")
            self.muat_ulang_semua_data()
        except ValueError as e:
            messagebox.showerror("Gagal Menambah Item", str(e))

    def aksi_hapus_item_keranjang(self):
        terpilih = self.tabel_keranjang.selection()
        if not terpilih:
            messagebox.showwarning("Peringatan", "Pilih item di keranjang yang ingin dihapus!")
            return
        hapus_barang(keranjang_belanja, terpilih[0])
        self.muat_ulang_semua_data()

    def aksi_reset_keranjang(self):
        keranjang_belanja.clear()
        self.var_uang_bayar.set("")
        self.muat_ulang_semua_data()

    def aksi_proses_bayar(self):
        if not keranjang_belanja:
            messagebox.showwarning("Keranjang Kosong", "Tambahkan minimal 1 barang ke keranjang terlebih dahulu!")
            return

        subtotal, diskon, total_akhir = hitung_ringkasan_transaksi(keranjang_belanja)

        # Validasi pembayaran dengan try-except & pengkondisian
        try:
            uang_tunai = int(self.var_uang_bayar.get().strip())
        except ValueError:
            messagebox.showerror("Input Tidak Valid", "Masukkan nominal uang tunai dalam angka bulat!")
            return

        if uang_tunai < total_akhir:
            kurang = total_akhir - uang_tunai
            messagebox.showerror("Pembayaran Kurang", f"Uang tunai kurang sebesar {format_rupiah(kurang)}!")
            return

        kembalian = uang_tunai - total_akhir
        # SINKRONISASI OTOMATIS: Kurangi stok pada daftar_barang master & simpan permanen
        for item_beli in keranjang_belanja:
            indeks = cari_indeks_barang(daftar_barang, item_beli["kode"])
            if indeks != -1:
                daftar_barang[indeks]["stok"] -= item_beli["jumlah"]
        simpan_data_ke_file(daftar_barang)

        # Tampilkan Struk Pembayaran
        waktu_skrg = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        rincian_struk = "\n".join(
            [f"- {i['nama']} ({i['jumlah']}x) = {format_rupiah(i['subtotal'])}" for i in keranjang_belanja]
        )
        pesan_struk = (
            f"========= STRUK PEMBAYARAN =========\n"
            f"Waktu : {waktu_skrg}\n"
            f"------------------------------------\n"
            f"{rincian_struk}\n"
            f"------------------------------------\n"
            f"Subtotal  : {format_rupiah(subtotal)}\n"
            f"Diskon    : -{format_rupiah(diskon)}\n"
            f"Total     : {format_rupiah(total_akhir)}\n"
            f"Tunai     : {format_rupiah(uang_tunai)}\n"
            f"Kembalian : {format_rupiah(kembalian)}\n"
            f"====================================\n"
            f"Stok barang di inventaris telah otomatis diperbarui!"
        )

        messagebox.showinfo("Transaksi Berhasil", pesan_struk)
        self.aksi_reset_keranjang()

# -- MENJALANKAN APLIKASI --
if __name__ == "__main__":
    root = tk.Tk()
    app = AplikasiKasir(root)
    root.mainloop()