import streamlit as st
import datetime
import json
import os

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
        color: #ff6b6b;
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


def muat_data():
    if not os.path.exists(FILE_DATA):
        return []
    with open(FILE_DATA, "r", encoding="utf-8") as f:
        data_mentah = json.load(f)
    for item in data_mentah:
        item["tanggal"] = datetime.date.fromisoformat(item["tanggal"])
    return data_mentah


def simpan_data(data):
    data_untuk_simpan = []
    for item in data:
        salinan = dict(item)
        salinan["tanggal"] = item["tanggal"].isoformat()
        data_untuk_simpan.append(salinan)
    with open(FILE_DATA, "w", encoding="utf-8") as f:
        json.dump(data_untuk_simpan, f, ensure_ascii=False, indent=2)


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

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
            st.rerun()
        else:
            st.error("Username atau password salah, coba lagi.")

    st.stop()

# --- Mulai dari sini, kode hanya jalan kalau sudah login ---

if "pengeluaran" not in st.session_state:
    st.session_state.pengeluaran = muat_data()

st.markdown("## 💰 Program Kas")
st.caption(f"Login sebagai **{st.session_state.username}**")

tab_tambah, tab_riwayat = st.tabs(["➕ Tambah", "📋 Riwayat"])

# --- TAB TAMBAH ---
with tab_tambah:
    with st.form("form_tambah", clear_on_submit=True):
        keterangan = st.text_input("Nama barang / keterangan")
        jumlah = st.number_input("Harga (Rp)", min_value=0, step=1000)
        tanggal = st.date_input(
            "Tanggal",
            value=datetime.date.today(),
            min_value=datetime.date(2000, 1, 1),
            max_value=datetime.date(2100, 12, 31),
        )

        submit = st.form_submit_button("Tambahkan", use_container_width=True)

        if submit:
            if keterangan == "":
                st.warning("Nama barang tidak boleh kosong.")
            else:
                nama_bulan = BULAN_LIST[tanggal.month - 1]
                st.session_state.pengeluaran.append({
                    "keterangan": keterangan,
                    "jumlah": jumlah,
                    "tanggal": tanggal,
                    "bulan": nama_bulan,
                    "tahun": tanggal.year,
                })
                simpan_data(st.session_state.pengeluaran)
                st.success(f"Tercatat: {keterangan} - Rp {jumlah:,.0f}")

# --- TAB RIWAYAT ---
with tab_riwayat:
    if len(st.session_state.pengeluaran) == 0:
        st.info("Belum ada pengeluaran yang dicatat.")
    else:
        tahun_tersedia = sorted(set(p["tahun"] for p in st.session_state.pengeluaran))

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_tahun = st.selectbox("Tahun", tahun_tersedia, index=len(tahun_tersedia) - 1)
        with col_f2:
            filter_bulan = st.selectbox("Bulan", ["Semua Bulan"] + BULAN_LIST)

        urutan = sorted(
            enumerate(st.session_state.pengeluaran),
            key=lambda pasangan: pasangan[1]["tanggal"],
            reverse=True,
        )

        total = 0
        ada_data = False

        for i, p in urutan:
            cocok_tahun = p["tahun"] == filter_tahun
            cocok_bulan = (filter_bulan == "Semua Bulan") or (p["bulan"] == filter_bulan)
            if not (cocok_tahun and cocok_bulan):
                continue
            total += p["jumlah"]
            ada_data = True

        if not ada_data:
            st.info("Tidak ada pengeluaran untuk periode ini.")
        else:
            st.metric(f"Total {filter_bulan} {filter_tahun}", f"Rp {total:,.0f}")
            st.divider()

            for i, p in urutan:
                cocok_tahun = p["tahun"] == filter_tahun
                cocok_bulan = (filter_bulan == "Semua Bulan") or (p["bulan"] == filter_bulan)
                if not (cocok_tahun and cocok_bulan):
                    continue

                col_isi, col_hapus = st.columns([5, 1])
                with col_isi:
                    st.markdown(f"""
                    <div class="kartu-item">
                        <div class="kartu-keterangan">{p['keterangan']}</div>
                        <div class="kartu-tanggal">{p['tanggal'].strftime('%d %B %Y')}</div>
                        <div class="kartu-jumlah">Rp {p['jumlah']:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_hapus:
                    if st.button("🗑️", key=f"hapus_{i}"):
                        st.session_state.pengeluaran.pop(i)
                        simpan_data(st.session_state.pengeluaran)
                        st.rerun()

    st.divider()
    if len(st.session_state.pengeluaran) > 0:
        if st.button("Hapus Semua Data", use_container_width=True):
            st.session_state.pengeluaran = []
            simpan_data(st.session_state.pengeluaran)
            st.rerun()

# --- Tombol logout ---
st.divider()
if st.button("Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()
