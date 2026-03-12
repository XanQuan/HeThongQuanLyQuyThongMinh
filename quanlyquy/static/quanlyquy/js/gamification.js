/* ======================================================
   JAVASCRIPT CHO GAMIFICATION
   ====================================================== */

// 1. Chức năng Vòng quay nhân phẩm
function spinWheel() {
    const wheel = document.querySelector('.wheel');
    if (wheel) {
        // Tắt animation mặc định để bắt đầu quay theo JS
        wheel.style.animation = 'none';
        
        // Random ra số vòng xoay (từ 5 đến 10 vòng)
        let randomDegree = Math.floor(Math.random() * (3600 - 1800 + 1)) + 1800;
        
        // Thực hiện hiệu ứng quay
        wheel.style.transform = `rotate(${randomDegree}deg)`;
        
        // Chờ 3 giây cho vòng quay dừng lại rồi báo kết quả
        setTimeout(() => {
            alert('🎉 Chúc mừng! Bạn quay trúng Voucher giảm 10K cho tháng sau!');
            // Reset lại vòng quay mượt mà như cũ
            wheel.style.transform = 'rotate(0deg)';
            wheel.style.animation = 'spinSlow 3s linear infinite';
        }, 3100);
    }
}

// 2. Chức năng Chatbot
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
function openModal(id) { 
    const modal = document.getElementById(id);
    if(modal) modal.classList.add('active'); 
}
function closeModal(id) { 
    const modal = document.getElementById(id);
    if(modal) modal.classList.remove('active'); 
}