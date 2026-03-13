from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser

# ==========================================
# LÕI HỆ THỐNG: QUẢN LÝ DẤU VẾT & XÓA MỀM
# ==========================================
class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Lần sửa cuối")
    created_by = models.CharField(max_length=50, null=True, blank=True, verbose_name="Người tạo (ID)")
    updated_by = models.CharField(max_length=50, null=True, blank=True, verbose_name="Người sửa (ID)")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Ngày xóa mềm")

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

# ==========================================
# PHÂN HỆ 1 & 2: THÔNG TIN NGƯỜI DÙNG & QUỸ LỚP
# ==========================================
class User(AbstractUser):
    ROLE_CHOICES = (('ADMIN', 'Thủ Quỹ (Lớp trưởng)'), ('MEMBER', 'Thành Viên'), ('TESTER', 'QA/Tester'))
    full_name = models.CharField(max_length=255, verbose_name="Họ và tên")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='MEMBER')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True, verbose_name="Số điện thoại")
    mssv = models.CharField(max_length=20, null=True, blank=True, verbose_name="Mã sinh viên")
    credit_score = models.IntegerField(default=100, verbose_name="Điểm tín nhiệm")
    secure_pin = models.CharField(max_length=128, null=True, blank=True, verbose_name="Mã PIN bảo mật")

    class Meta:
        verbose_name = "Tài Khoản"
        verbose_name_plural = "Tài Khoản Hệ Thống"

    def __str__(self): return self.full_name or self.username

class LopHoc(BaseModel):
    ten_lop = models.CharField(max_length=50, verbose_name="Tên lớp")
    nien_khoa = models.CharField(max_length=50, verbose_name="Niên khóa")
    
    class Meta:
        verbose_name = "Lớp Học"
        verbose_name_plural = "Lớp Học"
        
    def __str__(self): return self.ten_lop

class ThanhVien(BaseModel):
    ho_ten = models.CharField(max_length=100, verbose_name="Họ tên")
    mssv = models.CharField(max_length=20, unique=True, verbose_name="MSSV")
    gender = models.CharField(max_length=10, choices=[('NAM', 'Nam'), ('NU', 'Nữ')], null=True, verbose_name="Giới tính")
    phone = models.CharField(max_length=15, null=True, blank=True, verbose_name="Số điện thoại")
    lop_hoc = models.ForeignKey(LopHoc, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Lớp học")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    is_no_xau = models.BooleanField(default=False, verbose_name="Nợ xấu/Bảo lưu")
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Thành Viên"
        verbose_name_plural = "Hồ Sơ Sinh Viên"

    def __str__(self): return f"{self.mssv} - {self.ho_ten}"

class LoaiQuy(BaseModel):
    ten_quy = models.CharField(max_length=100, verbose_name="Tên quỹ")
    is_khoa_so = models.BooleanField(default=False, verbose_name="Khóa sổ kế toán")

    class Meta:
        verbose_name = "Quỹ Lớp"
        verbose_name_plural = "Quản Lý Quỹ Lớp"

    @property
    def so_du_hien_tai(self):
        thu = GiaoDich.objects.filter(loai_quy=self, loai__in=['THU', 'LAI', 'HU']).aggregate(models.Sum('so_tien'))['so_tien__sum'] or 0
        chi = GiaoDich.objects.filter(loai_quy=self, loai__in=['CHI', 'TU']).aggregate(models.Sum('so_tien'))['so_tien__sum'] or 0
        return thu - chi

    def __str__(self): return self.ten_quy

class DotThu(BaseModel):
    ten_dot = models.CharField(max_length=200, verbose_name="Tên đợt thu")
    loai_quy = models.ForeignKey(LoaiQuy, on_delete=models.CASCADE, verbose_name="Vào quỹ")
    so_tien_moi_nguoi = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Định mức nộp")
    han_chot = models.DateField(verbose_name="Hạn chót")

    class Meta:
        verbose_name = "Đợt Thu"
        verbose_name_plural = "Đợt Thu Tiền"

    def __str__(self): return self.ten_dot

class TienDoDongQuy(BaseModel):
    dot_thu = models.ForeignKey(DotThu, on_delete=models.CASCADE)
    thanh_vien = models.ForeignKey(ThanhVien, on_delete=models.CASCADE)
    so_tien_can_nop = models.DecimalField(max_digits=12, decimal_places=0)
    so_tien_da_nop = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    duoc_mien_giam = models.BooleanField(default=False)
    trang_thai = models.CharField(max_length=20, choices=[('CHUA_NOP', 'Chưa nộp'), ('THIEU', 'Nộp thiếu'), ('DU', 'Đã đủ')], default='CHUA_NOP')

class TaiSan(BaseModel):
    ten_tai_san = models.CharField(max_length=200, verbose_name="Tên tài sản")
    gia_mua = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Giá mua")
    ngay_mua = models.DateField(default=timezone.now, verbose_name="Ngày mua")
    ti_le_khau_hao = models.FloatField(default=10, verbose_name="% Khấu hao/Năm")

    class Meta:
        verbose_name = "Tài Sản"
        verbose_name_plural = "Tài Sản Của Lớp"

    @property
    def gia_tri_hien_tai(self):
        tuoi_doi = (timezone.now().date() - self.ngay_mua).days / 365
        khau_hao = float(self.gia_mua) * (self.ti_le_khau_hao / 100) * tuoi_doi
        gia_tri = float(self.gia_mua) - khau_hao
        return max(gia_tri, 0)

class MucTieuQuy(BaseModel):
    ten_muc_tieu = models.CharField(max_length=255, verbose_name="Tên mục tiêu")
    so_tien_muc_tieu = models.BigIntegerField(verbose_name="Số tiền mục tiêu (VNĐ)")
    so_tien_hien_tai = models.BigIntegerField(default=0, verbose_name="Đã gom được (VNĐ)")
    hoan_thanh = models.BooleanField(default=False, verbose_name="Đã hoàn thành?")
    
    class Meta:
        verbose_name = "Mục Tiêu"
        verbose_name_plural = "Mục Tiêu Tích Lũy"

class SuKienNhacViec(BaseModel):
    ten_su_kien = models.CharField(max_length=255, verbose_name="Tên sự kiện")
    mo_ta = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mô tả ngắn")
    ngay_dien_ra = models.DateField(default=timezone.now, verbose_name="Ngày diễn ra")
    
    class Meta:
        verbose_name = "Sự Kiện"
        verbose_name_plural = "Sự Kiện & Lịch Trình"

# ==========================================
# PHÂN HỆ 3: LÕI TÀI CHÍNH & GIAO DỊCH
# ==========================================
class DanhMucThuChi(BaseModel):
    ten_danh_muc = models.CharField(max_length=100, verbose_name="Tên danh mục")
    loai = models.CharField(max_length=3, choices=[('THU', 'Thu'), ('CHI', 'Chi')], verbose_name="Loại")
    mo_ta = models.TextField(null=True, blank=True, verbose_name="Mô tả danh mục")

    class Meta:
        verbose_name = "Danh Mục"
        verbose_name_plural = "Danh Mục Thu/Chi"

    def __str__(self): return f"[{self.get_loai_display()}] {self.ten_danh_muc}"

class GiaoDich(BaseModel):
    LOAI = [('THU', 'Thu quỹ'), ('CHI', 'Chi quỹ'), ('TU', 'Tạm ứng'), ('HU', 'Hoàn ứng'), ('LAI', 'Lãi NH'), ('NB', 'Điều chuyển nội bộ')]
    
    loai = models.CharField(max_length=3, choices=LOAI, verbose_name="Loại giao dịch")
    so_tien = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Số tiền")
    loai_quy = models.ForeignKey(LoaiQuy, on_delete=models.CASCADE, verbose_name="Quỹ")
    
    # [QUAN TRỌNG]: Thêm cột dot_thu để tránh lỗi Crash khi xem biểu đồ Thống Kê
    dot_thu = models.ForeignKey('DotThu', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Đợt thu")
    danh_muc = models.ForeignKey(DanhMucThuChi, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Danh mục")
    thanh_vien = models.ForeignKey(ThanhVien, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Thành viên")
    ly_do = models.CharField(max_length=255, verbose_name="Nội dung/Ghi chú")
    anh_hoa_don = models.ImageField(upload_to='hoadon/', blank=True, null=True, verbose_name="Minh chứng (Hóa đơn)")
    
    is_an_danh = models.BooleanField(default=False, verbose_name="Giao dịch ẩn danh")
    ngay_tao = models.DateTimeField(default=timezone.now, verbose_name="Ngày tạo giao dịch")

    class Meta:
        verbose_name = "Giao Dịch"
        verbose_name_plural = "Sổ Giao Dịch"

    def clean(self):
        if self.loai_quy and self.loai_quy.is_khoa_so:
            raise ValidationError(f"Quỹ '{self.loai_quy.ten_quy}' đã bị khóa sổ. Không thể thêm giao dịch.")

    def __str__(self): return f"{self.ngay_tao.strftime('%d/%m/%Y')} - {self.ly_do} ({self.so_tien}đ)"

class LichSuWebhook(BaseModel):
    ma_giao_dich_ngan_hang = models.CharField(max_length=100, unique=True)
    so_tien = models.DecimalField(max_digits=12, decimal_places=0)
    raw_payload = models.JSONField(verbose_name="Dữ liệu JSON gốc từ NH")
    trang_thai_xu_ly = models.BooleanField(default=False, verbose_name="Đã gạch nợ tự động chưa?")
    
    class Meta:
        verbose_name = "Webhook"
        verbose_name_plural = "Lịch Sử Webhook Auto"

# ==========================================
# PHÂN HỆ GAMIFICATION & QUY TRÌNH (Rút gọn)
# ==========================================
class PhieuDeXuatChi(BaseModel):
    nguoi_de_xuat = models.ForeignKey(ThanhVien, on_delete=models.CASCADE, verbose_name="Người xin chi")
    so_tien = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Số tiền cần xin")
    muc_dich = models.TextField(verbose_name="Mục đích chi")
    trang_thai = models.CharField(max_length=20, choices=[('CHO_DUYET', 'Chờ duyệt'), ('DA_DUYET', 'Đã duyệt'), ('TU_CHOI', 'Từ chối')], default='CHO_DUYET')
    class Meta: verbose_name = "Đề Xuất"; verbose_name_plural = "Phiếu Đề Xuất Chi"

class KhieuNai(BaseModel):
    thanh_vien = models.ForeignKey(ThanhVien, on_delete=models.CASCADE, verbose_name="Người khiếu nại")
    tieu_de = models.CharField(max_length=255, verbose_name="Vấn đề")
    noi_dung = models.TextField(verbose_name="Chi tiết")
    trang_thai = models.CharField(max_length=20, choices=[('MO', 'Đang mở'), ('DANG_XU_LY', 'Đang xử lý'), ('DONG', 'Đã giải quyết')], default='MO')
    class Meta: verbose_name = "Khiếu Nại"; verbose_name_plural = "Quản Lý Khiếu Nại"

class QuaTang(BaseModel):
    ten_qua = models.CharField(max_length=255, verbose_name="Tên món quà")
    gia_xu = models.IntegerField(default=100, verbose_name="Giá đổi (Xu)")
    so_luong_kho = models.IntegerField(default=10, verbose_name="Số lượng còn")
    class Meta: verbose_name = "Quà Tặng"; verbose_name_plural = "Cửa Hàng Quà Tặng"

class NhiemVu(BaseModel):
    ten_nhiem_vu = models.CharField(max_length=255, verbose_name="Tên nhiệm vụ")
    xu_thuong = models.IntegerField(default=10, verbose_name="Xu thưởng")
    is_kich_hoat = models.BooleanField(default=True, verbose_name="Đang kích hoạt")
    class Meta: verbose_name = "Nhiệm Vụ"; verbose_name_plural = "Nhiệm Vụ Tích Xu"

class BieuQuyet(BaseModel):
    cau_hoi = models.CharField(max_length=255, verbose_name="Câu hỏi biểu quyết")
    han_chot = models.DateTimeField(verbose_name="Hạn chót vote")
    dang_mo = models.BooleanField(default=True, verbose_name="Đang diễn ra")
    class Meta: verbose_name = "Khảo Sát"; verbose_name_plural = "Bầu Cử / Khảo Sát"

class QATestingLog(models.Model):
    nguoi_test = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    loai_test = models.CharField(max_length=100, verbose_name="Kịch bản giả lập")
    du_lieu_phat_sinh = models.JSONField(verbose_name="Dữ liệu Data-Seed")
    trang_thai = models.CharField(max_length=50, default="SUCCESS")
    thoi_gian_test = models.DateTimeField(auto_now_add=True)
    class Meta: verbose_name = "Log QA"; verbose_name_plural = "Lịch Sử Test QA"
class HuyHieu(BaseModel):
    ten_huy_hieu = models.CharField(max_length=100, verbose_name="Tên Huy hiệu")
    link_icon = models.CharField(max_length=255, blank=True, null=True, verbose_name="Icon/Emoji")
    mo_ta = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    diem_yeu_cau = models.IntegerField(default=0, verbose_name="Điểm yêu cầu")
    
    class Meta: 
        verbose_name = "Huy Hiệu"
        verbose_name_plural = "Danh Sách Huy Hiệu"
        
    def __str__(self): return self.ten_huy_hieu

class HuyHieuThanhVien(BaseModel):
    thanh_vien = models.ForeignKey(ThanhVien, on_delete=models.CASCADE)
    huy_hieu = models.ForeignKey(HuyHieu, on_delete=models.CASCADE)
    ngay_dat_duoc = models.DateTimeField(default=timezone.now)
    
    class Meta: 
        verbose_name = "Cấp Phát Huy Hiệu"
        verbose_name_plural = "Lịch Sử Cấp Huy Hiệu"