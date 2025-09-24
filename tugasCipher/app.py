from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import io
import numpy as np
from string import ascii_uppercase
import base64

app = Flask(__name__)
app.secret_key = "change-this"

# ===== Utility Functions =====
ALPHA = ascii_uppercase.replace("J", "")  # untuk Playfair
A2I = {c: i for i, c in enumerate(ascii_uppercase)}

def char_to_num(c): return A2I[c.upper()]
def num_to_char(n): return ascii_uppercase[n % 26]

def gcd(a,b):
    while b: a,b = b,a%b
    return a

def mod_inverse(a,m):
    """Extended Euclidean Algorithm untuk modular inverse"""
    if gcd(a, m) != 1:
        return None
    
    # Extended Euclidean Algorithm
    def extended_gcd(a, b):
        if a == 0:
            return b, 0, 1
        gcd_val, x1, y1 = extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd_val, x, y
    
    _, x, _ = extended_gcd(a % m, m)
    return (x % m + m) % m

def matrix_inverse_mod26(M):
    det = int(np.round(np.linalg.det(M))) % 26
    det_inv = mod_inverse(det,26)
    if det_inv is None: return None
    adj = np.array([[M[1][1], -M[0][1]], [-M[1][0], M[0][0]]])
    return (det_inv*adj) % 26

def format_output(text, fmt):
    if fmt == "nospace":
        return ''.join(text.split())
    elif fmt == "groups":
        clean = ''.join(text.split())
        return ' '.join([clean[i:i+5] for i in range(0,len(clean),5)])
    return text

# ===== File Metadata Handling =====
def create_cipher_file(original_filename: str, cipher_data: bytes) -> bytes:
    """
    Membuat file cipher dengan format:
    [4 bytes: panjang nama file][nama file][data terenkripsi]
    """
    filename_bytes = original_filename.encode('utf-8')
    length_bytes = len(filename_bytes).to_bytes(4, 'big')
    return length_bytes + filename_bytes + cipher_data

def extract_from_cipher_file(cipher_file: bytes) -> tuple:
    """
    Mengextract nama file asli dan data dari file cipher
    Returns: (original_filename, cipher_data)
    """
    if len(cipher_file) < 4:
        raise ValueError("Invalid cipher file format")
    
    filename_length = int.from_bytes(cipher_file[:4], 'big')
    if len(cipher_file) < 4 + filename_length:
        raise ValueError("Invalid cipher file format")
    
    filename = cipher_file[4:4+filename_length].decode('utf-8')
    cipher_data = cipher_file[4+filename_length:]
    return filename, cipher_data

# ===== Cipher Functions - Text Mode =====
def shift_text(text, key, enc=True):
    """Shift cipher untuk text (huruf A-Z saja)"""
    res = ""
    for ch in text.upper():
        if ch.isalpha():
            res += num_to_char(char_to_num(ch) + (key if enc else -key))
        else: 
            res += ch
    return res

def vigenere_text(text, key, enc=True):
    """Vigenere cipher untuk text"""
    if not key.isalpha(): 
        raise ValueError("Key must be letters")
    res = ""; j = 0
    for ch in text.upper():
        if ch.isalpha():
            shift_val = char_to_num(key[j % len(key)].upper())
            res += num_to_char(char_to_num(ch) + (shift_val if enc else -shift_val))
            j += 1
        else: 
            res += ch
    return res

def substitution(text,key,enc=True):
    key=key.upper()
    if len(key)!=26 or len(set(key))!=26:
        raise ValueError("Key must be 26 unique letters")
    if enc:
        table={ascii_uppercase[i]:key[i] for i in range(26)}
    else:
        table={key[i]:ascii_uppercase[i] for i in range(26)}
    return ''.join(table.get(ch,ch) for ch in text.upper())

def affine(text,a,b,enc=True):
    if gcd(a,26)!=1: raise ValueError("a must be coprime with 26")
    if enc:
        return ''.join(num_to_char(a*char_to_num(ch)+b) if ch.isalpha() else ch for ch in text.upper())
    else:
        ainv=mod_inverse(a,26)
        return ''.join(num_to_char(ainv*(char_to_num(ch)-b)) if ch.isalpha() else ch for ch in text.upper())

def hill(text,M,enc=True):
    t=''.join([c for c in text.upper() if c.isalpha()])
    if len(t)%2: t+='X'
    if not enc:
        M=matrix_inverse_mod26(M)
        if M is None: raise ValueError("Matrix not invertible mod 26")
    res=""
    for i in range(0,len(t),2):
        v=np.array([char_to_num(t[i]),char_to_num(t[i+1])])
        w=np.dot(M,v)%26
        res+=num_to_char(int(w[0]))+num_to_char(int(w[1]))
    return res

def permutation(text,key_nums,enc=True):
    t=''.join([c for c in text.upper() if c.isalpha()])
    n=len(key_nums)
    while len(t)%n: t+='X'
    if enc:
        out=[]
        for i in range(0,len(t),n):
            block=t[i:i+n]; e=['']*n
            for j in range(n): e[key_nums[j]-1]=block[j]
            out.append(''.join(e))
        return ''.join(out)
    else:
        inv=[0]*n
        for i,k in enumerate(key_nums): inv[k-1]=i
        out=[]
        for i in range(0,len(t),n):
            block=t[i:i+n]; d=['']*n
            for j in range(n): d[j]=block[inv[j]]
            out.append(''.join(d))
        return ''.join(out)

def generate_playfair_table(key):
    key = key.upper().replace("J", "I")
    table = ""
    for c in key:
        if c not in table and c in ascii_uppercase.replace("J",""):
            table+=c
    for c in ascii_uppercase.replace("J",""):
        if c not in table:
            table+=c
    return [list(table[i*5:(i+1)*5]) for i in range(5)]

def find_position(table, ch):
    for r in range(5):
        for c in range(5):
            if table[r][c]==ch: return r,c
    return None,None

def playfair(text,key,enc=True):
    table=generate_playfair_table(key)
    t=''.join([c for c in text.upper() if c.isalpha()]).replace("J","I")
    pairs=[]
    i=0
    while i<len(t):
        a=t[i]
        b=t[i+1] if i+1<len(t) else 'X'
        if a==b: 
            pairs.append((a,'X'))
            i+=1
        else:
            pairs.append((a,b))
            i+=2
    res=""
    for a,b in pairs:
        r1,c1=find_position(table,a)
        r2,c2=find_position(table,b)
        if r1==r2:
            if enc:
                res+=table[r1][(c1+1)%5]+table[r2][(c2+1)%5]
            else:
                res+=table[r1][(c1-1)%5]+table[r2][(c2-1)%5]
        elif c1==c2:
            if enc:
                res+=table[(r1+1)%5][c1]+table[(r2+1)%5][c2]
            else:
                res+=table[(r1-1)%5][c1]+table[(r2-1)%5][c2]
        else:
            res+=table[r1][c2]+table[r2][c1]
    return res

def otp(text,key,enc=True):
    t=''.join([c for c in text.upper() if c.isalpha()])
    k=''.join([c for c in key.upper() if c.isalpha()])
    if len(k)<len(t): raise ValueError("OTP key too short")
    res=""
    for i,ch in enumerate(t):
        shift_val=char_to_num(k[i])
        if enc:
            res+=num_to_char(char_to_num(ch)+shift_val)
        else:
            res+=num_to_char(char_to_num(ch)-shift_val)
    return res

# ===== Cipher Functions - Binary Mode =====
def shift_binary(data: bytes, key: int, enc=True) -> bytes:
    """Shift cipher untuk data binary"""
    result = []
    for byte_val in data:
        if enc:
            new_val = (byte_val + key) % 256
        else:
            new_val = (byte_val - key) % 256
        result.append(new_val)
    return bytes(result)

def vigenere_binary(data: bytes, key: str, enc=True) -> bytes:
    """Vigenere cipher untuk data binary"""
    if not key.isalpha():
        raise ValueError("Key must be letters")
    
    key_nums = [char_to_num(c) for c in key.upper()]
    result = []
    
    for i, byte_val in enumerate(data):
        key_val = key_nums[i % len(key_nums)]
        key_scaled = int((key_val / 25) * 255)
        
        if enc:
            new_val = (byte_val + key_scaled) % 256
        else:
            new_val = (byte_val - key_scaled) % 256
        result.append(new_val)
    
    return bytes(result)

def substitution_binary(data: bytes, key: str, enc=True) -> bytes:
    """Substitution cipher untuk data binary"""
    key = key.upper()
    if len(key) != 26 or len(set(key)) != 26:
        raise ValueError("Key must be 26 unique letters")
    
    # Buat lookup table 256 byte berdasarkan key 26 huruf
    if enc:
        # Enkripsi: buat mapping byte -> byte berdasarkan pattern key
        table = {}
        for i in range(256):
            # Map setiap byte ke posisi dalam alphabet, lalu substitute
            alpha_pos = i % 26
            key_char = key[alpha_pos]
            new_pos = char_to_num(key_char)
            table[i] = (i // 26) * 26 + new_pos
        return bytes([table[b] % 256 for b in data])
    else:
        # Dekripsi: reverse mapping
        reverse_key = [''] * 26
        for i, c in enumerate(key):
            reverse_key[char_to_num(c)] = ascii_uppercase[i]
        
        table = {}
        for i in range(256):
            alpha_pos = i % 26
            orig_char = reverse_key[alpha_pos] if alpha_pos < len(reverse_key) else ascii_uppercase[alpha_pos]
            new_pos = char_to_num(orig_char)
            table[i] = (i // 26) * 26 + new_pos
        return bytes([table[b] % 256 for b in data])

def affine_binary(data: bytes, a: int, b: int, enc=True) -> bytes:
    """Affine cipher untuk data binary (mod 256)"""
    if gcd(a, 256) != 1:
        raise ValueError("a must be coprime with 256")
    
    result = []
    if enc:
        for byte_val in data:
            new_val = (a * byte_val + b) % 256
            result.append(new_val)
    else:
        a_inv = mod_inverse(a, 256)
        if a_inv is None:
            raise ValueError("Cannot find modular inverse")
        for byte_val in data:
            new_val = (a_inv * (byte_val - b)) % 256
            result.append(new_val)
    
    return bytes(result)

def hill_binary(data: bytes, M, enc=True) -> bytes:
    """Hill cipher untuk data binary (2x2 matrix, mod 256)"""
    # Pastikan data panjangnya genap
    if len(data) % 2:
        data = data + b'\x00'  # padding dengan null byte
    
    if not enc:
        # Hitung inverse matrix mod 256
        det = int(np.round(np.linalg.det(M))) % 256
        det_inv = mod_inverse(det, 256)
        if det_inv is None:
            raise ValueError("Matrix not invertible mod 256")
        adj = np.array([[M[1][1], -M[0][1]], [-M[1][0], M[0][0]]])
        M = (det_inv * adj) % 256
    
    result = []
    for i in range(0, len(data), 2):
        v = np.array([data[i], data[i+1]])
        w = np.dot(M, v) % 256
        result.extend([int(w[0]), int(w[1])])
    
    return bytes(result)

def permutation_binary(data: bytes, key_nums, enc=True) -> bytes:
    """Permutation cipher untuk data binary"""
    n = len(key_nums)
    # Padding data agar bisa dibagi blok n
    while len(data) % n:
        data = data + b'\x00'
    
    if enc:
        result = []
        for i in range(0, len(data), n):
            block = data[i:i+n]
            encrypted_block = [0] * n
            for j in range(n):
                encrypted_block[key_nums[j]-1] = block[j]
            result.extend(encrypted_block)
        return bytes(result)
    else:
        # Buat inverse permutation
        inv = [0] * n
        for i, k in enumerate(key_nums):
            inv[k-1] = i
        
        result = []
        for i in range(0, len(data), n):
            block = data[i:i+n]
            decrypted_block = [0] * n
            for j in range(n):
                decrypted_block[j] = block[inv[j]]
            result.extend(decrypted_block)
        return bytes(result)

def playfair_binary(data: bytes, key: str, enc=True) -> bytes:
    """
    Playfair untuk binary - convert bytes ke base64, 
    lalu apply playfair text, lalu convert balik
    """
    if enc:
        # Convert binary -> base64 -> playfair encrypt
        b64_data = base64.b64encode(data).decode('ascii')
        encrypted_text = playfair(b64_data, key, enc=True)
        return encrypted_text.encode('ascii')
    else:
        # playfair decrypt -> base64 decode -> binary
        try:
            decrypted_text = playfair(data.decode('ascii'), key, enc=False)
            # Remove padding jika ada
            decrypted_text = decrypted_text.rstrip('X')
            return base64.b64decode(decrypted_text)
        except Exception as e:
            raise ValueError(f"Playfair binary decryption failed: {e}")

def otp_binary(data: bytes, key_data: bytes, enc=True) -> bytes:
    """One-Time Pad untuk data binary"""
    if len(key_data) < len(data):
        raise ValueError("OTP key too short for binary data")
    
    result = []
    for i, byte_val in enumerate(data):
        key_byte = key_data[i]
        if enc:
            new_val = (byte_val + key_byte) % 256
        else:
            new_val = (byte_val - key_byte) % 256
        result.append(new_val)
    
    return bytes(result)

# ===== Unified Cipher Functions =====
def process_shift(data, key, enc=True, is_binary=False):
    """Unified function untuk shift cipher"""
    if is_binary:
        return shift_binary(data, key, enc)
    else:
        return shift_text(data, key, enc)

def process_vigenere(data, key, enc=True, is_binary=False):
    """Unified function untuk vigenere cipher"""
    if is_binary:
        return vigenere_binary(data, key, enc)
    else:
        return vigenere_text(data, key, enc)

def process_substitution(data, key, enc=True, is_binary=False):
    """Unified function untuk substitution cipher"""
    if is_binary:
        return substitution_binary(data, key, enc)
    else:
        return substitution(data, key, enc)

def process_affine(data, a, b, enc=True, is_binary=False):
    """Unified function untuk affine cipher"""
    if is_binary:
        return affine_binary(data, a, b, enc)
    else:
        return affine(data, a, b, enc)

def process_hill(data, M, enc=True, is_binary=False):
    """Unified function untuk hill cipher"""
    if is_binary:
        return hill_binary(data, M, enc)
    else:
        return hill(data, M, enc)

def process_permutation(data, key_nums, enc=True, is_binary=False):
    """Unified function untuk permutation cipher"""
    if is_binary:
        return permutation_binary(data, key_nums, enc)
    else:
        return permutation(data, key_nums, enc)

def process_playfair(data, key, enc=True, is_binary=False):
    """Unified function untuk playfair cipher"""
    if is_binary:
        return playfair_binary(data, key, enc)
    else:
        return playfair(data, key, enc)

def process_otp(data, key, enc=True, is_binary=False):
    """Unified function untuk OTP cipher"""
    if is_binary:
        # Untuk binary, key harus berupa bytes
        if isinstance(key, str):
            key_bytes = key.encode('utf-8')
        else:
            key_bytes = key
        return otp_binary(data, key_bytes, enc)
    else:
        return otp(data, key, enc)

# ===== Main Route =====
@app.route("/", methods=["GET","POST"])
def index():
    output = None
    
    if request.method == "POST":
        cipher = request.form["cipher"]
        action = request.form["action"]
        input_type = request.form.get("input_type", "text")
        fmt = request.form.get("format", "normal")
        
        try:
            # Determine input source and type
            if input_type == "file":
                if "file_input" not in request.files:
                    raise ValueError("No file uploaded")
                f = request.files["file_input"]
                if not f or f.filename == "":
                    raise ValueError("No file selected")
                
                original_filename = secure_filename(f.filename)
                data = f.read()
                is_binary = True
                
            else:  # text input
                data = request.form.get("input_text", "")
                if not data:
                    raise ValueError("No text input provided")
                is_binary = False
                original_filename = None

            # Process with appropriate cipher
            if cipher == "shift":
                key = int(request.form["shift_key"])
                result = process_shift(data, key, enc=(action=="Encrypt"), is_binary=is_binary)
                    
            elif cipher == "vig":
                key = request.form["vig_key"]
                result = process_vigenere(data, key, enc=(action=="Encrypt"), is_binary=is_binary)
                    
            elif cipher == "sub":
                key = request.form["sub_key"]
                result = process_substitution(data, key, enc=(action=="Encrypt"), is_binary=is_binary)
                
            elif cipher == "affine":
                a = int(request.form["a"]); b = int(request.form["b"])
                result = process_affine(data, a, b, enc=(action=="Encrypt"), is_binary=is_binary)
                
            elif cipher == "hill":
                M = np.array([
                    [int(request.form["m00"]),int(request.form["m01"])],
                    [int(request.form["m10"]),int(request.form["m11"])]
                ])
                result = process_hill(data, M, enc=(action=="Encrypt"), is_binary=is_binary)
                
            elif cipher == "perm":
                key_nums = list(map(int, request.form["perm_key"].split()))
                result = process_permutation(data, key_nums, enc=(action=="Encrypt"), is_binary=is_binary)
                
            elif cipher == "playfair":
                key = request.form["playfair_key"]
                result = process_playfair(data, key, enc=(action=="Encrypt"), is_binary=is_binary)
                
            elif cipher == "otp":
                if is_binary:
                    # Untuk binary OTP, baca key sebagai binary data
                    if "otp_key_file" in request.files:
                        f = request.files["otp_key_file"]
                        key = f.read()  # Read as bytes
                    else:
                        raise ValueError("OTP key file required for binary mode")
                else:
                    # Untuk text OTP, baca key sebagai text
                    if "otp_key_file" in request.files:
                        f = request.files["otp_key_file"]
                        key = f.read().decode("utf-8")
                    else:
                        raise ValueError("OTP key file required")
                result = process_otp(data, key, enc=(action=="Encrypt"), is_binary=is_binary)
                
            else:
                raise ValueError("Unknown cipher")

            # Prepare output
            if is_binary:
                if action == "Encrypt":
                    # Create cipher file with metadata
                    cipher_file_data = create_cipher_file(original_filename, result)
                    download_filename = original_filename + ".dat"
                    
                    # Store binary data for download
                    output = {
                        'type': 'binary',
                        'message': f"File '{original_filename}' berhasil dienkripsi!",
                        'filename': download_filename,
                        'data': base64.b64encode(cipher_file_data).decode('utf-8')
                    }
                else:  # Decrypt
                    # Extract original filename and data from encrypted file
                    original_filename, result = extract_from_cipher_file(data)
                    download_filename = "DECRYPTED_" + original_filename
                    
                    output = {
                        'type': 'binary',
                        'message': f"File berhasil didekripsi menjadi '{original_filename}'!",
                        'filename': download_filename,
                        'data': base64.b64encode(result).decode('utf-8')
                    }
                
            else:
                # Text output
                output = {
                    'type': 'text',
                    'message': format_output(result, fmt),
                    'filename': None,
                    'data': None
                }

        except Exception as e:
            flash(str(e), "danger")
    
    return render_template("index.html", output=output)

@app.route("/download_binary", methods=["POST"])
def download_binary():
    """Handle binary file downloads"""
    try:
        filename = request.form.get("filename", "result.dat")
        data_b64 = request.form.get("data", "")
        
        if not data_b64:
            flash("No data to download", "danger")
            return redirect(url_for("index"))
        
        # Decode base64 data
        binary_data = base64.b64decode(data_b64)
        bio = io.BytesIO(binary_data)
        
        return send_file(bio, as_attachment=True, download_name=filename)
        
    except Exception as e:
        flash(f"Download error: {str(e)}", "danger")
        return redirect(url_for("index"))

@app.route("/save", methods=["POST"])
def save():
    """Save text output to file"""
    data = request.form.get("output", "")
    if not data: 
        return redirect(url_for("index"))
    bio = io.BytesIO(data.encode("utf-8"))
    return send_file(bio, as_attachment=True, download_name="ciphertext.txt")

if __name__ == "__main__":
    app.run(debug=True)