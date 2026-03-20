/* ======================================================
   XỬ LÝ NGHIỆP VỤ TIẾN ĐỘ THU (tien_do.js) - BẢN HOÀN THIỆN
   ====================================================== */

// 1. TIỆN ÍCH HỆ THỐNG
// Hàm lấy CSRF Token để bảo mật các yêu cầu POST từ Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
// BỔ SUNG VÀO ĐẦU FILE TIEN_DO.JS
window.openModal = function(id) { 
    const m = document.getElementById(id);
    if(m) {
        m.style.display = 'flex';
        m.style.zIndex = '10000';
    }
};

window.closeModal = function(id) { 
    const m = document.getElementById(id);
    if(m) m.style.display = 'none'; 
};

// 2. HIỂN THỊ THÔNG BÁO (TOAST)
window.showToast = function(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    const color = type === 'success' ? '#10b981' : '#ef4444';
    const icon = type === 'success' ? 'fa-circle-check' : 'fa-triangle-exclamation';
    
    toast.style.cssText = `background: rgba(15, 23, 42, 0.95); border-left: 4px solid ${color}; color: white; padding: 16px 20px; border-radius: 12px; font-size: 13px; font-weight: 600; box-shadow: 0 10px 30px rgba(0,0,0,0.5); display: flex; align-items: center; gap: 12px; transform: translateX(120%); transition: 0.3s; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.05); margin-bottom: 10px; z-index: 99999;`;
    toast.innerHTML = `<i class="fa-solid ${icon}" style="color: ${color}; font-size: 18px;"></i> ${message}`;
    
    container.appendChild(toast);
    setTimeout(() => toast.style.transform = 'translateX(0)', 10);
    setTimeout(() => {
        toast.style.transform = 'translateX(120%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
};

// 3. XỬ LÝ MODAL KPI CHI TIẾT
// Khắc phục lỗi "bấm vào không hiện thông tin" bằng cách dùng dữ liệu từ window.FUND_DATA
window.showKpiDetail = function(type) {
    const modal = document.getElementById('kpiModal');
    const title = document.getElementById('kpiModalTitle');
    const content = document.getElementById('kpiModalContent');
    const d = window.FUND_DATA; // Cầu nối dữ liệu từ HTML

    if (!modal || !title || !content || !d) {
        console.error("Thiếu container modal hoặc window.FUND_DATA chưa được khai báo!");
        return;
    }

    if (type === 'muctieu') {
        title.innerHTML = '<i class="fa-solid fa-flag-checkered" style="color: #a855f7;"></i> Chi Tiết Đợt Thu';
        content.innerHTML = `
            <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1);">
                <p><strong>Tên đợt thu:</strong> <span style="color: white;">${d.tenDot}</span></p>
                <p><strong>Loại quỹ:</strong> <span style="color: var(--theme-primary);">${d.tenQuy}</span></p>
                <p><strong>Định mức:</strong> <span style="color: white;">${d.dinhMuc} đ</span></p>
                <p><strong>Hạn chót:</strong> <span style="color: #fca5a5; font-weight: 800;">${d.deadline}</span></p>
            </div>`;
    } 
    else if (type === 'tiendo') {
        title.innerHTML = '<i class="fa-solid fa-chart-pie" style="color: #10b981;"></i> Thống Kê Dòng Tiền';
        content.innerHTML = `
            <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1);">
                <p><strong>Tiền kỳ vọng:</strong> <span style="color: white;">${d.totalNeeded} đ</span></p>
                <p><strong>Đã thu thực tế:</strong> <span style="color: #10b981; font-weight: 800;">${d.totalCollected} đ</span></p>
                <p><strong>Tỷ lệ hoàn thành:</strong> <span style="color: white;">${d.percent}%</span></p>
                <div style="width: 100%; height: 10px; background: rgba(255,255,255,0.1); border-radius: 10px; overflow: hidden; margin-top: 10px;">
                    <div style="width: ${d.percent}%; height: 100%; background: #10b981; box-shadow: 0 0 10px #10b981;"></div>
                </div>
            </div>`;
    } 
    else if (type === 'conno') {
        title.innerHTML = '<i class="fa-solid fa-circle-exclamation" style="color: #ef4444;"></i> Danh Sách Nợ Quỹ';
        let listNoHtml = d.danhSachNo.length > 0 
            ? d.danhSachNo.map(tv => `
                <div style="display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px dashed rgba(255,255,255,0.1);">
                    <span style="color: white; font-weight: 600;">${tv.ho_ten}</span>
                    <span style="color: #94a3b8; font-family: monospace;">${tv.mssv}</span>
                </div>`).join('')
            : '<p style="text-align: center; padding: 20px; color: #10b981;">Tuyệt vời! Không ai nợ quỹ.</p>';

        content.innerHTML = `
            <p>Có <strong style="color: #f87171;">${d.debtCount}</strong> thành viên chưa hoàn tất:</p>
            <div style="max-height: 250px; overflow-y: auto; padding-right: 5px;">${listNoHtml}</div>
            ${d.isAdmin ? `
                <button onclick="runMassRemind()" id="massRemindBtn" class="hover-scale" style="width: 100%; background: rgba(239, 68, 68, 0.1); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); padding: 12px; border-radius: 10px; margin-top: 20px; font-weight: 800; cursor: pointer;">
                    <i class="fa-solid fa-bullhorn me-2"></i> NHẮC NỢ HÀNG LOẠT 🚀
                </button>` : ''}
        `;
    }
    modal.style.display = 'flex';
};

// 4. NGHIỆP VỤ NHẮC NỢ & DỌN DẸP THÔNG BÁO
window.runMassRemind = function() {
    const btn = document.getElementById('massRemindBtn');
    if (!btn) return;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang băm lệnh...';
    btn.disabled = true;

    fetch('/api/mass-remind/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body: new URLSearchParams({ 'dot_thu_id': window.FUND_DATA.dotThuId })
    })
    .then(res => res.json())
    .then(data => {
        showToast(data.message, data.status);
        btn.innerHTML = '<i class="fa-solid fa-check"></i> ĐÃ NHẮC XONG';
    })
    .catch(() => {
        showToast("Lỗi kết nối máy chủ!", "error");
        btn.disabled = false;
    });
};

// 1. Hàm mở modal hỏi sếp
window.clearNotifications = function(btn) {
    // Lưu lại cái nút Dọn Rác để tí nữa gắn spinner vào nó
    window.lastClickedClearBtn = btn;
    const modal = document.getElementById('customConfirmModal');
    if(modal) modal.style.display = 'flex';
};

// 2. Hàm thực thi xóa thật sự (Bản dứt điểm "quay quài")
window.executeDeleteNotifications = function() {
    const btn = window.lastClickedClearBtn;
    const modal = document.getElementById('customConfirmModal');
    if(modal) modal.style.display = 'none';
    if(!btn) return;

    const originalHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    btn.style.pointerEvents = 'none';

    // Gọi API xóa bưu tá
    fetch('/api/clear-notifications/', {
        method: 'POST',
        headers: { 
            'X-CSRFToken': getCookie('csrftoken'), // Lấy token trực tiếp từ cookie
            'Content-Type': 'application/json'
        }
    })
    .then(res => {
        if (!res.ok) throw new Error('Lỗi server');
        return res.json();
    })
    .then(data => {
        if(data.status === 'success') {
            // Xóa badge trên chuông
            const badge = document.querySelector('.fa-bell + span');
            if(badge) badge.style.display = 'none';
            
            // Cập nhật giao diện trống
            const container = document.getElementById('notif-list-container');
            if(container) {
                container.innerHTML = `<div style="text-align: center; padding: 50px 0;"><i class="fa-solid fa-mailbox" style="font-size: 30px; opacity: 0.1; margin-bottom: 20px;"></i><p style="font-weight: 800; color: white;">Hộp thư trống</p></div>`;
            }
            showToast("Hòm thư đã sạch bóng!", "success");
        }
    })
    .catch(err => {
        showToast("Lỗi: Không thể kết nối máy chủ!", "error");
    })
    .finally(() => {
        // ✅ QUAN TRỌNG: Dù thành công hay lỗi cũng phải dừng quay
        btn.innerHTML = originalHtml;
        btn.style.pointerEvents = 'auto';
    });
};

// 5. GÓP QUỸ HỘ (NỘP HỘ)
window.submitNopHo = function() {
    const amount = document.getElementById('nopHoAmount').value.replace(/\D/g, '');
    const name = document.getElementById('nopHoName').value;
    if (!amount || amount <= 0) { showToast("Số tiền không hợp lệ!", "error"); return; }

    document.getElementById('nopHoModal').style.display = 'none';
    showToast(`Đang xử lý nộp quỹ cho ${name}...`);

    fetch('/api/nop-quy-ho/', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            tv_id: document.getElementById('nopHoId').value,
            so_tien: amount,
            dot_thu_id: window.FUND_DATA.dotThuId
        })
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            showToast(data.message, "success");
            setTimeout(() => window.location.reload(), 1000);
        } else showToast(data.message, "error");
    });
};

// 6. CHATBOT AI LOGIC
window.toggleChatbot = function() {
    const bot = document.getElementById('chatbot-window');
    if (!bot) return;
    const isClosed = bot.style.opacity === "0" || bot.style.opacity === "";
    bot.style.transform = isClosed ? 'scale(1)' : 'scale(0)';
    bot.style.opacity = isClosed ? '1' : '0';
    bot.style.pointerEvents = isClosed ? 'auto' : 'none';
    if (isClosed) document.getElementById('chat-input')?.focus();
};

// 7. KHỞI TẠO KHI TRANG SẴN SÀNG
document.addEventListener('DOMContentLoaded', () => {
    // Tự động gán sự kiện cho các nút chatbot
    document.getElementById('chatbot-fab')?.addEventListener('click', toggleChatbot);
    document.getElementById('close-bot')?.addEventListener('click', toggleChatbot);
    document.getElementById('send-chat')?.addEventListener('click', sendChatMessage);
    document.getElementById('chat-input')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
});