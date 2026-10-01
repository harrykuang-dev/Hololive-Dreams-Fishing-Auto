# Hololive Dreams Auto Fishing

[Masalah yang diketahui dan solusi sementara](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/docs/KNOWN_ISSUES.md)

[繁體中文](README.md) · [简体中文](README.zh-CN.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md)

Asisten memancing otomatis untuk **hololive Dreams** versi Windows. Aplikasi memakai pengenalan layar dan input mouse biasa untuk menangani sambaran, menarik ikan, hasil tangkapan, dan ronde berikutnya melalui antarmuka sederhana tanpa kalibrasi manual.

## Unduh

Buka [GitHub Releases](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/releases/latest) dan unduh `Hololive-Dreams-Fishing-Auto-v1.0.exe` dari lampiran rilis.

Satu EXE sudah berisi runtime dan aset ikon. Tidak perlu memasang Python atau menyalin file tambahan. File checksum SHA-256 juga tersedia; ZIP kode sumber bukan aplikasi siap jalan.

## Fitur

- Mengenali tanda sambaran serta melacak ikan dan zona tangkapan saat menarik ikan.
- Menangani tombol Lanjut / Berikutnya serta menutup koleksi atau pop-up item untuk melanjutkan memancing.
- Enam bahasa antarmuka: 繁體中文, 简体中文, English, 日本語, 한국어, dan Indonesian. Pilihan ini mengubah bahasa asisten, bukan bahasa game.
- Penghitung tangkapan terkonfirmasi dan target opsional yang menghentikan asisten.
- Setiap kali Mulai ditekan, hitungan kembali ke nol. Material dan hasil yang belum terkonfirmasi tidak dihitung; hitungan tidak disimpan.
- Tombol pintas berhenti dapat diubah, dengan F9 sebagai bawaan. Klik kolomnya lalu tekan tombol atau kombinasi; kembali ke jendela tidak memulai pengikatan ulang.
- Antarmuka terang sederhana, penskalaan DPI tinggi, riwayat aktivitas, dan diagnostik lokal opsional melalui Mode pengembang.

## Cara menggunakan

1. Buka game, siapkan umpan, dan masuk ke layar memancing.
2. Jalankan EXE dan pilih bahasa yang sama dengan game.
3. Atur target tangkapan; `0` berarti tanpa batas. Untuk mengubah pintasan berhenti, klik kolomnya lalu tekan kombinasi yang diinginkan.
4. Klik Mulai. Asisten mencoba mengaktifkan game; pertahankan game di depan dengan seluruh tampilannya terlihat selama berjalan.
5. Berhenti dengan pintasan, tombol Berhenti, atau berpindah jendela. Mulai lagi akan mengatur hitungan ke nol dan menghitung target dari awal.

## Persyaratan dan batasan

Memerlukan Windows 10 / 11 x64 dan game versi Windows. Pertahankan area klien game pada 16:9; jangan minimalkan, tutupi, atau ubah ukuran jendela saat berjalan. Memancing di latar belakang, membeli umpan, berpindah peta, dan mengisi ulang sumber daya tidak didukung.

Warna karakter, animasi, resolusi, kinerja, dan pembaruan game masih dapat memengaruhi pengenalan dan input; hentikan dan berikan data diagnostik jika terjadi masalah. Ini adalah alat tidak resmi yang tidak membaca atau mengubah memori proses, data simpanan, atau file game. Alat ini hanya ditujukan untuk pembelajaran pemrograman Python serta penelitian dan pertukaran pengetahuan tentang teknologi pengenalan gambar. Periksa sendiri aturan game mengenai penggunaan alat otomatisasi. Jangan gunakan alat ini untuk merusak ekosistem game atau untuk tujuan komersial maupun mencari keuntungan. Pengembang tidak bertanggung jawab atas masalah apa pun yang timbul akibat penggunaan alat ini.

## Melaporkan masalah dan Mode pengembang

Laporkan kegagalan melanjutkan ronde, masalah pelacakan, atau masalah lain melalui [GitHub Issues](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues).

Aktifkan Mode pengembang sebelum mengulangi masalah. Mode ini menyimpan tangkapan layar status, kartu tangkapan, data pelacakan, dan waktu pemrosesan secara lokal; tidak ada unggahan otomatis. Tangkapan layar berisi tampilan game, dan diagnostik menambah beban kinerja.

Klik `?` di sebelah Mode pengembang untuk melihat dan membuka folder diagnostik:

```text
%LOCALAPPDATA%\HololiveFishingAuto\sessions\
```

Lokasi mengikuti akun Windows Anda. Setiap sesi membuat folder bernama waktu. Sertakan versi aplikasi, bahasa / karakter game, resolusi, skala tampilan Windows, deskripsi masalah, dan ZIP seluruh folder sesi terkait. Periksa tangkapan layar sebelum membagikannya agar tidak ada informasi yang tidak ingin dipublikasikan.

## Kode sumber dan lisensi

Lihat [panduan pengembangan](docs/DEVELOPMENT.md) untuk menjalankan kode sumber, membuat EXE tunggal, dan pengujian offline. Kode berlisensi [MIT](LICENSE); hak atas karakter ikan dan game tetap milik pemilik masing-masing.
