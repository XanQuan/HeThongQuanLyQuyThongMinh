# File: quanlyquy/api_views.py
import sys
import io
from django.db.models import Sum, Q
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
from django.core.exceptions import ValidationError

from .models import GiaoDich, ThanhVien, LoaiQuy
from .utils import format_money
from google import genai

# --- HÀM HỖ TRỢ XỬ LÝ SỐ TIỀN CÓ DẤU CHẤM ---
def clean_amount(amount_str):
    if not amount_str: return 0
    # Xóa dấu chấm để biến "20.000" thành 20000
    return int(str(amount_str).replace('.', ''))

@login_required
@require_POST
def api_nop_quy_ho(request):
    try:
        data = json.loads(request.body)
        tv_id = data.get('tv_id')
        so_tien = clean_amount(data.get('so_tien'))
        ly_do = data.get('ly_do')

        tv = ThanhVien.objects.get(id=tv_id)
        quy = LoaiQuy.objects.first()
        if not quy:
            return JsonResponse({'status': 'error', 'message': 'Chưa có Quỹ. Hãy vào Admin tạo quỹ!'})

        GiaoDich.objects.create(loai='THU', so_tien=so_tien, ly_do=ly_do, loai_quy=quy, thanh_vien=tv)

        if tv.is_no_xau:
            tv.is_no_xau = False
            tv.save()

        return JsonResponse({'status': 'success', 'message': f'Đã ghi nhận {format_money(so_tien)}đ từ {tv.ho_ten}'})
    except ValidationError as e:
        return JsonResponse({'status': 'error', 'message': list(e.messages)[0]})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Lỗi: {str(e)}'})

@login_required
def api_nop_quy(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tv = ThanhVien.objects.filter(email=request.user.email).first()
            
            quy = LoaiQuy.objects.first()
            if not quy:
                return JsonResponse({'status': 'error', 'message': 'Chưa có Quỹ. Hãy vào Admin tạo quỹ!'})
            
            so_tien = clean_amount(data.get('so_tien'))
            ly_do = data.get('ly_do') or f"{request.user.username} nộp quỹ"
            
            GiaoDich.objects.create(loai='THU', so_tien=so_tien, ly_do=ly_do, loai_quy=quy, thanh_vien=tv)
            return JsonResponse({'status': 'success', 'message': 'Nộp quỹ thành công!'})
        except ValidationError as e:
            return JsonResponse({'status': 'error', 'message': list(e.messages)[0]})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Lỗi: {str(e)}'})

@login_required
def api_tam_ung(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tv = ThanhVien.objects.filter(email=request.user.email).first()
            
            quy = LoaiQuy.objects.first()
            if not quy:
                return JsonResponse({'status': 'error', 'message': 'Chưa có Quỹ. Hãy vào Admin tạo quỹ!'})

            so_tien = clean_amount(data.get('so_tien')) 
            ly_do = data.get('ly_do') or f"Tạm ứng cho {request.user.username}"
            
            # Hàm này sẽ tự động gọi logic chặn thâm hụt tiền trong models.py
            GiaoDich.objects.create(loai='TU', so_tien=so_tien, ly_do=ly_do, loai_quy=quy, thanh_vien=tv)
            return JsonResponse({'status': 'success', 'message': 'Phiếu tạm ứng đã được lưu!'})
        except ValidationError as e:
            # Nếu tiền quỹ không đủ, thông báo sẽ văng ra ở đây
            return JsonResponse({'status': 'error', 'message': list(e.messages)[0]})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Lỗi: {str(e)}'})

@login_required
def api_chuyen_noi_bo(request):
    if request.method == 'POST':
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
        
@login_required
def api_tao_quy(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ten_quy = data.get('ten_quy')
            if ten_quy:
                LoaiQuy.objects.create(ten_quy=ten_quy)
                return JsonResponse({'status': 'success', 'message': f'Đã tạo quỹ "{ten_quy}" thành công!'})
            return JsonResponse({'status': 'error', 'message': 'Tên quỹ không được để trống'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
        
@login_required
def api_nhac_no(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tv_id = data.get('tv_id')
            
            tv = ThanhVien.objects.filter(id=tv_id).first()
            if not tv:
                return JsonResponse({'status': 'error', 'message': 'Không tìm thấy thành viên!'})

            return JsonResponse({'status': 'success', 'message': f'Đã gửi Email nhắc nợ đến {tv.ho_ten} ({tv.email or "chưa cập nhật email"})'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

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
# 6. API CHATBOT TRỢ LÝ ẢO (TÍCH HỢP GEMINI AI)
# ==========================================
@login_required
def api_chatbot(request):
    if request.method == 'POST':
        import json
        from .utils import format_money
        
        try:
            data = json.loads(request.body.decode('utf-8'))
            # Biến tin nhắn thành chữ thường để dễ nhận diện từ khóa
            message = data.get('message', '').strip().lower() 
            
            # --- BƯỚC 1: LẤY TẤT TẦN TẬT DỮ LIỆU TỪ DATABASE ---
            user_name = request.user.full_name or request.user.username
            tv_hien_tai = ThanhVien.objects.filter(email=request.user.email).first()
            
            # 1.1 Tổng quỹ
            danh_sach_quy = LoaiQuy.objects.all()
            tong_du = sum([q.so_du_hien_tai for q in danh_sach_quy])
            
            # 1.2 Chi tiết từng quỹ
            chi_tiet_quy = "<br>".join([f"• **{q.ten_quy}**: {format_money(q.so_du_hien_tai)}đ" for q in danh_sach_quy])
            
            # 1.3 Danh sách nợ xấu
            ds_no_xau = ThanhVien.objects.filter(is_no_xau=True)
            so_nguoi_no = ds_no_xau.count()
            ten_nguoi_no = ", ".join([tv.user.full_name for tv in ds_no_xau]) if so_nguoi_no > 0 else "Không có ai"
            
            # 1.4 Giao dịch gần nhất
            gd_cuoi = GiaoDich.objects.order_by('-ngay_tao').first()
            
            # --- BƯỚC 2: BỘ NÃO NHẬN DIỆN TỪ KHÓA (INTENT MATCHING) ---
            reply = f"Chào {user_name}! Mình là Trợ lý ảo của hệ thống quản lý quỹ lớp thông minh. Bạn có thể hỏi mình về **số dư**, **tình trạng nợ**, hoặc **giao dịch gần đây** nhé!"

            # Nhóm 1: Hỏi thăm / Chào hỏi
            if any(word in message for word in ['chào', 'hello', 'hi', 'ê bot']):
                reply = f"Chào sếp {user_name}! Hôm nay sếp muốn tra cứu thông tin gì nào?"
            
            # Nhóm 2: Hỏi TỔNG TIỀN QUỸ
            elif any(word in message for word in ['còn bao nhiêu', 'tổng tiền', 'số dư', 'giàu không', 'tổng quỹ']):
                reply = f"💰 Báo cáo sếp, tổng tài sản của lớp mình hiện tại là: **{format_money(tong_du)} VNĐ**.<br>Rất minh bạch và rõ ràng nhé!"
                
            # Nhóm 3: Hỏi CHI TIẾT TỪNG QUỸ (Tiền mặt, Ngân hàng...)
            elif any(word in message for word in ['chi tiết', 'từng quỹ', 'tiền mặt', 'ngân hàng', 'ở đâu']):
                if danh_sach_quy:
                    reply = f"🏦 Chi tiết các két sắt của lớp mình đây:<br>{chi_tiet_quy}"
                else:
                    reply = "Lớp mình chưa tạo quỹ nào cả. Bạn vào trang Admin tạo quỹ đi nhé!"
                    
            # Nhóm 4: Hỏi NỢ CÁ NHÂN (Người đang chat)
            elif any(word in message for word in ['tôi có nợ', 'mình có nợ', 'đóng chưa', 'thiếu tiền', 'nợ không']):
                if tv_hien_tai:
                    if tv_hien_tai.is_no_xau:
                        reply = f"🚨 Cảnh báo đỏ! Kiểm tra hệ thống thấy {user_name} **ĐANG BỊ ĐÁNH DẤU NỢ XẤU**. Mau nộp lúa đi bạn êi!"
                    else:
                        reply = f"✨ Quá đỉnh! {user_name} là thành viên gương mẫu, **KHÔNG NỢ** một đồng nào. Xứng đáng nhận bằng khen!"
                else:
                    reply = "Tài khoản của bạn chưa được liên kết với hồ sơ thành viên nào trong lớp nên mình không tra nợ được."
                    
            # Nhóm 5: Hỏi DANH SÁCH CON NỢ TRONG LỚP
            elif any(word in message for word in ['ai đang nợ', 'danh sách nợ', 'đứa nào nợ', 'chưa đóng', 'ai thiếu']):
                if so_nguoi_no == 0:
                    reply = "🎉 Tuyệt vời! Cả lớp mình đóng quỹ đầy đủ, không có ai bị nợ xấu cả."
                else:
                    reply = f"🕵️‍♂️ Hệ thống ghi nhận có **{so_nguoi_no} người** đang nợ tiền quỹ lớp.<br>Danh sách bêu tên: **{ten_nguoi_no}**."
                    
            # Nhóm 6: Hỏi GIAO DỊCH MỚI NHẤT
            elif any(word in message for word in ['mới nhất', 'gần đây', 'vừa chi', 'vừa thu', 'mới chi', 'lịch sử']):
                if gd_cuoi:
                    loai_gd = "Thu vào" if gd_cuoi.loai_giao_dich == 'THU' else "Chi ra"
                    icon = "🟢" if gd_cuoi.loai_giao_dich == 'THU' else "🔴"
                    reply = f"📅 Biến động mới nhất:<br>{icon} **{loai_gd}**: {format_money(gd_cuoi.so_tien)}đ<br>📝 Lý do: {gd_cuoi.ly_do}<br>Vào lúc: {gd_cuoi.ngay_tao.strftime('%d/%m/%Y %H:%M')}"
                else:
                    reply = "Sổ quỹ đang trắng tinh, chưa có giao dịch nào được ghi nhận cả."
            
            # Nhóm 7: Khen chê vui vẻ
            elif any(word in message for word in ['thông minh', 'giỏi', 'xịn', 'tuyệt']):
                reply = f"Hehe, cảm ơn {user_name} quá khen! Đồ án điểm A+ là cái chắc! 😎"
            elif any(word in message for word in ['ngu', 'dở']):
                reply = "Bot đang học việc thôi, sếp thông cảm nha! 😭"

            # --- BƯỚC 3: TRẢ KẾT QUẢ VỀ FRONTEND ---
            return JsonResponse({'status': 'success', 'reply': reply}, json_dumps_params={'ensure_ascii': False})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'reply': f'❌ Lỗi vận hành Bot: {str(e)}'}, json_dumps_params={'ensure_ascii': False})