""" File: xuly.py - Đã tối ưu cho Vercel """
import time
import json
import base64
from urllib3 import disable_warnings
from requests import session
from bs4 import BeautifulSoup

# Import các hàm từ file khác
from txtcaptcha import bypass_text_captcha
from InvisCapcha import bypass_captcha
from config import *

disable_warnings()

# --- Giữ nguyên hàm extract_violations_from_html ---
def extract_violations_from_html(html_content, url_csgt):
    # (Giữ nguyên nội dung hàm này như cũ của cậu)
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        violations = []
        body_print = soup.find("div", id="bodyPrint123")
        if not body_print:
            return {"status": "failed", "data": None}
        
        sections = body_print.find_all(recursive=False)
        current_violation = None
        for element in sections:
            if "form-group" in element.get("class", []):
                if current_violation is None:
                    current_violation = {
                        "Biển kiểm soát": "", "Màu biển": "", "Loại phương tiện": "",
                        "Thời gian vi phạm": "", "Địa điểm vi phạm": "", "Hành vi vi phạm": "",
                        "Trạng thái": "", "Đơn vị phát hiện vi phạm": "", "Nơi giải quyết vụ việc": []
                    }
                label = element.find("label", class_="control-label")
                value = element.find("div", class_="col-md-9")
                if label and value:
                    key = label.get_text(strip=True).replace(":", "")
                    val = value.get_text(strip=True)
                    if key in current_violation and key != "Nơi giải quyết vụ việc":
                        current_violation[key] = val
                
                text = element.get_text(strip=True)
                if text and ("Đội" in text or "Địa chỉ" in text or "Số điện thoại" in text):
                    if isinstance(current_violation["Nơi giải quyết vụ việc"], list):
                        current_violation["Nơi giải quyết vụ việc"].append(text)
                    else:
                        current_violation["Nơi giải quyết vụ việc"] = [text]

            elif element.name == "hr":
                if current_violation:
                    violations.append(current_violation)
                    current_violation = None

        if current_violation:
            violations.append(current_violation)
            
        if not violations:
            return {"status": "success", "url": url_csgt, "msg": "Không có vi phạm", "data": None}
        return {"status": "success", "url": url_csgt, "msg": "Có vi phạm", "data": violations}

    except Exception as e:
        return {"status": "success", "url": url_csgt, "msg": "Không có vi phạm", "data": None}

def image_to_base64(ss, url):
    try:
        response = ss.get(url, timeout=5) # Thêm timeout
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')
    except:
        pass
    return None

# --- Hàm chính đã tối ưu ---
def kiemtra_bienso(bienso, loaiXe, apicaptcha, attempts=1):
    ss = session()
    url_check_param = f'https://www.csgt.vn/tra-cuu-phuong-tien-vi-pham.html?&LoaiXe={loaiXe}&BienKiemSoat={bienso}'
    
    try:
        response = ss.get(url=url_check_param, headers=check_header, verify=False, timeout=5)
    except:
        return json.dumps({"status": "error", "message": "Lỗi kết nối CSGT"}, ensure_ascii=False)

    if response.status_code != 200:
        return json.dumps({"status": "error", "message": "CSGT.vn không phản hồi"}, ensure_ascii=False)
    
    cookies = response.cookies.get_dict()
    PHPSESSID = cookies.get('PHPSESSID', '')
    tracuu_cookie = f'PHPSESSID={PHPSESSID}'
    
    # Xử lý Captcha
    image_base64 = image_to_base64(ss, captcha_url_csgt)
    if image_base64:
        captcha_image = bypass_text_captcha(apicaptcha, image_base64)
    else:
        return json.dumps({"status": "error", "message": "Lỗi tải ảnh captcha"}, ensure_ascii=False)
    
    if not captcha_image:
         captcha_image = "error"
         
    captcha_image = str(captcha_image).replace(' ','').lower()
    
    # Giả lập bypass invisible (có thể cần cập nhật token nếu Google đổi)
    # Token cứng này có thể hết hạn, nhưng tạm thời giữ nguyên logic của cậu
    captcha_invisible = bypass_captcha(get_invisible_captcha, post_invisible_captcha)
    
    tracuu_data = f'BienKS={bienso}&Xe={loaiXe}&captcha={captcha_image}&token={captcha_invisible}&ipClient=9.9.9.91&cUrl=1'
    
    headers_post = tracuu_header.copy()
    headers_post['Cookie'] = tracuu_cookie
    headers_post['Referer'] = url_check_param

    try:
        response_check = ss.post(url=tracuu_url, headers=headers_post, data=tracuu_data, timeout=10)
        json_response = response_check.json()
        respond_check = json_response.get('href') # Link kết quả
        
        # LOGIC QUAN TRỌNG: Giảm số lần thử lại để tránh Timeout Vercel
        if not respond_check:
            if attempts < 2:  # <--- CHỈ THỬ LẠI 1 LẦN (Tổng 2 lần)
                time.sleep(1) # <--- NGHỈ 1 GIÂY THÔI
                return kiemtra_bienso(bienso, loaiXe, apicaptcha, attempts + 1)
            else:
                return json.dumps({"status": "error", "message": "Sai captcha hoặc lỗi hệ thống"}, ensure_ascii=False)
        
        # Lấy kết quả cuối cùng
        respond_tracuu = ss.get(url=respond_check, verify=False, timeout=10)
        violations = extract_violations_from_html(respond_tracuu.text, respond_check)
        return json.dumps(violations, ensure_ascii=False)
        
    except Exception as e:
        if attempts < 2:
            time.sleep(1)
            return kiemtra_bienso(bienso, loaiXe, apicaptcha, attempts + 1)
        return json.dumps({"status": "error", "message": f"Lỗi xử lý: {str(e)}"}, ensure_ascii=False)
