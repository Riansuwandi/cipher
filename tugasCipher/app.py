from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import io
import numpy as np
from string import ascii_uppercase

app = Flask(__name__)
app.secret_key = "change-this"

# ===== Utility =====
ALPHA = ascii_uppercase.replace("J", "")  # untuk Playfair
A2I = {c: i for i, c in enumerate(ascii_uppercase)}

def char_to_num(c): return A2I[c.upper()]
def num_to_char(n): return ascii_uppercase[n % 26]

def gcd(a,b):
    while b: a,b = b,a%b
    return a

def mod_inverse(a,m):
    for i in range(1,m):
        if (a*i)%m==1: return i
    return None

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

# ===== Cipher Functions =====
def shift(text,key,enc=True):
    res=""
    for ch in text.upper():
        if ch.isalpha():
            res+=num_to_char(char_to_num(ch)+(key if enc else -key))
        else: res+=ch
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

def vigenere(text,key,enc=True):
    if not key.isalpha(): raise ValueError("Key must be letters")
    res=""; j=0
    for ch in text.upper():
        if ch.isalpha():
            shift_val=char_to_num(key[j%len(key)].upper())
            res+=num_to_char(char_to_num(ch)+(shift_val if enc else -shift_val))
            j+=1
        else: res+=ch
    return res

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

# ===== Playfair =====
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

# ===== One Time Pad =====
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

# ===== Routes =====
@app.route("/", methods=["GET","POST"])
def index():
    output=None
    if request.method=="POST":
        cipher=request.form["cipher"]
        action=request.form["action"]
        fmt=request.form.get("format","normal")
        text=request.form.get("input_text","")

        # handle file input
        if "file_input" in request.files:
            f=request.files["file_input"]
            if f and f.filename:
                text=f.read().decode("utf-8")

        try:
            if cipher=="shift":
                key=int(request.form["shift_key"])
                result=shift(text,key,enc=(action=="Encrypt"))
            elif cipher=="sub":
                key=request.form["sub_key"]
                result=substitution(text,key,enc=(action=="Encrypt"))
            elif cipher=="affine":
                a=int(request.form["a"]); b=int(request.form["b"])
                result=affine(text,a,b,enc=(action=="Encrypt"))
            elif cipher=="vig":
                key=request.form["vig_key"]
                result=vigenere(text,key,enc=(action=="Encrypt"))
            elif cipher=="hill":
                M=np.array([
                    [int(request.form["m00"]),int(request.form["m01"])],
                    [int(request.form["m10"]),int(request.form["m11"])]
                ])
                result=hill(text,M,enc=(action=="Encrypt"))
            elif cipher=="perm":
                key_nums=list(map(int,request.form["perm_key"].split()))
                result=permutation(text,key_nums,enc=(action=="Encrypt"))
            elif cipher=="playfair":
                key=request.form["playfair_key"]
                result=playfair(text,key,enc=(action=="Encrypt"))
            elif cipher=="otp":
                if "otp_key_file" in request.files:
                    f=request.files["otp_key_file"]
                    key=f.read().decode("utf-8")
                else:
                    raise ValueError("OTP key file required")
                result=otp(text,key,enc=(action=="Encrypt"))
            else:
                raise ValueError("Unknown cipher")

            output=format_output(result,fmt)
        except Exception as e:
            flash(str(e),"danger")
    else:
        output=None
    return render_template("index.html",output=output)

@app.route("/save",methods=["POST"])
def save():
    data=request.form.get("output","")
    if not data: return redirect(url_for("index"))
    bio=io.BytesIO(data.encode("utf-8"))
    return send_file(bio,as_attachment=True,download_name="ciphertext.txt")

if __name__=="__main__":
    app.run(debug=True)
