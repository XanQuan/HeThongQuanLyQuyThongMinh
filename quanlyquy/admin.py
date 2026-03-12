from django import forms 
from django.http import HttpResponse
from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import render, redirect
import pandas as pd
from django.contrib import admin
from .models import MucTieuQuy, SuKienNhacViec

from unfold.admin import ModelAdmin
from unfold.decorators import action, display
from .models import ThanhVien, LoaiQuy, DotThu, TaiSan, GiaoDich

# --- CẤU HÌNH HEADER HỆ THỐNG ---
admin.site.site_header = "HỆ THỐNG TÀI CHÍNH FUNDSMART PRO"
admin.site.site_title = "FundSmart Advanced"
admin.site.index_title = "Bảng điều khiển Kế toán kép"

# Helper định dạng tiền tệ chuẩn VNĐ (Tránh lỗi format code 'f' trên Django 6.x)
def f_money(value):
    return "{:,.0f} đ".format(value or 0).replace(',', '.')

# --- FORM UPLOAD EXCEL (Phải khai báo ở đầu file) ---
class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label="Chọn file sao kê ngân hàng (Excel)")

# --- 1. QUẢN LÝ THÀNH VIÊN ---
@admin.register(ThanhVien)
class ThanhVienAdmin(ModelAdmin):
    list_display = ('mssv', 'ho_ten', 'is_no_xau', 'display_status', 'email') 
    list_filter = ('is_no_xau',)
    search_fields = ('mssv', 'ho_ten')
    list_editable = ('is_no_xau',) 
    list_per_page = 20

    # FIX TRIỆT ĐỂ LỖI TYPE ERROR: Đã thêm "{}" và biến "NỢ XẤU"/"AN TOÀN"
    @display(description="Trạng thái tài chính")
    def display_status(self, obj):
        if obj.is_no_xau:
            return format_html('<span style="background-color: rgba(244, 63, 94, 0.1); color: #f43f5e; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 11px; border: 1px solid rgba(244, 63, 94, 0.2);">{}</span>', 'NỢ XẤU')
        return format_html('<span style="background-color: rgba(16, 185, 129, 0.1); color: #10b981; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 11px; border: 1px solid rgba(16, 185, 129, 0.2);">{}</span>', 'AN TOÀN')

# --- 2. QUẢN LÝ ĐA QUỸ ---
@admin.register(LoaiQuy)
class LoaiQuyAdmin(ModelAdmin):
    list_display = ('ten_quy', 'display_balance', 'trang_thai_khoa', 'dieu_chuyen_nhanh')

    @display(description="Số dư hiện tại")
    def display_balance(self, obj):
        balance = obj.so_du_hien_tai
        color = "#ef4444" if balance < 500000 else "#10b981"
        return format_html('<b style="color: {}; font-size: 15px;">{}</b>', color, f_money(balance))

    @display(description="Trạng thái sổ", label=True)
    def trang_thai_khoa(self, obj):
        if obj.is_khoa_so:
            return "ĐÃ KHÓA SỔ", "danger"
        return "ĐANG MỞ", "info"

    @display(description="⚡ Chuyển tiền")
    def dieu_chuyen_nhanh(self, obj):
        url = reverse('admin:quanlyquy_giaodich_add') + f"?loai=NB&loai_quy={obj.id}"
        return format_html('<a href="{}" style="background:#6366f1; color:white; padding:4px 12px; border-radius:6px; font-size:11px; font-weight:700;">{}</a>', url, "ĐIỀU CHUYỂN")

# --- 3. CÁC ĐỢT THU TIỀN ---
@admin.register(DotThu)
class DotThuAdmin(ModelAdmin):
    list_display = ('ten_dot', 'loai_quy', 'format_dinh_muc', 'display_progress', 'han_chot')
    list_filter = ('loai_quy', 'han_chot')
    
    @display(description="Định mức")
    def format_dinh_muc(self, obj):
        return f_money(obj.so_tien_moi_nguoi)

    @display(description="Tiến độ đã thu")
    def display_progress(self, obj):
        return format_html('<span style="color:#6366f1; font-weight:bold;">{}</span>', f_money(obj.tong_da_thu))

# --- 4. TÀI SẢN LỚP ---
@admin.register(TaiSan)
class TaiSanAdmin(ModelAdmin):
    list_display = ('ten_tai_san', 'display_gia_mua', 'display_khau_hao', 'ngay_mua')
    date_hierarchy = 'ngay_mua'
    
    @display(description="Giá trị hiện tại")
    def display_khau_hao(self, obj):
        return format_html('<b style="color: #f59e0b;">{}</b>', f_money(obj.gia_tri_hien_tai))

    @display(description="Giá gốc")
    def display_gia_mua(self, obj):
        return f_money(obj.gia_mua)

# --- 5. LỊCH SỬ GIAO DỊCH & ĐỐI SOÁT ---
@admin.register(GiaoDich)
class GiaoDichAdmin(ModelAdmin):
    list_display = ('ngay_tao', 'display_loai', 'display_amount', 'loai_quy', 'thanh_vien', 'xem_hoa_don')
    list_filter = ('loai', 'loai_quy', 'ngay_tao')
    search_fields = ('ly_do', 'thanh_vien__ho_ten')
    actions = ['reconcile_with_bank']

    @display(description="Dòng tiền")
    def display_amount(self, obj):
        is_in = obj.loai in ['THU', 'LAI', 'HU']
        color = "#10b981" if is_in else "#f43f5e"
        prefix = "▲" if is_in else "▼" 
        return format_html(
            '<span style="color: {}; font-weight: 900; letter-spacing: -0.5px;">{} {}</span>',
            color, prefix, f_money(obj.so_tien)
        )

    @display(description="Nghiệp vụ")
    def display_loai(self, obj):
        loai_name = obj.get_loai_display()
        if obj.loai in ['THU', 'LAI', 'HU']:
            return format_html('<span style="background-color: rgba(99, 102, 241, 0.1); color: #6366f1; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 11px;">{}</span>', loai_name.upper())
        return format_html('<span style="background-color: rgba(245, 158, 11, 0.1); color: #f59e0b; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 11px;">{}</span>', loai_name.upper())

    @display(description="Hóa đơn")
    def xem_hoa_don(self, obj):
        if obj.anh_hoa_don:
            return format_html('<a href="{}" target="_blank" style="color:#6366f1;">{}</a>', obj.anh_hoa_don.url, "🖼️ Xem bill")
        return format_html('<span style="color:#94a3b8;">{}</span>', "Trống")

    # --- TÍNH NĂNG: TẢI FILE EXCEL MẪU ---
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('download-template/', self.download_template, name='quanlyquy_giaodich_download_template'),
        ]
        return custom_urls + urls

    def download_template(self, request):
        """Tạo file Excel mẫu với cột chuẩn ngay trên bộ nhớ"""
        df = pd.DataFrame({
            'Số tiền': [150000, -20000, 5000],
            'Nội dung': ['Ví dụ: Nguyễn Văn A nộp quỹ', 'Ví dụ: Chi mua nước', 'Ví dụ: Lãi ngân hàng']
        })
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=mau_doi_soat_fundsmart.xlsx'
        df.to_excel(response, index=False)
        return response

    # --- TÍNH NĂNG: ĐỐI SOÁT NGÂN HÀNG (ACTION) ---
    @action(description="🔍 Đối soát ngân hàng từ file Excel")
    def reconcile_with_bank(self, request, queryset):
        if 'apply' in request.POST:
            form = ExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    df = pd.read_excel(request.FILES['excel_file'])
                    bank_amounts = df['Số tiền'].astype(float).tolist()
                    system_amounts = [float(gd.so_tien) for gd in queryset]
                    
                    matches = [f_money(a) for a in bank_amounts if a in system_amounts]
                    missing_sys = [f_money(a) for a in bank_amounts if a not in system_amounts]
                    missing_bank = [f_money(a) for a in system_amounts if a not in bank_amounts]
                    
                    return render(request, "admin/reconciliation_report.html", {
                        'results': {'match': matches, 'missing_sys': missing_sys, 'missing_bank': missing_bank},
                        'title': "Kết quả đối soát tài chính"
                    })
                except Exception as e:
                    self.message_user(request, f"Lỗi xử lý file: {str(e)}", messages.ERROR)
                    return redirect(request.get_full_path())
        
        download_url = reverse('admin:quanlyquy_giaodich_download_template')
        return render(request, "admin/excel_upload.html", {
            'items': queryset, 
            'form': ExcelUploadForm(), 
            'title': "Tải lên sao kê để so đối",
            'download_url': download_url
        })
    
@admin.register(MucTieuQuy)
class MucTieuQuyAdmin(admin.ModelAdmin):
    list_display = ['ten_muc_tieu', 'so_tien_hien_tai', 'so_tien_muc_tieu', 'hoan_thanh']

@admin.register(SuKienNhacViec)
class SuKienNhacViecAdmin(admin.ModelAdmin):
    list_display = ['ten_su_kien', 'ngay_dien_ra', 'mo_ta']