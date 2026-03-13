import json
import requests
import time
import random
import csv
from datetime import datetime, timedelta

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q, Count
from django.db.models.functions import TruncMonth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

# Gom tất cả Model vào 1 chỗ cho dễ quản lý
from .models import (
    GiaoDich, ThanhVien, TaiSan, LoaiQuy, DotThu, 
    MucTieuQuy, SuKienNhacViec, User, QuaTang, 
    NhiemVu, BieuQuyet, HuyHieuThanhVien, QATestingLog, 
    LichSuWebhook, DanhMucThuChi
)
from .utils import format_money

# ==========================================
# 1. HÀM BỔ TRỢ (HELPERS)
# ==========================================
def is_thu_quy(user):
    return user.is_active and (user.is_staff or user.is_superuser or getattr(user, 'role', '') == 'ADMIN')

def get_percent_change(current, previous):
    if not previous or previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100, 1)

# ==========================================
# 2. HỆ THỐNG XÁC THỰC (AUTH)
# ==========================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('login_redirect')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me')
        recaptcha_response = request.POST.get('g-recaptcha-response')

        if not recaptcha_response:
            messages.error(request, 'Vui lòng xác thực "Tôi không phải là người máy"!')
            return render(request, 'quanlyquy/login.html', {'username': username})

        data = {'secret': settings.RECAPTCHA_PRIVATE_KEY, 'response': recaptcha_response}
        try:
            r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data, timeout=5)
            if not r.json().get('success'):
                messages.error(request, 'Xác thực Captcha thất bại!')
                return render(request, 'quanlyquy/login.html', {'username': username})
        except:
            messages.error(request, 'Lỗi kết nối xác thực!')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            request.session.set_expiry(1209600 if remember_me else 0)
            messages.success(request, f'Chào mừng {user.full_name or user.username} quay trở lại!')
            return redirect('login_redirect')
        else:
            messages.error(request, 'Tài khoản không tồn tại hoặc sai mật khẩu!')
            
    return render(request, 'quanlyquy/login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        full_name = request.POST.get('full_name', '').strip()
        mssv = request.POST.get('mssv', '').strip()

        context = {'username': username, 'email': email, 'full_name': full_name, 'mssv': mssv}

        if password != confirm_password:
            messages.error(request, "Mật khẩu xác nhận không khớp!")
            return render(request, 'quanlyquy/register.html', context)
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "Tên đăng nhập này đã tồn tại!")
            return render(request, 'quanlyquy/register.html', context)

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.full_name = full_name
            user.mssv = mssv
            user.role = 'MEMBER'   
            user.is_staff = False  
            user.save()
            
            messages.success(request, "Tạo tài khoản thành công! Vui lòng đăng nhập.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Lỗi tạo tài khoản: {str(e)}")
            return render(request, 'quanlyquy/register.html', context)
            
    return render(request, 'quanlyquy/register.html')

@login_required
def login_redirect_view(request):
    if is_thu_quy(request.user):
        return redirect('/admin/') 
    else:
        return redirect('dashboard')

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, "Bạn đã đăng xuất khỏi hệ thống.")
        return redirect('login')
    return redirect('/')

# ==========================================
# 3. TRANG CHỦ & DASHBOARD
# ==========================================
@login_required
def dashboard(request):
    now = timezone.now()
    thang_nay = now.month
    nam_nay = now.year
    
    first_day_this_month = now.replace(day=1)
    last_day_last_month = first_day_this_month - timedelta(days=1)
    thang_truoc = last_day_last_month.month
    nam_truoc = last_day_last_month.year

    thu_thang_nay = GiaoDich.objects.filter(loai__in=['THU', 'LAI', 'HU'], ngay_tao__month=thang_nay, ngay_tao__year=nam_nay).aggregate(Sum('so_tien'))['so_tien__sum'] or 0
    chi_thang_nay = GiaoDich.objects.filter(loai__in=['CHI', 'TU'], ngay_tao__month=thang_nay, ngay_tao__year=nam_nay).aggregate(Sum('so_tien'))['so_tien__sum'] or 0
    
    thu_thang_truoc = GiaoDich.objects.filter(loai__in=['THU', 'LAI', 'HU'], ngay_tao__month=thang_truoc, ngay_tao__year=nam_truoc).aggregate(Sum('so_tien'))['so_tien__sum'] or 0
    chi_thang_truoc = GiaoDich.objects.filter(loai__in=['CHI', 'TU'], ngay_tao__month=thang_truoc, ngay_tao__year=nam_truoc).aggregate(Sum('so_tien'))['so_tien__sum'] or 0

    thu_percent = get_percent_change(thu_thang_nay, thu_thang_truoc)
    chi_percent = get_percent_change(chi_thang_nay, chi_thang_truoc)

    thu_tong = GiaoDich.objects.filter(loai__in=['THU', 'LAI', 'HU']).aggregate(Sum('so_tien'))['so_tien__sum'] or 0
    chi_tong = GiaoDich.objects.filter(loai__in=['CHI', 'TU']).aggregate(Sum('so_tien'))['so_tien__sum'] or 0
    so_du_raw = thu_tong - chi_tong

    stats = (GiaoDich.objects.annotate(month=TruncMonth('ngay_tao'))
             .values('month').annotate(
                 thu=Sum('so_tien', filter=Q(loai__in=['THU', 'LAI', 'HU'])),
                 chi=Sum('so_tien', filter=Q(loai__in=['CHI', 'TU']))
             ).order_by('-month')[:6])
    
    stats_list = list(stats)[::-1]
    chart_months = [s['month'].strftime("Th%m/%y") for s in stats_list if s['month']]
    chart_thu = [float(s['thu'] or 0) for s in stats_list]
    chart_chi = [float(s['chi'] or 0) for s in stats_list]

    is_admin = is_thu_quy(request.user)
    user_role_name = "Thủ quỹ hệ thống" if is_admin else "Thành viên lớp"
    member_section_title = "Hồ sơ Thành Viên" if is_admin else "Bạn bè cùng lớp"

    ai_alerts = []
    if is_admin:
        late_night_txs = GiaoDich.objects.filter(loai='CHI', ngay_tao__hour__gte=23) | GiaoDich.objects.filter(loai='CHI', ngay_tao__hour__lte=5)
        if late_night_txs.exists():
            ai_alerts.append({
                'type': 'danger',
                'title': 'Cảnh báo khung giờ nhạy cảm',
                'desc': f'Có {late_night_txs.count()} khoản chi được tạo vào ban đêm. Khuyến nghị kiểm tra lại tính minh bạch.'
            })
        
        today_chi_count = GiaoDich.objects.filter(loai='CHI', ngay_tao__date=now.date()).count()
        if today_chi_count >= 3:
            ai_alerts.append({
                'type': 'warning',
                'title': 'Phát hiện chia nhỏ chi tiêu',
                'desc': f'Đã có {today_chi_count} khoản chi trong hôm nay. Trí tuệ nhân tạo đề xuất nên gộp chung để dễ kê khai.'
            })
        
    top_dai_gia = ThanhVien.objects.annotate(
        tong_nop=Sum('giaodich__so_tien', filter=Q(giaodich__loai='THU'))
    ).order_by('-tong_nop')[:5]

    context = {
        'so_du': format_money(so_du_raw),
        'tong_thu': format_money(thu_tong),
        'tong_chi': format_money(chi_tong),
        'thu_nay': format_money(thu_thang_nay),
        'chi_nay': format_money(chi_thang_nay),
        'thu_percent': thu_percent,
        'chi_percent': chi_percent,
        'tai_san': TaiSan.objects.all().order_by('-ngay_mua')[:3],
        'thanh_viens': ThanhVien.objects.all().order_by('ho_ten')[:12],
        'giao_dich_moi': GiaoDich.objects.all().select_related('thanh_vien').order_by('-ngay_tao')[:5],
        'muc_tieu_quy': MucTieuQuy.objects.filter(hoan_thanh=False)[:3],
        'su_kien_nhac_viec': SuKienNhacViec.objects.filter(ngay_dien_ra__gte=now.date())[:4],
        'chart_months': json.dumps(chart_months),
        'chart_thu': json.dumps(chart_thu),
        'chart_chi': json.dumps(chart_chi),
        'is_admin': is_admin,
        'user_role_name': user_role_name,
        'member_section_title': member_section_title,
        'ai_alerts': ai_alerts,
        'top_dai_gia': top_dai_gia,
    }
    return render(request, 'quanlyquy/dashboard.html', context)

# ==========================================
# 4. CÁC TRANG CHỨC NĂNG CHÍNH
# ==========================================
@login_required
def giao_dich_view(request):
    giao_dich_list_raw = GiaoDich.objects.all().select_related('thanh_vien').order_by('-ngay_tao')
    q = request.GET.get('search')
    if q:
        giao_dich_list_raw = giao_dich_list_raw.filter(
            Q(thanh_vien__ho_ten__icontains=q) | Q(thanh_vien__mssv__icontains=q) | Q(ly_do__icontains=q)
        )
    for gd in giao_dich_list_raw:
        gd.so_tien_format = format_money(gd.so_tien)

    paginator = Paginator(giao_dich_list_raw, 15)
    page_number = request.GET.get('page')
    giao_dich_list = paginator.get_page(page_number)

    return render(request, 'quanlyquy/page_giao_dich.html', {
        'giao_dich_list': giao_dich_list,
        'search_query': q or "",
        'is_admin': is_thu_quy(request.user)
    })

@login_required
def thong_ke_view(request):
    is_admin = is_thu_quy(request.user)
    
    # Chart 1: Dòng tiền 6 tháng
    stats = GiaoDich.objects.annotate(month=TruncMonth('ngay_tao')).values('month').annotate(
        thu=Sum('so_tien', filter=Q(loai__in=['THU', 'LAI', 'HU'])),
        chi=Sum('so_tien', filter=Q(loai__in=['CHI', 'TU']))
    ).order_by('-month')[:6]
    
    stats_list = list(stats)[::-1]
    chart1_labels = [s['month'].strftime("Th%m/%y") for s in stats_list if s['month']]
    chart1_thu = [float(s['thu'] or 0) for s in stats_list]
    chart1_chi = [float(s['chi'] or 0) for s in stats_list]

    # Chart 2: Cơ cấu chi tiêu (Đã tối ưu: Lấy theo Danh mục thay vì Lý do)
    chi_tieu_db = GiaoDich.objects.filter(loai='CHI').values('danh_muc__ten_danh_muc').annotate(
        tong_chi=Sum('so_tien')
    ).order_by('-tong_chi')[:5]
    
    chart2_labels = [item['danh_muc__ten_danh_muc'] or "Chi phí khác" for item in chi_tieu_db]
    chart2_data = [float(item['tong_chi']) for item in chi_tieu_db]

    # Chart 3: Top đóng góp
    top_members = ThanhVien.objects.annotate(
        tong_dong_gop=Sum('giaodich__so_tien', filter=Q(giaodich__loai='THU'))
    ).order_by('-tong_dong_gop')[:5]
    chart3_labels = [m.ho_ten for m in top_members]
    chart3_data = [float(m.tong_dong_gop or 0) for m in top_members]

    # Chart 4: Thống kê nợ theo đợt thu
    dot_thu_list = DotThu.objects.all().order_by('-id')[:4]
    tong_tv = ThanhVien.objects.count()
    chart4_labels = []; chart4_da_thu = []; chart4_no = []
    
    for dt in dot_thu_list:
        chart4_labels.append(dt.ten_dot)
        da_thu = float(GiaoDich.objects.filter(dot_thu=dt, loai='THU').aggregate(Sum('so_tien'))['so_tien__sum'] or 0)
        tong_can_thu = float(dt.so_tien_moi_nguoi * tong_tv)
        chart4_da_thu.append(da_thu)
        chart4_no.append(max(0, tong_can_thu - da_thu))

    # Chart 5: Tồn quỹ
    quys = LoaiQuy.objects.all()
    chart5_labels = []; chart5_data = []
    for q in quys:
        chart5_labels.append(q.ten_quy)
        chart5_data.append(max(0, float(q.so_du_hien_tai)))

    context = {
        'is_admin': is_admin,
        'user_role_name': "Thủ quỹ hệ thống" if is_admin else "Thành viên lớp",
        'chart1_labels': json.dumps(chart1_labels),
        'chart1_thu': json.dumps(chart1_thu),
        'chart1_chi': json.dumps(chart1_chi),
        'chart2_labels': json.dumps(chart2_labels),
        'chart2_data': json.dumps(chart2_data),
        'chart3_labels': json.dumps(chart3_labels),
        'chart3_data': json.dumps(chart3_data),
        'chart4_labels': json.dumps(chart4_labels),
        'chart4_da_thu': json.dumps(chart4_da_thu),
        'chart4_no': json.dumps(chart4_no),
        'chart5_labels': json.dumps(chart5_labels),
        'chart5_data': json.dumps(chart5_data),
    }
    return render(request, 'quanlyquy/thong_ke.html', context)

@login_required
def tien_do_thu_view(request):
    is_admin = is_thu_quy(request.user)
    dot_thu = DotThu.objects.order_by('-id').first()
    
    total_needed = 0; total_collected = 0; percent = 0
    thanh_viens = ThanhVien.objects.all()
    
    if dot_thu:
        total_needed = dot_thu.so_tien_moi_nguoi * thanh_viens.count()
        total_collected = GiaoDich.objects.filter(dot_thu=dot_thu, loai='THU').aggregate(Sum('so_tien'))['so_tien__sum'] or 0
        if total_needed > 0:
            percent = int((total_collected / total_needed) * 100)

    context = {
        'is_admin': is_admin,
        'user_role_name': "Thủ quỹ hệ thống" if is_admin else "Thành viên lớp",
        'dot_thu': dot_thu,
        'total_needed': format_money(total_needed),
        'total_collected': format_money(total_collected),
        'total_remaining': format_money(max(0, total_needed - total_collected)),
        'percent': percent,
        'remaining_percent': max(0, 100 - percent),
        'thanh_vien_stats': thanh_viens,
    }
    return render(request, 'quanlyquy/page_tien_do.html', context)

@login_required
@user_passes_test(is_thu_quy, login_url='/')
def cai_dat_view(request):
    return render(request, 'quanlyquy/page_cai_dat.html', {'is_admin': True})

@login_required
def gamification_view(request):
    is_admin = (request.user.role == 'ADMIN' or request.user.is_superuser)
    nhiem_vu_list = NhiemVu.objects.filter(deleted_at__isnull=True)
    bieu_quyet_active = BieuQuyet.objects.filter(dang_mo=True)
    
    top_dai_gia = ThanhVien.objects.annotate(
        tong_nop=Sum('giaodich__so_tien', filter=Q(giaodich__loai='THU'))
    ).order_by('-tong_nop')[:3]

    context = {
        'nhiem_vu_list': nhiem_vu_list,
        'bieu_quyet_active': bieu_quyet_active,
        'top_dai_gia': top_dai_gia,
        'is_admin': is_admin,
        'has_vong_quay': True 
    }
    return render(request, 'quanlyquy/gamification.html', context)

@login_required
def export_misa_view(request):
    is_admin = getattr(request.user, 'role', '') == 'ADMIN' or request.user.is_superuser
    if not is_admin:
        return HttpResponse("Bạn không có quyền thực hiện thao tác này.", status=403)

    giao_dich_list = GiaoDich.objects.all().order_by('-ngay_tao')

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="SaoKe_QuyLop_MISA_FundFlow.csv"'
    response.write(u'\ufeff'.encode('utf8'))

    writer = csv.writer(response)
    writer.writerow(['Ngày hạch toán', 'Ngày chứng từ', 'Số chứng từ', 'Diễn giải', 'Tài khoản Nợ', 'Tài khoản Có', 'Số tiền', 'Đối tượng', 'Loại giao dịch'])

    for gd in giao_dich_list:
        tk_no = "1111"
        tk_co = "1111"
        if gd.loai in ['THU', 'LAI']:
            tk_no = "1111"
            tk_co = "511" 
        elif gd.loai in ['CHI', 'TU']:
            tk_no = "811"
            tk_co = "1111"

        is_an_danh = getattr(gd, 'is_an_danh', False)
        ten_nguoi_nop = "Nhà hảo tâm ẩn danh" if is_an_danh else (gd.thanh_vien.ho_ten if gd.thanh_vien else "Hệ thống")
        
        writer.writerow([
            gd.ngay_tao.strftime("%d/%m/%Y"), gd.ngay_tao.strftime("%d/%m/%Y"), 
            f"FF-{gd.id:05d}", gd.ly_do, tk_no, tk_co, gd.so_tien, ten_nguoi_nop, gd.get_loai_display()
        ])
    return response

@login_required
def settings_view(request):
    is_admin = getattr(request.user, 'role', '') == 'ADMIN' or request.user.is_superuser
    if not is_admin: return redirect('/') 
    return render(request, 'quanlyquy/settings.html', {'is_admin': is_admin, 'user_role_name': "Thủ quỹ hệ thống"})

@login_required
def qa_testing_view(request):
    is_admin = getattr(request.user, 'role', '') == 'ADMIN' or request.user.is_superuser
    if not is_admin: return redirect('/')
    return render(request, 'quanlyquy/qa_testing.html', {'is_admin': is_admin, 'user_role_name': "Thủ quỹ hệ thống"})

@login_required
def store_view(request):
    is_admin = getattr(request.user, 'role', '') == 'ADMIN' or request.user.is_superuser
    items = QuaTang.objects.all()
    context = {
        'items': items,
        'is_admin': is_admin,
        'user_role_name': "Thủ quỹ hệ thống" if is_admin else "Thành viên lớp" 
    }
    return render(request, 'quanlyquy/store.html', context)

# ==========================================
# 5. API XỬ LÝ DỮ LIỆU BẰNG AJAX
# ==========================================
@csrf_exempt
def api_chaos_action(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        user = request.user if request.user.is_authenticated else None

        if action == 'TIMEOUT_504':
            time.sleep(1.5)
            QATestingLog.objects.create(
                nguoi_test=user,
                loai_test="ROT_MANG_BANK",
                du_lieu_phat_sinh={"error": "504 Gateway Timeout", "rollback_id": f"RB-{random.randint(1000, 9999)}"},
                trang_thai="ROLLBACK_SUCCESS"
            )
            return JsonResponse({"status": "error", "message": "[FATAL] Lỗi 504 Gateway Timeout kết nối Ngân Hàng.<br>[SYS] Rollback transaction initiated...<br>[SUCCESS] DB Rollback thành công, không mất tiền."})

        elif action == 'SEED_DATA':
            try:
                quy = LoaiQuy.objects.first()
                if quy:
                    # Tối ưu tốc độ bơm bằng bulk_create
                    GiaoDich.objects.bulk_create([
                        GiaoDich(loai='THU', so_tien=random.randint(10, 50)*1000, loai_quy=quy, ly_do=f"Auto Seed Data #{i}", is_an_danh=True)
                        for i in range(50)
                    ])
                    QATestingLog.objects.create(
                        nguoi_test=user, loai_test="STRESS_TEST_DB",
                        du_lieu_phat_sinh={"records_inserted": 50, "table": "GiaoDich"},
                        trang_thai="SUCCESS"
                    )
                    return JsonResponse({"status": "warn", "message": "[WORKING] Seeding data...<br>[SUCCESS] Đã bơm 50 giao dịch ảo vào Database thành công! Hãy check trang Tổng quan."})
                else:
                    return JsonResponse({"status": "error", "message": "[ERROR] Không tìm thấy Quỹ nào để bơm dữ liệu. Vui lòng tạo Quỹ trước."})
            except Exception as e:
                return JsonResponse({"status": "error", "message": f"[ERROR] Bơm dữ liệu thất bại: {str(e)}"})

        elif action == 'RATE_LIMIT':
            QATestingLog.objects.create(
                nguoi_test=user, loai_test="DDOS_ATTACK",
                du_lieu_phat_sinh={"requests_per_sec": 500, "ip_blocked": "192.168.1.100"},
                trang_thai="BLOCKED"
            )
            return JsonResponse({"status": "info", "message": "[ALERT] Phát hiện lưu lượng bất thường: 500 req/s.<br>[SECURITY] Kích hoạt Firewall. Đã block IP tấn công."})

    return JsonResponse({"status": "error", "message": "Invalid request"})

# ==========================================
# 6. API WEBHOOK NGÂN HÀNG (TỰ ĐỘNG GẠCH NỢ)
# ==========================================
@csrf_exempt
def sepay_webhook(request):
    if request.method == 'POST':
        try:
            # 1. Nhận dữ liệu JSON từ Ngân Hàng / SePay bắn sang
            data = json.loads(request.body)
            
            # Giả định cấu trúc JSON chuẩn của SePay
            ma_gd = data.get('id', '') 
            so_tien = data.get('transferAmount', 0)
            noi_dung_ck = data.get('content', '').upper() # Chuyển hết thành in hoa

            # 2. Lưu NGAY LẬP TỨC vào Database để làm Bằng chứng đối soát
            webhook_log = LichSuWebhook.objects.create(
                ma_giao_dich_ngan_hang=str(ma_gd),
                so_tien=so_tien,
                raw_payload=data,
                trang_thai_xu_ly=False
            )

            # 3. Thuật toán "Săn tìm MSSV" trong Nội dung chuyển khoản
            thanh_vien_nhan_dien = None
            danh_sach_tv = ThanhVien.objects.filter(deleted_at__isnull=True)
            
            for tv in danh_sach_tv:
                if tv.mssv and tv.mssv.upper() in noi_dung_ck:
                    thanh_vien_nhan_dien = tv
                    break
            
            # Lấy quỹ đầu tiên làm quỹ mặc định để cộng tiền
            quy_mac_dinh = LoaiQuy.objects.filter(deleted_at__isnull=True).first()

            # 4. Nếu tìm thấy cả Sinh viên và Quỹ -> Tiến hành tự động gạch nợ
            if thanh_vien_nhan_dien and quy_mac_dinh:
                GiaoDich.objects.create(
                    loai='THU',
                    so_tien=so_tien,
                    loai_quy=quy_mac_dinh,
                    thanh_vien=thanh_vien_nhan_dien,
                    ly_do=f"[AUTO] CK qua Bank: {noi_dung_ck}",
                    is_an_danh=False
                )
                # Đánh dấu đã xử lý thành công
                webhook_log.trang_thai_xu_ly = True
                webhook_log.save()
                
                return JsonResponse({"status": "success", "message": f"Đã gạch nợ tự động cho {thanh_vien_nhan_dien.ho_ten}"})
            
            # Nếu CK không ghi mssv -> Đẩy vào danh sách chờ rà soát tay
            return JsonResponse({"status": "skipped", "message": "Giao dịch lưu thành công nhưng không tìm thấy MSSV hợp lệ"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Lỗi hệ thống: {str(e)}"}, status=500)
            
    return JsonResponse({"status": "invalid_method", "message": "Chỉ nhận phương thức POST"}, status=405)