/* ================= LOGIC TRANG TIẾN ĐỘ ================= */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Tiến Độ Đợt Thu - Premium Interface Ready!");

    // Thêm chức năng tìm kiếm thành viên nhanh (giống trang Giao dịch)
    const searchInput = document.createElement('input'); // Có thể thêm input vào HTML nếu cần
    // Hiện tại chức năng search này sẽ so khớp text trong các dòng của bảng
    
    // Xử lý đóng mở Modal Hồ sơ cá nhân
    window.openModal = function(id) { document.getElementById(id).classList.add('active'); }
    window.closeModal = function(id) { document.getElementById(id).classList.remove('active'); }
});