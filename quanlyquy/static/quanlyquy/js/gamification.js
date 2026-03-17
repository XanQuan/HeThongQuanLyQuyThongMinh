/* ======================================================
   JAVASCRIPT CHO GAMIFICATION
   ====================================================== */

// 0. Hệ thống Thông báo Toast (Dành cho Khu vui chơi)
window.showToast = function(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        // Nếu chưa có container thì tạo luôn để không bị lỗi
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position: fixed; top: 30px; right: 30px; z-index: 99999; display: flex; flex-direction: column; gap: 12px;';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const color = type === 'success' ? '#10b981' : (type === 'error' ? '#ef4444' : '#3b82f6');
    const icon = type === 'success' ? 'fa-gift' : 'fa-circle-exclamation';
    
    toast.style.cssText = `background: rgba(15, 23, 42, 0.95); border-left: 4px solid ${color}; color: white; padding: 16px 20px; border-radius: 12px; font-size: 13px; font-weight: 600; box-shadow: 0 10px 30px rgba(0,0,0,0.5); display: flex; align-items: center; gap: 12px; transform: translateX(120%); transition: 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.05); margin-bottom: 10px;`;
    toast.innerHTML = `<i class="fa-solid ${icon}" style="color: ${color}; font-size: 18px;"></i> ${message}`;
    
    container.appendChild(toast);
    
    // Hiệu ứng trượt vào
    setTimeout(() => toast.style.transform = 'translateX(0)', 10);
    // Tự động biến mất sau 4 giây
    setTimeout(() => {
        toast.style.transform = 'translateX(120%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
};

// 1. Chức năng Vòng quay nhân phẩm
function spinWheel() {
    const wheel = document.querySelector('.wheel');
    if (wheel) {
        // Báo đang trừ Xu trước
        showToast('Đang quay... Trừ 20 Xu từ ví!', 'info');

        // Tắt animation mặc định để bắt đầu quay theo JS
        wheel.style.animation = 'none';
        
        // Random ra số vòng xoay (từ 5 đến 10 vòng) + Tốc độ cực gắt
        let randomDegree = Math.floor(Math.random() * (3600 - 1800 + 1)) + 1800;
        
        // Thực hiện hiệu ứng quay
        wheel.style.transform = `rotate(${randomDegree}deg)`;
        
        // Chờ 3 giây cho vòng quay dừng lại rồi báo kết quả bằng TOAST
        setTimeout(() => {
            showToast('🎉 Chúc mừng! Bạn quay trúng Voucher Giảm 10K (Sẽ sớm cập nhật vào Kho)!', 'success');
            
            // Reset lại vòng quay chầm chậm như cũ sau 2 giây nữa
            setTimeout(() => {
                wheel.style.transition = 'none';
                wheel.style.transform = 'rotate(0deg)';
                setTimeout(() => {
                    wheel.style.transition = 'transform 3s cubic-bezier(0.25, 0.1, 0.25, 1)';
                    wheel.style.animation = 'spinSlow 15s linear infinite';
                }, 50);
            }, 2000);
        }, 3100);
    }
}

// 2. Chức năng Chatbot (Giữ nguyên của sếp)
function toggleChatbot() {
    const bot = document.getElementById('chatbot-window');
    if (bot) {
        if (bot.style.transform === 'scale(0)' || bot.style.transform === '') {
            bot.style.transform = 'scale(1)'; 
            bot.style.opacity = '1';
        } else {
            bot.style.transform = 'scale(0)'; 
            bot.style.opacity = '0';
        }
    }
}

// Gửi tin nhắn chatbot đơn giản
function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const body = document.getElementById('chat-body');
    
    if (input && input.value.trim() !== '') {
        const userMsg = document.createElement('div');
        userMsg.style.cssText = "align-self: flex-end; background: var(--theme-primary); color: white; padding: 12px 16px; border-radius: 16px 0 16px 16px; font-size: 13px; max-width: 80%; margin-top: 10px;";
        userMsg.innerText = input.value;
        body.appendChild(userMsg);
        
        input.value = '';
        body.scrollTop = body.scrollHeight;

        // Giả lập AI trả lời sau 1 giây
        setTimeout(() => {
            const aiMsg = document.createElement('div');
            aiMsg.style.cssText = "align-self: flex-start; background: white; padding: 12px 16px; border-radius: 0 16px 16px 16px; font-size: 13px; color: #334155; box-shadow: 0 2px 5px rgba(0,0,0,0.02); max-width: 80%; margin-top: 10px;";
            aiMsg.innerText = "Chức năng AI đang được nhà phát triển cập nhật! 🚀";
            body.appendChild(aiMsg);
            body.scrollTop = body.scrollHeight;
        }, 1000);
    }
}

// 3. Modal dùng chung
window.openModal = function(id) { 
    const modal = document.getElementById(id);
    if(modal) modal.classList.add('active'); 
};
window.closeModal = function(id) { 
    const modal = document.getElementById(id);
    if(modal) modal.classList.remove('active'); 
};