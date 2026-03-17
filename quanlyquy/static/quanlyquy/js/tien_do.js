/* ================= HỆ THỐNG THÔNG BÁO UI ================= */
// Hàm tạo thông báo đẹp trượt từ góc phải (Nằm ngoài cùng để gọi được ở mọi nơi)
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return; // Chống lỗi nếu web chưa load xong container

    const toast = document.createElement('div');
    const color = type === 'success' ? '#10b981' : '#ef4444'; // Xanh hoặc Đỏ
    const icon = type === 'success' ? 'fa-circle-check' : 'fa-triangle-exclamation';
    
    toast.style.cssText = `background: rgba(15, 23, 42, 0.95); border-left: 4px solid ${color}; color: white; padding: 16px 20px; border-radius: 12px; font-size: 13px; font-weight: 600; box-shadow: 0 10px 30px rgba(0,0,0,0.5); display: flex; align-items: center; gap: 12px; transform: translateX(120%); transition: 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.05); margin-bottom: 10px;`;
    toast.innerHTML = `<i class="fa-solid ${icon}" style="color: ${color}; font-size: 18px;"></i> ${message}`;
    
    container.appendChild(toast);
    
    // Hiệu ứng trượt vào
    setTimeout(() => toast.style.transform = 'translateX(0)', 10);
    // Tự động biến mất sau 3 giây
    setTimeout(() => {
        toast.style.transform = 'translateX(120%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/* ================= CHỨC NĂNG THỰC TẾ ================= */

// 1. CHỨC NĂNG NHẮC NỢ
window.handleNhacNo = function(memberId, btnElement) {
    if (btnElement) {
        // Đổi UI sang trạng thái "Đang gửi"
        btnElement.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang gửi...';
        btnElement.style.opacity = '0.7';
        btnElement.disabled = true;

        // Giả lập gửi API mất 1 giây:
        setTimeout(() => {
            showToast("Đã gửi tin nhắn nhắc nợ thành công!", "success");
            // Đổi nút thành "Đã nhắc" màu xanh
            btnElement.innerHTML = '<i class="fa-solid fa-check"></i> Đã nhắc';
            btnElement.style.background = 'rgba(16, 185, 129, 0.2)';
            btnElement.style.color = '#4ade80';
            btnElement.style.borderColor = 'rgba(16, 185, 129, 0.3)';
        }, 1000);
    } else {
        showToast("Đã gửi tin nhắn nhắc nợ thành công!", "success");
    }
};

// 2. CHỨC NĂNG NỘP HỘ - MỞ MODAL
window.showFriendProfile = function(id, name, mssv) {
    document.getElementById('nopHoId').value = id;
    document.getElementById('nopHoName').value = `${name} (${mssv})`;
    document.getElementById('nopHoModal').style.display = 'flex';
};

// 3. CHỨC NĂNG NỘP HỘ - XÁC NHẬN BẮN API
window.submitNopHo = function() {
    const id = document.getElementById('nopHoId').value;
    const amount = document.getElementById('nopHoAmount').value;
    const name = document.getElementById('nopHoName').value;

    if (!amount || amount <= 0) {
        showToast("Vui lòng nhập số tiền hợp lệ!", "error");
        return;
    }

    // Đóng modal và báo đang xử lý
    document.getElementById('nopHoModal').style.display = 'none';
    showToast(`Đang xử lý nộp quỹ cho ${name}...`, "success");

    // TODO: Chỗ này sếp dùng fetch() để gọi API api_nop_quy trong views.py
    setTimeout(() => {
        showToast("Giao dịch thành công! Đang làm mới...", "success");
        // Tải lại trang để cập nhật số dư sau 1.5 giây
        setTimeout(() => window.location.reload(), 1500);
    }, 1500);
};

// ================= CÁC HÀM MODAL CƠ BẢN =================
window.openModal = function(id) { 
    const m = document.getElementById(id);
    if(m) m.classList.add('active'); 
};
window.closeModal = function(id) { 
    const m = document.getElementById(id);
    if(m) m.classList.remove('active'); 
};

/* ================= LOGIC KÍCH HOẠT KHI TRANG LOAD XONG ================= */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Hệ thống Hành động - Ready! Các hàm đã được nạp ra Global.");
});