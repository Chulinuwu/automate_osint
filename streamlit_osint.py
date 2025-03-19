import streamlit as st
import subprocess
import os

## If domain is hosted by cloudflare etc, instead of using something like example.com, use the real ip address instead should be good
def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

st.title("🔍 OSINT + Pentest Automation Tool")
st.subheader("ใส่ URL ของเว็บที่ต้องการทดสอบ")

target = st.text_input("🔗 ใส่เป้าหมาย (เช่น example.com)")
target_folder = f"results/{target}" if target else "results/default"
os.makedirs(target_folder, exist_ok=True)

if st.button("🚀 เริ่มสแกน"):
    st.write("## **1️⃣ ค้นหา Subdomains (ใช้ Sublist3r แทน Subfinder)**")
    subdomains = run_command(f"python3 /usr/share/sublist3r/sublist3r.py -d {target} -o {target_folder}/subdomains.txt")
    st.code(subdomains)

    st.write("## **2️⃣ ตรวจสอบ DNS & หา IP จริง**")
    dns_info = run_command(f"dnsrecon -d {target}")
    st.code(dns_info)
    with open(f"{target_folder}/dns.txt", "w") as f:
        f.write(dns_info)

    # 🔎 ใช้ CloudFail หา IP ถ้าเจอ Cloudflare
    st.write("## **3️⃣ ตรวจหา Cloudflare และดึง IP จริง (CloudFail)**")
    cloudfail_result = run_command(f"cloudfail -t {target}")
    st.code(cloudfail_result)
    with open(f"{target_folder}/cloudfail.txt", "w") as f:
        f.write(cloudfail_result)

    # ดึงค่า IP จริงจาก CloudFail
    real_ip = None
    for line in cloudfail_result.split("\n"):
        if "IP Address Found" in line:
            real_ip = line.split(":")[-1].strip()
            break

    # ใช้ IP จริงแทนโดเมน ถ้าเจอ
    scan_target = real_ip if real_ip else target

    st.write("## **4️⃣ สแกนพอร์ต (Nmap)**")
    ports = run_command(f"nmap -p 1-65535 {scan_target}")
    st.code(ports)
    with open(f"{target_folder}/nmap.txt", "w") as f:
        f.write(ports)

    st.write("## **5️⃣ ตรวจสอบ WAF (Web Application Firewall)**")
    waf = run_command(f"wafw00f {scan_target}")
    st.code(waf)
    with open(f"{target_folder}/waf.txt", "w") as f:
        f.write(waf)

    st.write("## **6️⃣ ค้นหา Directories ที่ซ่อนอยู่ (Gobuster - ข้าม 404)**")
    gobuster_output = run_command(f"gobuster dir -u http://{scan_target} -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt --timeout 10s -b 404")
    st.code(gobuster_output)
    with open(f"{target_folder}/dirs.txt", "w") as f:
        f.write(gobuster_output)

    st.write("## **7️⃣ ตรวจหา SQL Injection & XSS**")
    sql_xss = run_command(f"sqlmap -u 'http://{scan_target}' --dbs --batch --crawl=2")
    st.code(sql_xss)
    with open(f"{target_folder}/sqlmap.txt", "w") as f:
        f.write(sql_xss)

    st.write("## **8️⃣ ตรวจสอบ Security Headers (ปรับให้รองรับ HTTPS & Timeout)**")
    headers = run_command(f"curl -s --max-time 10 -I --location --user-agent 'Mozilla/5.0' https://{scan_target}")
    if headers:
        st.code(headers)
        with open(f"{target_folder}/headers.txt", "w") as f:
            f.write(headers)
    else:
        st.warning("⚠️ ไม่สามารถดึง Security Headers ได้ อาจมีการป้องกันจาก WAF หรือเซิร์ฟเวอร์ไม่ตอบสนอง")

    st.success("✅ การสแกนเสร็จสิ้น! ผลลัพธ์ถูกบันทึกในโฟลเดอร์ results/")
