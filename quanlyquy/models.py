from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date
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
    mssv = models.CharField(max_length=20, null=True, blank=True, verbose_name="Mã sinh viên")
    credit_score = models.IntegerField(default=100, verbose_name="Điểm tín nhiệm")

    def __str__(self): return self.full_name or self.username

class ThanhVien(BaseModel):
    ho_ten = models.CharField(max_length=100, verbose_name="Họ tên")
    mssv = models.CharField(max_length=20, unique=True, verbose_name="MSSV")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    is_no_xau = models.BooleanField(default=False, verbose_name="Nợ xấu/Bảo lưu")
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self): return f"{self.mssv} - {self.ho_ten}"

class LoaiQuy(BaseModel):
    ten_quy = models.CharField(max_length=100, verbose_name="Tên quỹ")
    is_khoa_so = models.BooleanField(default=False, verbose_name="Khóa sổ kế toán")

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

class MucTieuQuy(BaseModel):
    ten_muc_tieu = models.CharField(max_length=255, verbose_name="Tên mục tiêu")
    so_tien_muc_tieu = models.BigIntegerField(verbose_name="Số tiền mục tiêu (VNĐ)")
    so_tien_hien_tai = models.BigIntegerField(default=0, verbose_name="Đã gom được (VNĐ)")
    hoan_thanh = models.BooleanField(default=False, verbose_name="Đã hoàn thành?")

class SuKienNhacViec(BaseModel):
    ten_su_kien = models.CharField(max_length=255, verbose_name="Tên sự kiện")
    mo_ta = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mô tả ngắn")
    ngay_dien_ra = models.DateField(default=timezone.now, verbose_name="Ngày diễn ra")

# ==========================================
# PHÂN HỆ 3: LÕI TÀI CHÍNH & GIAO DỊCH
# ==========================================
class DanhMucThuChi(BaseModel):
    ten_danh_muc = models.CharField(max_length=100, verbose_name="Tên danh mục")
    loai = models.CharField(max_length=3, choices=[('THU', 'Thu'), ('CHI', 'Chi')], verbose_name="Loại")
    def __str__(self): return self.ten_danh_muc

class GiaoDich(BaseModel):
    LOAI = [('THU', 'Thu quỹ'), ('CHI', 'Chi quỹ'), ('TU', 'Tạm ứng'), ('HU', 'Hoàn ứng'), ('LAI', 'Lãi NH'), ('NB', 'Điều chuyển nội bộ')]
    loai = models.CharField(max_length=3, choices=LOAI, verbose_name="Loại giao dịch")
    so_tien = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Số tiền")
    loai_quy = models.ForeignKey(LoaiQuy, on_delete=models.CASCADE, verbose_name="Quỹ")
    dot_thu = models.ForeignKey(DotThu, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Đợt thu")
    thanh_vien = models.ForeignKey(ThanhVien, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Thành viên")
    ly_do = models.CharField(max_length=255, verbose_name="Nội dung")
    anh_hoa_don = models.ImageField(upload_to='hoadon/', blank=True, null=True, verbose_name="Hóa đơn")
    ngay_tao = models.DateTimeField(default=timezone.now, verbose_name="Ngày giao dịch")
    
    is_an_danh = models.BooleanField(default=False, verbose_name="Giao dịch ẩn danh")

    def clean(self):
        if self.loai_quy.is_khoa_so:
            raise ValidationError(f"Quỹ {self.loai_quy.ten_quy} đã khóa sổ.")

class HoaDonChungTu(BaseModel):
    giao_dich = models.OneToOneField(GiaoDich, on_delete=models.CASCADE, verbose_name="Giao dịch")
    link_anh = models.ImageField(upload_to='chung_tu/', verbose_name="Ảnh chứng từ")
    ai_doc_so_tien = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    ai_doc_noi_dung = models.CharField(max_length=255, null=True, blank=True)

class LichSuWebhook(BaseModel):
    ma_giao_dich_ngan_hang = models.CharField(max_length=100, unique=True)
    so_tien = models.DecimalField(max_digits=12, decimal_places=0)
    raw_payload = models.JSONField(verbose_name="Dữ liệu JSON gốc từ NH")
    trang_thai_xu_ly = models.BooleanField(default=False, verbose_name="Đã gạch nợ tự động chưa?")

class KhoanNo(BaseModel):
    thanh_vien = models.ForeignKey(ThanhVien, on_delete=models.CASCADE, verbose_name="Người nợ")
    so_tien = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Số tiền nợ")
    loai_no = models.CharField(max_length=50, verbose_name="Loại nợ")
    han_chot = models.DateField(null=True, blank=True, verbose_name="Hạn chót")
    da_hoan_thanh = models.BooleanField(default=False, verbose_name="Đã trả xong")

# ==========================================
# PHÂN HỆ 4: QUY TRÌNH, KHIẾU NẠI & BẢO MẬT
# ==========================================
class PhieuDeXuatChi(BaseModel):
    nguoi_de_xuat = models.ForeignKey(ThanhVien, on_delete=models.CASCADE, verbose_name="Người xin chi")
    so_tien = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Số tiền cần xin")
    muc_dich = models.TextField(verbose_name="Mục đích chi")
    trang_thai = models.CharField(max_length=20, choices=[('CHO_DUYET', 'Chờ duyệt'), ('DA_DUYET', 'Đã duyệt'), ('TU_CHOI', 'Từ chối')], default='CHO_DUYET')

class KhieuNai(BaseModel):
    thanh_vien = models.ForeignKey(ThanhVien, on_delete=models.CASCADE, verbose_name="Người khiếu nại")
    tieu_de = models.CharField(max_length=255, verbose_name="Vấn đề")
    noi_dung = models.TextField(verbose_name="Chi tiết")
    trang_thai = models.CharField(max_length=20, choices=[('MO', 'Đang mở'), ('DANG_XU_LY', 'Đang xử lý'), ('DONG', 'Đã giải quyết')], default='MO')

class BugBounty(BaseModel):
    nguoi_bao_cao = models.ForeignKey(User, on_delete=models.CASCADE)
    mo_ta_loi = models.TextField(verbose_name="Mô tả lỗi")
    trang_thai = models.CharField(max_length=20, choices=[('PENDING', 'Chờ duyệt'), ('FIXED', 'Đã sửa - Đã cấp Xu'), ('REJECTED', 'Báo cáo sai')], default='PENDING')

class ThoaThuanBaoMat(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dong_y_dieu_khoan = models.BooleanField(default=False, verbose_name="Đã đồng ý PDPA")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP lúc xác nhận")

# ==========================================
# PHÂN HỆ 5: TRÒ CHƠI HÓA (GAMIFICATION) & STORE
# ==========================================
class HuyHieu(BaseModel):
    ten_huy_hieu = models.CharField(max_length=100, verbose_name="Tên Huy hiệu")
    link_icon = models.CharField(max_length=255, blank=True, null=True, verbose_name="Icon/Emoji")
    mo_ta = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    diem_yeu_cau = models.IntegerField(default=0, verbose_name="Điểm yêu cầu")
    def __str__(self): return self.ten_huy_hieu

class HuyHieuThanhVien(BaseModel):
    thanh_vien = models.ForeignKey(ThanhVien, on_delete=models.CASCADE)
    huy_hieu = models.ForeignKey(HuyHieu, on_delete=models.CASCADE)
    ngay_dat_duoc = models.DateTimeField(default=timezone.now)

class BieuQuyet(BaseModel):
    cau_hoi = models.CharField(max_length=255, verbose_name="Câu hỏi biểu quyết")
    han_chot = models.DateTimeField(verbose_name="Hạn chót vote")
    dang_mo = models.BooleanField(default=True, verbose_name="Đang diễn ra")
    def __str__(self): return self.cau_hoi

class LuaChonBieuQuyet(BaseModel):
    bieu_quyet = models.ForeignKey(BieuQuyet, on_delete=models.CASCADE, related_name='cac_lua_chon')
    noi_dung_lua_chon = models.CharField(max_length=255, verbose_name="Lựa chọn")

class LuotBinhChon(BaseModel):
    bieu_quyet = models.ForeignKey(BieuQuyet, on_delete=models.CASCADE)
    lua_chon = models.ForeignKey(LuaChonBieuQuyet, on_delete=models.CASCADE)
    thanh_vien = models.ForeignKey(ThanhVien, on_delete=models.CASCADE)

class NhiemVu(BaseModel):
    ten_nhiem_vu = models.CharField(max_length=255, verbose_name="Tên nhiệm vụ", default='Nhiệm vụ chưa đặt tên')
    mo_ta = models.TextField(verbose_name="Mô tả cách thực hiện", null=True, blank=True)
    xu_thuong = models.IntegerField(default=10, verbose_name="Xu thưởng")
    is_kich_hoat = models.BooleanField(default=True, verbose_name="Đang kích hoạt")
    def __str__(self): return self.ten_nhiem_vu

class QuaTang(BaseModel):
    ten_qua = models.CharField(max_length=255, verbose_name="Tên món quà")
    mo_ta = models.TextField(blank=True, null=True, verbose_name="Mô tả đặc quyền")
    gia_xu = models.IntegerField(default=100, verbose_name="Giá đổi (Xu)")
    so_luong_kho = models.IntegerField(default=10, verbose_name="Số lượng còn")
    icon = models.CharField(max_length=50, default="fa-gift", verbose_name="Icon FontAwesome")
    mau_sac = models.CharField(max_length=20, default="#F6BCBA", verbose_name="Mã màu UI (Hex)")
    def __str__(self): return self.ten_qua

class LichSuDoiQua(BaseModel):
    thanh_vien = models.ForeignKey(ThanhVien, on_delete=models.CASCADE)
    qua_tang = models.ForeignKey(QuaTang, on_delete=models.CASCADE)
    trang_thai = models.CharField(max_length=20, choices=[('CHO_NHAN', 'Chờ nhận'), ('DA_GIAO', 'Đã giao')], default='CHO_NHAN')

# ==========================================
# PHÂN HỆ 6: GIÁM SÁT HỆ THỐNG & CHAOS LAB
# ==========================================
class NhatKyHeThong(models.Model):
    nguoi_dung = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    hanh_dong = models.CharField(max_length=50, verbose_name="Hành động")
    ten_bang = models.CharField(max_length=100, verbose_name="Bảng bị tác động")
    du_lieu_cu = models.JSONField(null=True, blank=True, verbose_name="Dữ liệu cũ")
    du_lieu_moi = models.JSONField(null=True, blank=True, verbose_name="Dữ liệu mới")
    thoi_gian = models.DateTimeField(auto_now_add=True)

class ThongBao(BaseModel):
    thanh_vien = models.ForeignKey(ThanhVien, on_delete=models.CASCADE)
    tieu_de = models.CharField(max_length=255)
    noi_dung = models.TextField()
    da_doc = models.BooleanField(default=False)

class CaiDatHeThong(BaseModel):
    ma_cai_dat = models.CharField(max_length=100, unique=True, verbose_name="Mã (VD: MUC_PHAT_TRE)")
    gia_tri = models.CharField(max_length=255, verbose_name="Giá trị")
    mo_ta = models.CharField(max_length=255, null=True, blank=True)

class QATestingLog(models.Model):
    nguoi_test = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    loai_test = models.CharField(max_length=100, verbose_name="Kịch bản giả lập")
    du_lieu_phat_sinh = models.JSONField(verbose_name="Dữ liệu Data-Seed")
    trang_thai = models.CharField(max_length=50, default="SUCCESS")
    thoi_gian_test = models.DateTimeField(auto_now_add=True)