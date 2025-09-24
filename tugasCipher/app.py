from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import io
import numpy as np
from string import ascii_uppercase

app = Flask(__name__)
app.secret_key = "change-this"

# ========= Utility =========
ALPHA = ascii_uppercase
A2I = {c: i for i, c in enumerate(ALPHA)}

def char_to_num(c): return A2I[c.upper()]
def num_to_char(n): return ALPHA[n % 26]

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

# ========= Cipher functions =========
def shift(text,key,enc=True):
    res=""
    for ch in text.upper():
        if ch.isalpha():
            res+=num_to_char(char_to_num(ch)+(key if enc else -key))
        else:
            res+=ch
    return res

def substitution(text,key,enc=True):
    key=key.upper()
    if len(key)!=26 or len(set(key))!=26:
        raise ValueError("Substitution key must be 26 unique letters")
    if enc:
        table={ALPHA[i]:key[i] for i in range(26)}
    else:
        table={key[i]:ALPHA[i] for i in range(26)}
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
            shift=char_to_num(key[j%len(key)].upper())
            res+=num_to_char(char_to_num(ch)+(shift if enc else -shift))
            j+=1
        else:
            res+=ch
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

# ========= Routes =========
@app.route("/", methods=["GET","POST"])
def index():
    output=None
    if request.method=="POST":
        cipher=request.form["cipher"]
        action=request.form["action"]
        fmt=request.form.get("format","normal")
        text=request.form.get("input_text","")
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
            else:
                raise ValueError("Unknown cipher")

            output=format_output(result,fmt)
        except Exception as e:
            flash(str(e),"danger")
    return render_template("index.html",output=output)

@app.route("/save",methods=["POST"])
def save():
    data=request.form.get("output","")
    if not data: return redirect(url_for("index"))
    bio=io.BytesIO(data.encode("utf-8"))
    return send_file(bio,as_attachment=True,download_name="ciphertext.txt")

if __name__=="__main__":
    app.run(debug=True)