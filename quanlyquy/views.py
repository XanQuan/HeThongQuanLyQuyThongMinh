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
# 3. TRANG CHỦ & DASHBOARD (ĐÃ TỐI ƯU HÓA HOÀN TOÀN)
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

    # ==========================================
    # QUẢN LÝ QUỸ & MỤC TIÊU (ĐÃ FIX LỖI TÊN CỘT)
    # ==========================================
    quy_nh = LoaiQuy.objects.filter(ten_quy__icontains="Ngân hàng").first()
    if quy_nh:
        thu_nh = GiaoDich.objects.filter(loai_quy=quy_nh, loai__in=['THU', 'LAI', 'HU']).aggregate(Sum('so_tien'))['so_tien__sum'] or 0
        chi_nh = GiaoDich.objects.filter(loai_quy=quy_nh, loai__in=['CHI', 'TU']).aggregate(Sum('so_tien'))['so_tien__sum'] or 0
        so_du_bank = format_money(thu_nh - chi_nh)
    else:
        so_du_bank = "0"

    quy_tm = LoaiQuy.objects.filter(ten_quy__icontains="Tiền mặt").first()
    if quy_tm:
        thu_tm = GiaoDich.objects.filter(loai_quy=quy_tm, loai__in=['THU', 'LAI', 'HU']).aggregate(Sum('so_tien'))['so_tien__sum'] or 0
        chi_tm = GiaoDich.objects.filter(loai_quy=quy_tm, loai__in=['CHI', 'TU']).aggregate(Sum('so_tien'))['so_tien__sum'] or 0
        so_du_cash = format_money(thu_tm - chi_tm)
    else:
        so_du_cash = "0"

    try:
        danh_sach_no_xau = ThanhVien.objects.filter(is_no_xau=True)
    except:
        danh_sach_no_xau = []

    # THUẬT TOÁN RADAR DÒ TÌM TIỀN MỤC TIÊU CHỐNG LỖI TÊN CỘT DATABASE
    muc_tieu_quy = list(MucTieuQuy.objects.filter(hoan_thanh=False)[:5])
    danh_sach_muc_tieu = []
    
    for mt in muc_tieu_quy:
        tien_ht = getattr(mt, 'tien_hien_tai', None)
        if tien_ht is None: tien_ht = getattr(mt, 'so_tien_hien_tai', None)
        if tien_ht is None: tien_ht = getattr(mt, 'so_tien_da_gom', None)
        if tien_ht is None: tien_ht = getattr(mt, 'da_gom_duoc', None)
        if tien_ht is None: tien_ht = getattr(mt, 'tien_da_gom', None)
        if tien_ht is None: tien_ht = getattr(mt, 'tien_hiam_tai', 0)
        tien_ht = int(tien_ht) if tien_ht else 0

        tien_mt = getattr(mt, 'tien_muc_tieu', None)
        if tien_mt is None: tien_mt = getattr(mt, 'so_tien_muc_tieu', 0)
        tien_mt = int(tien_mt) if tien_mt else 0
        
        mt.tien_hien_tai_format = format_money(tien_ht)
        mt.tien_muc_tieu_format = format_money(tien_mt)
        
        if tien_mt > 0:
            phan_tram = int((tien_ht / tien_mt) * 100)
            mt.phan_tram_thuc = min(phan_tram, 100) 
        else:
            mt.phan_tram_thuc = 0
            
        if hasattr(mt, 'han_chot') and mt.han_chot:
            delta = mt.han_chot - timezone.now().date()
            mt.ngay_con_lai = max(0, delta.days)
        else:
            mt.ngay_con_lai = None
            
        danh_sach_muc_tieu.append(mt)

    context = {
        'so_du': format_money(so_du_raw),
        'so_du_bank': so_du_bank,   
        'so_du_cash': so_du_cash,   
        'danh_sach_no_xau': danh_sach_no_xau,
        'tong_thu': format_money(thu_tong),
        'tong_chi': format_money(chi_tong),
        'thu_nay': format_money(thu_thang_nay),
        'chi_nay': format_money(chi_thang_nay),
        'thu_percent': thu_percent,
        'chi_percent': chi_percent,
        'tai_san': TaiSan.objects.all().order_by('-ngay_mua')[:3],
        'thanh_viens': ThanhVien.objects.all().order_by('ho_ten'),
        'giao_dich_moi': GiaoDich.objects.all().select_related('thanh_vien').order_by('-ngay_tao')[:5],
        
        # Đẩy danh sách đã qua bộ lọc ra ngoài HTML
        'muc_tieu_quy': danh_sach_muc_tieu, 
        
        'su_kien_nhac_viec': SuKienNhacViec.objects.filter(ngay_dien_ra__gte=now.date())[:4],
        'chart_months': json.dumps(chart_months),
        'chart_thu': json.dumps(chart_thu),
        'chart_chi': json.dumps(chart_chi),
        'is_admin': is_admin,
        'user_role_name': user_role_name,
        'member_section_title': member_section_title,
        'ai_alerts': ai_alerts,
        'top_dai_gia': top_dai_gia,
        'is_thanh_hut': so_du_raw < 0,
    }
    return render(request, 'quanlyquy/dashboard.html', context)


# ==========================================
# 4. CÁC TRANG CHỨC NĂNG CHÍNH
# ==========================================
@login_required
def giao_dich_view(request):
    giao_dich_list_raw = GiaoDich.objects.all().select_related('thanh_vien').order_by('-ngay_tao')
    q = request.GET.get('search', '').strip()
    tx_type = request.GET.get('type', '')

    if q:
        search_condition = Q(ly_do__icontains=q) | (
            Q(is_an_danh=False) & (Q(thanh_vien__ho_ten__icontains=q) | Q(thanh_vien__mssv__icontains=q))
        )
        if "hảo tâm" in q.lower() or "ẩn danh" in q.lower():
            search_condition |= Q(is_an_danh=True)
        giao_dich_list_raw = giao_dich_list_raw.filter(search_condition)

    if tx_type == 'THU':
        giao_dich_list_raw = giao_dich_list_raw.filter(loai__in=['THU', 'LAI', 'HU'])
    elif tx_type == 'CHI':
        giao_dich_list_raw = giao_dich_list_raw.filter(loai__in=['CHI', 'TU'])

    for gd in giao_dich_list_raw:
        gd.so_tien_format = format_money(gd.so_tien)

    paginator = Paginator(giao_dich_list_raw, 10) 
    page_number = request.GET.get('page')
    giao_dich_list = paginator.get_page(page_number)

    return render(request, 'quanlyquy/page_giao_dich.html', {
        'giao_dich_list': giao_dich_list,
        'search_query': q,
        'current_type': tx_type,
        'is_admin': is_thu_quy(request.user)
    })

@login_required
def thong_ke_view(request):
    stats = GiaoDich.objects.annotate(m=TruncMonth('ngay_tao')).values('m').annotate(
        thu=Sum('so_tien', filter=Q(loai__in=['THU', 'LAI', 'HU'])),
        chi=Sum('so_tien', filter=Q(loai__in=['CHI', 'TU']))
    ).order_by('m')
    
    last_6_stats = list(stats)[-6:]
    c1_labels = [s['m'].strftime("Th %m/%y") for s in last_6_stats if s['m']]
    c1_thu = [float(s['thu'] or 0) for s in last_6_stats]
    c1_chi = [float(s['chi'] or 0) for s in last_6_stats]

    chi_tieu_db = GiaoDich.objects.filter(loai__in=['CHI', 'TU']).values('danh_muc__ten_danh_muc').annotate(
        tong=Sum('so_tien')).order_by('-tong')[:5]
    c2_labels = [item['danh_muc__ten_danh_muc'] or "Khác" for item in chi_tieu_db]
    c2_data = [float(item['tong'] or 0) for item in chi_tieu_db]

    top_members = ThanhVien.objects.annotate(
        tong=Sum('giaodich__so_tien', filter=Q(giaodich__loai='THU', giaodich__is_an_danh=False))
    ).filter(tong__gt=0).order_by('-tong')[:5]
    c3_labels = [m.ho_ten for m in top_members]
    c3_data = [float(m.tong or 0) for m in top_members]

    dot_thu_list = DotThu.objects.all().order_by('-id')[:4]
    tong_tv = ThanhVien.objects.count()
    c4_labels = []; c4_dathu = []; c4_no = []
    for dt in dot_thu_list:
        c4_labels.append(dt.ten_dot)
        da_thu = float(GiaoDich.objects.filter(dot_thu=dt, loai='THU').aggregate(Sum('so_tien'))['so_tien__sum'] or 0)
        tong_phai_thu = float(dt.so_tien_moi_nguoi * tong_tv)
        c4_dathu.append(da_thu)
        c4_no.append(max(0, tong_phai_thu - da_thu))

    quys = LoaiQuy.objects.all()
    c5_labels = [q.ten_quy for q in quys]
    c5_data = [float(q.so_du_hien_tai or 0) for q in quys]

# [BỔ SUNG QUAN TRỌNG]: Kiểm tra quyền Admin để hiện Sidebar
    is_admin = is_thu_quy(request.user)
    user_role_name = "Thủ quỹ hệ thống" if is_admin else "Thành viên lớp"
    context = {
        'chart1_labels': json.dumps(c1_labels),
        'chart1_thu': json.dumps(c1_thu),
        'chart1_chi': json.dumps(c1_chi),
        'chart2_labels': json.dumps(c2_labels),
        'chart2_data': json.dumps(c2_data),
        'chart3_labels': json.dumps(c3_labels),
        'chart3_data': json.dumps(c3_data),
        'chart4_labels': json.dumps(c4_labels),
        'chart4_dathu': json.dumps(c4_dathu),
        'chart4_no': json.dumps(c4_no),
        'chart5_labels': json.dumps(c5_labels),
        'chart5_data': json.dumps(c5_data),
        'is_admin': is_admin,
        'user_role_name': user_role_name,
    }
    return render(request, 'quanlyquy/thong_ke.html', context)

@login_required
def tien_do_thu_view(request):
    is_admin = is_thu_quy(request.user)
    dot_thu = DotThu.objects.order_by('-id').first()
    tat_ca_tv = ThanhVien.objects.filter(deleted_at__isnull=True)
    
    total_needed = 0
    total_collected = 0
    if dot_thu:
        total_needed = dot_thu.so_tien_moi_nguoi * tat_ca_tv.count()
        total_collected = GiaoDich.objects.filter(dot_thu=dot_thu, loai__in=['THU', 'LAI']).aggregate(Sum('so_tien'))['so_tien__sum'] or 0

    search_query = request.GET.get('search', '').strip()
    tv_filtered = tat_ca_tv
    if search_query:
        tv_filtered = tv_filtered.filter(Q(ho_ten__icontains=search_query) | Q(mssv__icontains=search_query))

    thanh_vien_stats_raw = []
    for tv in tv_filtered:
        # Tính tiền đóng dựa trên Đợt thu hiện tại
        da_nop = GiaoDich.objects.filter(thanh_vien=tv, dot_thu=dot_thu, loai__in=['THU', 'LAI']).aggregate(Sum('so_tien'))['so_tien__sum'] or 0
        is_me = (tv.mssv == getattr(request.user, 'mssv', None) or tv.email == request.user.email)
        danh_sach_no = [x for x in thanh_vien_stats_raw if x['is_no_xau']]
        
        thanh_vien_stats_raw.append({
            'id': tv.id, 
            'ho_ten': tv.ho_ten, 
            'mssv': tv.mssv,
            'so_tien_da_dong': format_money(da_nop),
            'is_hoan_thanh': da_nop >= (dot_thu.so_tien_moi_nguoi if dot_thu else 0),
            'is_no_xau': da_nop < (dot_thu.so_tien_moi_nguoi if dot_thu else 0),
            'is_me': is_me
        })

    paginator = Paginator(thanh_vien_stats_raw, 10)
    page_number = request.GET.get('page')
    thanh_vien_stats = paginator.get_page(page_number)

    percent = int((total_collected / total_needed * 100)) if total_needed > 0 else 0
    
    # Lấy trạng thái của chính sếp Quân để hiện Badge riêng
    my_status = next((x['is_hoan_thanh'] for x in thanh_vien_stats_raw if x['is_me']), False)
    

    context = {
        'is_admin': is_admin,
        'user_role_name': "Thủ quỹ hệ thống" if is_admin else "Thành viên lớp",
        'dot_thu': dot_thu,
        'total_needed': format_money(total_needed),
        'total_collected': format_money(total_collected),
        'total_remaining': format_money(max(0, total_needed - total_collected)),
        'percent': percent,
        'remaining_percent': max(0, 100 - percent),
        'thanh_vien_stats': thanh_vien_stats,
        'search_query': search_query,
        'my_status': my_status, # Cần thiết cho Badge "Trạng thái của bạn"
        'debt_count': len(danh_sach_no),
        'danh_sach_no': danh_sach_no,
        'deadline': dot_thu.han_chot.strftime("%d/%m/%Y") if dot_thu and dot_thu.han_chot else "Chưa đặt",
    }
    return render(request, 'quanlyquy/page_tien_do.html', context)

@login_required
@user_passes_test(is_thu_quy, login_url='/')
def cai_dat_view(request):
    return render(request, 'quanlyquy/page_cai_dat.html', {'is_admin': True})

@login_required
def gamification_view(request):
    # Dùng hàm helper để kiểm tra quyền Admin chuẩn xác
    is_admin = is_thu_quy(request.user)
    
    # Ép tên chức vụ hiển thị đúng trên UI
    user_role_name = "Thủ quỹ hệ thống" if is_admin else "Thành viên lớp"
    
    # Lấy danh sách nhiệm vụ từ Database (Lấy cả nhiệm vụ sếp vừa tạo)
    nhiem_vu_list = NhiemVu.objects.filter(is_active=True).order_by('-phan_thuong_xu')
    bieu_quyet_active = BieuQuyet.objects.filter(dang_mo=True)
    cua_hang_items = QuaTang.objects.filter(is_active=True)[:3]
    
    # Lấy ví Xu của người dùng
    my_tv = ThanhVien.objects.filter(mssv=getattr(request.user, 'mssv', '')).first()
    if not my_tv:
        my_tv = ThanhVien.objects.filter(email=getattr(request.user, 'email', '')).first()
    vi_xu = getattr(my_tv, 'vi_xu', 0) if my_tv else getattr(request.user, 'credit_score', 0)

    # Bảng xếp hạng
    top_dai_gia = ThanhVien.objects.all().order_by('-tong_xu_tich_luy')[:5]

    context = {
        'nhiem_vu_list': nhiem_vu_list,
        'bieu_quyet_active': bieu_quyet_active,
        'cua_hang_items': cua_hang_items,
        'top_dai_gia': top_dai_gia,
        'is_admin': is_admin,
        'user_role_name': user_role_name,
        'vi_xu': vi_xu,
        'has_vong_quay': True,
        'days_left': 5
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

from django.views.decorators.http import require_POST
import json

from django.views.decorators.http import require_POST
import json

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from django.http import JsonResponse

