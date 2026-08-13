import streamlit as st
import datetime
import json
import os
import secrets

st.set_page_config(page_title="Program Kas", page_icon="💰", layout="centered")

# --- Styling tambahan biar tampilan lebih rapi, terutama di HP ---
st.markdown("""
<style>
    div[data-testid="stForm"] {
        border: 1px solid #333;
        border-radius: 12px;
        padding: 1.2rem;
    }
    div[data-testid="stButton"] > button {
        border-radius: 8px;
    }
    .kartu-item {
        background-color: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.6rem;
    }
    .kartu-keterangan {
        font-size: 1.05rem;
        font-weight: 600;
    }
    .kartu-tanggal {
        font-size: 0.8rem;
        opacity: 0.6;
    }
    .kartu-jumlah {
        font-size: 1.1rem;
        font-weight: 700;
    }
    .warna-pengeluaran { color: #ff6b6b; }
    .warna-pemasukan { color: #51cf66; }

    /* --- Styling untuk laporan yang bisa dicetak --- */
    .laporan-tabel {
        width: 100%;
        border-collapse: collapse;
        margin-top: 1rem;
    }
    .laporan-tabel th, .laporan-tabel td {
        border: 1px solid #444;
        padding: 8px 10px;
        text-align: left;
    }
    .laporan-tabel th {
        background-color: rgba(255, 255, 255, 0.08);
    }
    .laporan-total-row td {
        font-weight: 700;
        border-top: 2px solid #888;
    }

    /* --- Saat mode print aktif, sembunyikan semua kecuali area laporan --- */
    @media print {
        header, div[data-testid="stHeader"], div[data-testid="stToolbar"],
        div[data-testid="stSidebar"], .stTabs [data-baseweb="tab-list"],
        div[data-testid="stForm"], div[data-testid="stButton"],
        .kartu-item {
            display: none !important;
        }
        .area-cetak, .area-cetak * {
            display: block !important;
        }
        .laporan-tabel, .laporan-tabel * {
            display: revert !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Daftar akun yang bisa login ---
USERS = {
    "ichal": "kasku123",
    "admin": "admin123",
}

BULAN_LIST = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

FILE_DATA = "data_kas.json"
FILE_TOKEN = "tokens.json"


def muat_data():
    if not os.path.exists(FILE_DATA):
        return []
    with open(FILE_DATA, "r", encoding="utf-8") as f:
        data_mentah = json.load(f)
    for item in data_mentah:
        item["tanggal"] = datetime.date.fromisoformat(item["tanggal"])
        # Data lama (sebelum fitur pemasukan ditambahkan) belum punya
        # field "jenis", jadi dianggap Pengeluaran secara default
        if "jenis" not in item:
            item["jenis"] = "Pengeluaran"
    return data_mentah


def simpan_data(data):
    data_untuk_simpan = []
    for item in data:
        salinan = dict(item)
        salinan["tanggal"] = item["tanggal"].isoformat()
        data_untuk_simpan.append(salinan)
    with open(FILE_DATA, "w", encoding="utf-8") as f:
        json.dump(data_untuk_simpan, f, ensure_ascii=False, indent=2)


def muat_token():
    if not os.path.exists(FILE_TOKEN):
        return {}
    with open(FILE_TOKEN, "r", encoding="utf-8") as f:
        return json.load(f)


def simpan_token(data_token):
    with open(FILE_TOKEN, "w", encoding="utf-8") as f:
        json.dump(data_token, f, ensure_ascii=False, indent=2)


def buat_token_baru(username):
    data_token = muat_token()
    token_baru = secrets.token_hex(16)
    data_token[token_baru] = username
    simpan_token(data_token)
    return token_baru


def hapus_token(token):
    data_token = muat_token()
    if token in data_token:
        del data_token[token]
        simpan_token(data_token)


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# --- Cek apakah ada token login yang valid di URL (misal setelah refresh) ---
if not st.session_state.logged_in:
    token_di_url = st.query_params.get("token")
    if token_di_url:
        data_token = muat_token()
        if token_di_url in data_token:
            st.session_state.logged_in = True
            st.session_state.username = data_token[token_di_url]

# --- Halaman login ---
if not st.session_state.logged_in:
    st.title("🔒 Login")
    st.write("Masukkan username dan password untuk mengakses Program Kas")

    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")
    login_button = st.button("Masuk", use_container_width=True)

    if login_button:
        if username_input in USERS and USERS[username_input] == password_input:
            st.session_state.logged_in = True
            st.session_state.username = username_input
            token_baru = buat_token_baru(username_input)
            st.query_params["token"] = token_baru
            st.rerun()
        else:
            st.error("Username atau password salah, coba lagi.")

    st.stop()

# --- Mulai dari sini, kode hanya jalan kalau sudah login ---

if "transaksi" not in st.session_state:
    st.session_state.transaksi = muat_data()

st.markdown("## 💰 Program Kas")
st.caption(f"Login sebagai **{st.session_state.username}**")

tab_tambah, tab_riwayat, tab_laporan = st.tabs(["➕ Tambah", "📋 Riwayat", "🖨️ Laporan"])

# --- TAB TAMBAH ---
with tab_tambah:
    with st.form("form_tambah", clear_on_submit=True):
        jenis = st.radio("Jenis Transaksi", ["Pengeluaran", "Pemasukan"], horizontal=True)
        keterangan = st.text_input("Keterangan")
        jumlah = st.number_input("Jumlah (Rp)", min_value=0, step=1000)
        tanggal = st.date_input(
            "Tanggal",
            value=datetime.date.today(),
            min_value=datetime.date(2000, 1, 1),
            max_value=datetime.date(2100, 12, 31),
        )

        submit = st.form_submit_button("Tambahkan", use_container_width=True)

        if submit:
            if keterangan == "":
                st.warning("Keterangan tidak boleh kosong.")
            else:
                nama_bulan = BULAN_LIST[tanggal.month - 1]
                st.session_state.transaksi.append({
                    "jenis": jenis,
                    "keterangan": keterangan,
                    "jumlah": jumlah,
                    "tanggal": tanggal,
                    "bulan": nama_bulan,
                    "tahun": tanggal.year,
                })
                simpan_data(st.session_state.transaksi)
                st.success(f"Tercatat ({jenis}): {keterangan} - Rp {jumlah:,.0f}")

# --- TAB RIWAYAT ---
with tab_riwayat:
    if len(st.session_state.transaksi) == 0:
        st.info("Belum ada transaksi yang dicatat.")
    else:
        tahun_tersedia = sorted(set(p["tahun"] for p in st.session_state.transaksi))

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_tahun = st.selectbox("Tahun", tahun_tersedia, index=len(tahun_tersedia) - 1)
        with col_f2:
            filter_bulan = st.selectbox("Bulan", ["Semua Bulan"] + BULAN_LIST)
        with col_f3:
            filter_jenis = st.selectbox("Jenis", ["Semua", "Pemasukan", "Pengeluaran"])

        urutan = sorted(
            enumerate(st.session_state.transaksi),
            key=lambda pasangan: pasangan[1]["tanggal"],
            reverse=True,
        )

        total_pemasukan = 0
        total_pengeluaran = 0
        ada_data = False

        for i, p in urutan:
            cocok_tahun = p["tahun"] == filter_tahun
            cocok_bulan = (filter_bulan == "Semua Bulan") or (p["bulan"] == filter_bulan)
            if not (cocok_tahun and cocok_bulan):
                continue
            if p["jenis"] == "Pemasukan":
                total_pemasukan += p["jumlah"]
            else:
                total_pengeluaran += p["jumlah"]
            ada_data = True

        if not ada_data:
            st.info("Tidak ada transaksi untuk periode ini.")
        else:
            saldo = total_pemasukan - total_pengeluaran
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Pemasukan", f"Rp {total_pemasukan:,.0f}")
            col_m2.metric("Pengeluaran", f"Rp {total_pengeluaran:,.0f}")
            col_m3.metric("Saldo", f"Rp {saldo:,.0f}")
            st.divider()

            for i, p in urutan:
                cocok_tahun = p["tahun"] == filter_tahun
                cocok_bulan = (filter_bulan == "Semua Bulan") or (p["bulan"] == filter_bulan)
                cocok_jenis = (filter_jenis == "Semua") or (p["jenis"] == filter_jenis)
                if not (cocok_tahun and cocok_bulan and cocok_jenis):
                    continue

                kelas_warna = "warna-pemasukan" if p["jenis"] == "Pemasukan" else "warna-pengeluaran"
                tanda = "+" if p["jenis"] == "Pemasukan" else "-"

                col_isi, col_hapus = st.columns([5, 1])
                with col_isi:
                    st.markdown(
                        '<div class="kartu-item">'
                        f'<div class="kartu-keterangan">{p["keterangan"]} '
                        f'<span style="font-size:0.75rem; opacity:0.6;">({p["jenis"]})</span></div>'
                        f'<div class="kartu-tanggal">{p["tanggal"].strftime("%d %B %Y")}</div>'
                        f'<div class="kartu-jumlah {kelas_warna}">{tanda} Rp {p["jumlah"]:,.0f}</div>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                with col_hapus:
                    if st.button("🗑️", key=f"hapus_{i}"):
                        st.session_state.transaksi.pop(i)
                        simpan_data(st.session_state.transaksi)
                        st.rerun()

    st.divider()
    if len(st.session_state.transaksi) > 0:
        if st.button("Hapus Semua Data", use_container_width=True):
            st.session_state.transaksi = []
            simpan_data(st.session_state.transaksi)
            st.rerun()

# --- TAB LAPORAN ---
with tab_laporan:
    if len(st.session_state.transaksi) == 0:
        st.info("Belum ada transaksi yang dicatat.")
    else:
        tahun_tersedia_l = sorted(set(p["tahun"] for p in st.session_state.transaksi))

        col_l1, col_l2 = st.columns(2)
        with col_l1:
            laporan_tahun = st.selectbox(
                "Tahun", tahun_tersedia_l, index=len(tahun_tersedia_l) - 1, key="laporan_tahun"
            )
        with col_l2:
            laporan_bulan = st.selectbox(
                "Bulan", ["Semua Bulan"] + BULAN_LIST, key="laporan_bulan"
            )

        data_laporan = [
            p for p in st.session_state.transaksi
            if p["tahun"] == laporan_tahun
            and (laporan_bulan == "Semua Bulan" or p["bulan"] == laporan_bulan)
        ]
        data_laporan = sorted(data_laporan, key=lambda p: p["tanggal"])

        if len(data_laporan) == 0:
            st.info("Tidak ada data untuk periode ini.")
        else:
            total_pemasukan_l = sum(p["jumlah"] for p in data_laporan if p["jenis"] == "Pemasukan")
            total_pengeluaran_l = sum(p["jumlah"] for p in data_laporan if p["jenis"] == "Pengeluaran")
            saldo_l = total_pemasukan_l - total_pengeluaran_l
            judul_periode = f"{laporan_bulan} {laporan_tahun}"

            if st.button("🖨️ Cetak / Simpan sebagai PDF", use_container_width=True):
                st.components.v1.html(
                    "<script>window.parent.print();</script>", height=0
                )

            baris_html = ""
            for p in data_laporan:
                tanda = "+" if p["jenis"] == "Pemasukan" else "-"
                baris_html += (
                    "<tr>"
                    f"<td>{p['tanggal'].strftime('%d %B %Y')}</td>"
                    f"<td>{p['keterangan']}</td>"
                    f"<td>{p['jenis']}</td>"
                    f"<td>{tanda} Rp {p['jumlah']:,.0f}</td>"
                    "</tr>"
                )

            html_laporan = (
                '<div class="area-cetak">'
                f'<h3>Laporan Keuangan - {judul_periode}</h3>'
                f'<p>Dicetak oleh: {st.session_state.username}</p>'
                '<table class="laporan-tabel">'
                '<thead><tr><th>Tanggal</th><th>Keterangan</th><th>Jenis</th><th>Jumlah</th></tr></thead>'
                f'<tbody>{baris_html}'
                '<tr class="laporan-total-row">'
                '<td colspan="3">Total Pemasukan</td>'
                f'<td>Rp {total_pemasukan_l:,.0f}</td>'
                '</tr>'
                '<tr class="laporan-total-row">'
                '<td colspan="3">Total Pengeluaran</td>'
                f'<td>Rp {total_pengeluaran_l:,.0f}</td>'
                '</tr>'
                '<tr class="laporan-total-row">'
                '<td colspan="3">Saldo</td>'
                f'<td>Rp {saldo_l:,.0f}</td>'
                '</tr>'
                '</tbody></table></div>'
            )
            st.markdown(html_laporan, unsafe_allow_html=True)

# --- Tombol logout ---
st.divider()
if st.button("Logout", use_container_width=True):
    token_di_url = st.query_params.get("token")
    if token_di_url:
        hapus_token(token_di_url)
    st.query_params.clear()
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()
