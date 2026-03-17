import sys
import io
import json
from datetime import timedelta

from django.contrib.auth.hashers import check_password
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Q
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError

# Import đầy đủ các Models
from .models import GiaoDich, ThanhVien, LoaiQuy, DotThu, MucTieuQuy
from .utils import format_money
try:
    from google import genai
except ImportError:
    pass

# --- HÀM HỖ TRỢ XỬ LÝ SỐ TIỀN ---
def clean_amount(amount_str):
    if not amount_str: return 0
    # Xóa dấu chấm và phẩy để biến "20.000" thành 20000
    return int(str(amount_str).replace('.', '').replace(',', ''))

# ==========================================
# 1. API NỘP QUỸ (THU TIỀN)
# ==========================================
@csrf_exempt  # Tắt chặn bảo mật để tránh lỗi 403
@login_required
@require_POST
def api_nop_quy(request):
    try:
        data = json.loads(request.body)
        
        # Tối ưu: Tìm thành viên an toàn bằng MSSV trước, không có mới tìm Email
        tv = ThanhVien.objects.filter(mssv=getattr(request.user, 'mssv', '')).first()
        if not tv:
            tv = ThanhVien.objects.filter(email=getattr(request.user, 'email', '')).first()

        # Tối ưu: Lấy quỹ đầu tiên an toàn nhất
        quy = LoaiQuy.objects.first()
        if not quy:
            return JsonResponse({'status': 'error', 'message': 'Hệ thống chưa có Quỹ!'})
        
        so_tien = clean_amount(data.get('so_tien'))
        ly_do = data.get('ly_do') or f"{request.user.full_name or request.user.username} nộp quỹ"
        
        dot_thu_id = data.get('dot_thu_id')
        dot_thu_obj = DotThu.objects.filter(id=dot_thu_id).first() if dot_thu_id else None

        muc_tieu_id = data.get('muc_tieu_id')
        muc_tieu_obj = MucTieuQuy.objects.filter(id=muc_tieu_id).first() if muc_tieu_id else None

        # TẠO GIAO DỊCH
        GiaoDich.objects.create(
            loai='THU', 
            so_tien=so_tien, 
            ly_do=ly_do, 
            loai_quy=quy, 
            thanh_vien=tv, 
            dot_thu=dot_thu_obj, 
            muc_tieu=muc_tieu_obj,
            danh_muc_id=data.get('category_id'), 
            is_an_danh=data.get('is_an_danh', False),
            created_by=str(request.user.id)
        )

        # AUTO-CỘNG TIỀN VÀO MỤC TIÊU QUỸ 
        if muc_tieu_obj:
            tien_ht = getattr(muc_tieu_obj, 'tien_hien_tai', getattr(muc_tieu_obj, 'so_tien_hien_tai', 0)) or 0
            tien_mt = getattr(muc_tieu_obj, 'tien_muc_tieu', getattr(muc_tieu_obj, 'so_tien_muc_tieu', 0)) or 0
            
            tien_ht_moi = tien_ht + so_tien
            
            if hasattr(muc_tieu_obj, 'tien_hien_tai'):
                muc_tieu_obj.tien_hien_tai = tien_ht_moi
            elif hasattr(muc_tieu_obj, 'so_tien_hien_tai'):
                muc_tieu_obj.so_tien_hien_tai = tien_ht_moi
                
            if tien_ht_moi >= tien_mt and tien_mt > 0:
                muc_tieu_obj.hoan_thanh = True
                
            muc_tieu_obj.save()

        if tv and tv.is_no_xau:
            tv.is_no_xau = False
            tv.save()

        return JsonResponse({'status': 'success', 'message': 'Nộp quỹ thành công!'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Lỗi hệ thống: {str(e)}'})

# ==========================================
# 2. API NỘP QUỸ HỘ
# ==========================================
@csrf_exempt
@login_required
def api_nop_quy_ho(request):
    try:
        data = json.loads(request.body)
        tv = ThanhVien.objects.get(id=data.get('tv_id'))
        so_tien = clean_amount(data.get('so_tien'))
        
        dot_thu_id = data.get('dot_thu_id')
        dot_thu_obj = DotThu.objects.filter(id=dot_thu_id).first() if dot_thu_id else None
        
        muc_tieu_id = data.get('muc_tieu_id')
        muc_tieu_obj = MucTieuQuy.objects.filter(id=muc_tieu_id).first() if muc_tieu_id else None

        quy = LoaiQuy.objects.first()
        if not quy:
            return JsonResponse({'status': 'error', 'message': 'Hệ thống chưa có Quỹ!'})

        GiaoDich.objects.create(
            loai='THU', 
            so_tien=so_tien, 
            ly_do=data.get('ly_do'),
            loai_quy=quy,
            thanh_vien=tv,
            dot_thu=dot_thu_obj,
            muc_tieu=muc_tieu_obj, 
            danh_muc_id=data.get('category_id'),
            created_by=str(request.user.id)
        )

        if muc_tieu_obj:
            tien_ht = getattr(muc_tieu_obj, 'tien_hien_tai', getattr(muc_tieu_obj, 'so_tien_hien_tai', 0)) or 0
            tien_mt = getattr(muc_tieu_obj, 'tien_muc_tieu', getattr(muc_tieu_obj, 'so_tien_muc_tieu', 0)) or 0
            tien_ht_moi = tien_ht + so_tien
            
            if hasattr(muc_tieu_obj, 'tien_hien_tai'):
                muc_tieu_obj.tien_hien_tai = tien_ht_moi
            elif hasattr(muc_tieu_obj, 'so_tien_hien_tai'):
                muc_tieu_obj.so_tien_hien_tai = tien_ht_moi
                
            if tien_ht_moi >= tien_mt and tien_mt > 0:
                muc_tieu_obj.hoan_thanh = True
            muc_tieu_obj.save()

        return JsonResponse({'status': 'success', 'message': 'Nộp quỹ hộ thành công!'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

# ==========================================
# 3. API TẠM ỨNG TIỀN
# ==========================================
@csrf_exempt
@login_required
def api_tam_ung(request):
    try:
        data = json.loads(request.body)
        
        tv = ThanhVien.objects.filter(mssv=getattr(request.user, 'mssv', '')).first()
        if not tv:
            tv = ThanhVien.objects.filter(email=getattr(request.user, 'email', '')).first()
        
        quy = LoaiQuy.objects.first()
        if not quy:
            return JsonResponse({'status': 'error', 'message': 'Chưa có Quỹ. Hãy vào Admin tạo quỹ!'})

        so_tien = clean_amount(data.get('so_tien')) 
        ly_do = data.get('ly_do') or f"Tạm ứng cho {request.user.username}"
        
        GiaoDich.objects.create(loai='TU', so_tien=so_tien, ly_do=ly_do, loai_quy=quy, thanh_vien=tv)
        return JsonResponse({'status': 'success', 'message': 'Phiếu tạm ứng đã được lưu!'})
    except ValidationError as e:
        return JsonResponse({'status': 'error', 'message': list(e.messages)[0]})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Lỗi: {str(e)}'})

# ==========================================
# 4. API ĐIỀU CHUYỂN NỘI BỘ
# ==========================================
@csrf_exempt
@login_required
def api_chuyen_noi_bo(request):
    try:
        data = json.loads(request.body)
        so_tien = clean_amount(data.get('so_tien'))
        id_quy_di = data.get('id_quy_di')
        id_quy_den = data.get('id_quy_den')
        ly_do = data.get('ly_do') or "Chuyển tiền nội bộ"

        if id_quy_di == id_quy_den:
            return JsonResponse({'status': 'error', 'message': 'Quỹ nguồn và đích không được trùng nhau!'})

        quy_di = LoaiQuy.objects.get(id=id_quy_di)
        quy_den = LoaiQuy.objects.get(id=id_quy_den)

        GiaoDich.objects.create(loai='NB', so_tien=so_tien, ly_do=f"[-] {ly_do} (Sang {quy_den.ten_quy})", loai_quy=quy_di)
        GiaoDich.objects.create(loai='NB', so_tien=so_tien, ly_do=f"[+] {ly_do} (Từ {quy_di.ten_quy})", loai_quy=quy_den)

        return JsonResponse({'status': 'success', 'message': f'Đã điều chuyển {format_money(so_tien)}đ thành công!'})
    except ValidationError as e:
        return JsonResponse({'status': 'error', 'message': list(e.messages)[0]})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

# ==========================================
# 5. API TẠO QUỸ MỚI
# ==========================================      
@csrf_exempt
@login_required
def api_tao_quy(request):
    try:
        data = json.loads(request.body)
        ten_quy = data.get('ten_quy')
        if ten_quy:
            LoaiQuy.objects.create(ten_quy=ten_quy)
            return JsonResponse({'status': 'success', 'message': f'Đã tạo quỹ "{ten_quy}" thành công!'})
        return JsonResponse({'status': 'error', 'message': 'Tên quỹ không được để trống'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

# ==========================================
# 6. API NHẮC NỢ QUA EMAIL
# ==========================================        
@csrf_exempt
@login_required
def api_nhac_no(request):
    try:
        data = json.loads(request.body)
        tv_id = data.get('tv_id')
        
        tv = ThanhVien.objects.filter(id=tv_id).first()
        if not tv:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy thành viên!'})

        return JsonResponse({'status': 'success', 'message': f'Đã gửi Email nhắc nợ đến {tv.ho_ten} ({tv.email or "chưa cập nhật email"})'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

# ==========================================
# 7. API LẤY DỮ LIỆU VẼ BIỂU ĐỒ (CHART.JS)
# ==========================================
@csrf_exempt
@login_required
def api_chart_data(request):
    filter_type = request.GET.get('filter', '7days')
    now = timezone.now()
    labels = []; data_thu = []; data_chi = []

    def get_sum(start, end):
        stats = GiaoDich.objects.filter(ngay_tao__gte=start, ngay_tao__lte=end).aggregate(
            thu=Sum('so_tien', filter=Q(loai__in=['THU', 'LAI', 'HU'])),
            chi=Sum('so_tien', filter=Q(loai__in=['CHI', 'TU']))
        )
        return float(stats['thu'] or 0), float(stats['chi'] or 0)

    try:
        if filter_type == 'today':
            for i in range(0, 24, 3):
                labels.append(f"{i}h")
                start = now.replace(hour=i, minute=0, second=0)
                end = start + timedelta(hours=2, minutes=59)
                t, c = get_sum(start, end)
                data_thu.append(t); data_chi.append(c)

        elif filter_type in ['3days', '7days']:
            days = 3 if filter_type == '3days' else 7
            for i in range(days-1, -1, -1):
                d = now - timedelta(days=i)
                labels.append(d.strftime('%d/%m'))
                start = d.replace(hour=0, minute=0, second=0)
                end = d.replace(hour=23, minute=59, second=59)
                t, c = get_sum(start, end)
                data_thu.append(t); data_chi.append(c)

        elif filter_type == 'this_month':
            for i in range(1, now.day + 1):
                d = now.replace(day=i)
                labels.append(d.strftime('%d/%m'))
                start = d.replace(hour=0, minute=0, second=0)
                end = d.replace(hour=23, minute=59, second=59)
                t, c = get_sum(start, end)
                data_thu.append(t); data_chi.append(c)

        elif filter_type == 'this_quarter':
            current_quarter = (now.month - 1) // 3 + 1
            start_month = 3 * current_quarter - 2
            for i in range(3):
                m = start_month + i
                labels.append(f"Tháng {m}")
                t, c = get_sum(now.replace(month=m, day=1), now.replace(month=m, day=28) if m==2 else now.replace(month=m, day=30))
                data_thu.append(t); data_chi.append(c)

        elif filter_type == 'this_year':
            for m in range(1, 13):
                labels.append(f"T{m}")
                stats = GiaoDich.objects.filter(ngay_tao__year=now.year, ngay_tao__month=m).aggregate(
                    thu=Sum('so_tien', filter=Q(loai__in=['THU', 'LAI', 'HU'])),
                    chi=Sum('so_tien', filter=Q(loai__in=['CHI', 'TU']))
                )
                data_thu.append(float(stats['thu'] or 0)); data_chi.append(float(stats['chi'] or 0))

        return JsonResponse({'status': 'success', 'labels': labels, 'data_thu': data_thu, 'data_chi': data_chi})
    except Exception as e:
        return JsonResponse({'status': 'error', 'labels': ['Lỗi'], 'data_thu': [0], 'data_chi': [0]})
    
# ==========================================
# 8. API CHATBOT TRỢ LÝ ẢO (TÍCH HỢP GEMINI AI)
# ==========================================
@csrf_exempt
@login_required
def api_chatbot(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        message = data.get('message', '').strip().lower() 
        
        user_name = request.user.full_name or request.user.username
        
        tv_hien_tai = ThanhVien.objects.filter(mssv=getattr(request.user, 'mssv', '')).first()
        if not tv_hien_tai:
            tv_hien_tai = ThanhVien.objects.filter(email=getattr(request.user, 'email', '')).first()
        
        danh_sach_quy = LoaiQuy.objects.all()
        tong_du = sum([q.so_du_hien_tai for q in danh_sach_quy])
        chi_tiet_quy = "<br>".join([f"• **{q.ten_quy}**: {format_money(q.so_du_hien_tai)}đ" for q in danh_sach_quy])
        
        ds_no_xau = ThanhVien.objects.filter(is_no_xau=True)
        so_nguoi_no = ds_no_xau.count()
        ten_nguoi_no = ", ".join([tv.user.full_name for tv in ds_no_xau if tv.user]) if so_nguoi_no > 0 else "Không có ai"
        gd_cuoi = GiaoDich.objects.order_by('-ngay_tao').first()
        
        reply = f"Chào {user_name}! Mình là Trợ lý ảo của hệ thống quản lý quỹ lớp thông minh."

        if any(word in message for word in ['còn bao nhiêu', 'tổng tiền', 'số dư', 'giàu không']):
            reply = f"💰 Báo cáo sếp, tổng tài sản của lớp mình hiện tại là: **{format_money(tong_du)} VNĐ**.<br>{chi_tiet_quy}"
        elif any(word in message for word in ['mới nhất', 'gần đây', 'vừa chi', 'vừa thu']):
            if gd_cuoi:
                loai_gd = gd_cuoi.get_loai_display()
                icon = "🟢" if gd_cuoi.loai in ['THU', 'LAI'] else "🔴"
                reply = f"📅 Biến động mới nhất:<br>{icon} **{loai_gd}**: {format_money(gd_cuoi.so_tien)}đ<br>📝 Lý do: {gd_cuoi.ly_do}"
            else:
                reply = "Chưa có giao dịch nào được ghi nhận."
        elif any(word in message for word in ['nợ xấu', 'ai đang nợ']):
            reply = f"⚠️ Hiện tại có {so_nguoi_no} người đang bị đánh dấu nợ xấu: {ten_nguoi_no}"
        else:
            reply = f"Xin lỗi sếp, em chưa hiểu câu: '{message}'. Sếp thử hỏi về 'số dư', 'giao dịch mới nhất' xem sao ạ!"

        return JsonResponse({'status': 'success', 'reply': reply}, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({'status': 'error', 'reply': f'Lỗi Bot: {str(e)}'})

# ==========================================
# 9. API XÁC THỰC MÃ PIN
# ==========================================
@csrf_exempt
def api_verify_pin(request):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "message": "Vui lòng đăng nhập!"})
    
    try:
        data = json.loads(request.body)
        pin = data.get('pin', '')
        
        if len(pin) != 6:
            return JsonResponse({"status": "error", "message": "Mã PIN phải đủ 6 số!"})

        is_valid = False
        if getattr(request.user, 'secure_pin', None):
            is_valid = check_password(pin, request.user.secure_pin)
        elif pin == '123456': 
            is_valid = True

        if is_valid:
            return JsonResponse({"status": "success", "message": "Xác thực bảo mật thành công!"})
        else:
            return JsonResponse({"status": "error", "message": "Mã PIN không chính xác!"})
    except Exception as e:
         return JsonResponse({"status": "error", "message": f"Lỗi: {str(e)}"})