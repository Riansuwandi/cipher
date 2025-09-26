# **CRYPTOSYSTEM**

Program yang dapat menjalankan proses enkripsi dan deskripsi text maupun file biner menggunakan algoritma kriptogarfi. Tujuannya agar dapat membantu user memahami cara kerja dasar kriptografi.

## Features

- Enkripsi dan Deskripsi text ataupun file biner dengan berbagai macam algoritma kriptografi dasar
- Fitur algoritma Shift, Substitution, Affine, Vigenere, Hill, Permutation, Playfair, One-Time Pad
- Input text, upload file, dan key manual
- UI interactive
- Output dapat tersedia dalam format normal, satuan 5 huruf, dan tanpa spasi
- Output dapat di download

## Run Locally

1. Clone the project
```bash
  git clone https://github.com/Riansuwandi/cipher.git
```

2. Go to the project directory
```bash
  cd cipher/tugasCipher
```

3. Install dependency
```bash
  pip install -r requirements.txt
```

4. Start the program
```bash
  python app.py
```

5. Open the link `http://127.0.0.1:5000` on browser

## Build With

Program dibangun dengan beberapa Stack:

- ![Python](https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white)
- ![HTML](https://img.shields.io/badge/html5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
- ![CSS](https://img.shields.io/badge/css3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
- ![JavaScript](https://img.shields.io/badge/javascript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
## Algoritma Implementation 

### 1. Shift Cipher
Menggeser alfabet sejauh **kunci tertentu**. Misalnya, jika kunci = 3, maka huruf A → D, B → E, dst.

### 2. Substitution Cipher
Mengganti setiap huruf dengan huruf lain sesuai **peta substitusi** yang ditentukan. Contoh: A → Q, B → W, C → E.

### 3. Affine Cipher
Menggunakan rumus matematika:  
```bash
E(x) = (ax + b) mod 26
```  
dengan syarat `a` harus relatif prima terhadap 26.

### 4. Vigenere Cipher
Menggunakan **kunci berulang** untuk mengenkripsi teks. Setiap huruf plaintext digeser berdasarkan huruf kunci.

### 5. Hill Cipher
Menggunakan **matriks kunci** dari aljabar linear. Plaintext dipecah menjadi blok huruf, lalu dikalikan dengan matriks kunci (mod 26).

### 6. Permutation Cipher
Mengenkripsi dengan **mengacak posisi karakter** berdasarkan kunci permutasi. Pada file biner, semua byte (termasuk header) ikut berubah. Setelah didekripsi dengan kunci yang sama, file dapat dipulihkan kembali (dengan ekstensi asli).

### 7. Playfair Cipher
Menggunakan **tabel 5x5** yang dibangun dari kata kunci. Plaintext diproses berpasangan (digraph). Setiap pasangan huruf diganti sesuai aturan posisi di tabel (satu baris, satu kolom, atau kotak persegi panjang).

### 8. One-Time Pad (OTP)
Menggunakan kunci acak sepanjang pesan. Proses enkripsi dilakukan dengan operasi XOR antara plaintext dan kunci. Jika kunci benar-benar acak, digunakan hanya sekali, dan panjangnya sama dengan pesan.

## How to Use

1. Jalankan program `http://127.0.0.1:5000` di browser

![webHome](https://github.com/user-attachments/assets/17792328-cef2-4bb7-baa6-10e61e257280)

2. Pilih algoritma kriptografi pada `sidebar menu`

![sidebar](https://github.com/user-attachments/assets/3f4a9e92-afd6-415d-9999-ddabb1ea59d7)

3. Pilih opsi input (`text input`/`file upload`)

![inputOption](https://github.com/user-attachments/assets/769114aa-66ed-47bd-8b47-dfe3632dd09d)

4. Tulis text input atau upload file yang ingin di enkripsi atau deskripsi

![input](https://github.com/user-attachments/assets/9fdf68d5-d3c5-464a-b4f9-0ce819d7e106)

5. Masukkan `key` (kunci)

![key](https://github.com/user-attachments/assets/ea47df28-cbcb-452a-bf22-5029f7c4d32f)

6. Pilih format output lalu klik tombol `encrypt` atau `decrypt`

![outputOption](https://github.com/user-attachments/assets/4e41c492-4153-4dcb-b13d-ced0c739ab11)

7. Hasil akan tampil di bawah, dan bisa di `download`

![outputFinish](https://github.com/user-attachments/assets/e40c734d-512f-40e1-b646-119ecd112947)

## Contributors

- Afanina Rizky Ramadhani [L0123008]
- Alya Irgina Mas'udah [L0123018]
- Muhamad Afrian Suwandi [L0123087]

## Credits
Segala resource yang dimuat dalam project ini dikembangkan oleh Anggota kelompok kami, yang bertujuan untuk menuntaskan tugas implementasi algoritma kriptografi dalam program web.
