/* ======================================================
   XỬ LÝ NGHIỆP VỤ TIẾN ĐỘ THU (tien_do.js)
   ====================================================== */

// 1. Hàm Toggle Chatbot (Bản Fix Cứng 100%)
window.toggleChatbot = function() {
    const bot = document.getElementById('chatbot-window');
    if(!bot) return;

    // Check trạng thái dựa trên Opacity
    const isClosed = bot.style.opacity === "0" || bot.style.opacity === "";

    if (isClosed) {
        // MỞ BOT
        bot.style.transform = 'scale(1)';
        bot.style.opacity = '1';
        bot.style.pointerEvents = 'auto'; // Cho phép tương tác
        setTimeout(() => {
            const input = document.getElementById('chat-input');
            if(input) input.focus();
        }, 300);
    } else {
        // ĐÓNG BOT
        bot.style.transform = 'scale(0)';
        bot.style.opacity = '0';
        bot.style.pointerEvents = 'none'; // Không chặn click nút bên dưới
    }
};

// 2. Hàm Gửi Tin Nhắn
window.sendChatMessage = async function() {
    const input = document.getElementById('chat-input');
    const body = document.getElementById('chat-body');
    if(!input || !body) return;
    const message = input.value.trim();
    if (!message) return;

    const userMsg = document.createElement('div');
    userMsg.style.cssText = "align-self: flex-end; background: var(--theme-primary); color: white; padding: 10px 15px; border-radius: 15px 0 15px 15px; font-size: 13px; max-width: 80%; margin-top: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);";
    userMsg.innerText = message;
    body.appendChild(userMsg);
    input.value = '';
    body.scrollTop = body.scrollHeight;

    const botTyping = document.createElement('div');
    botTyping.style.cssText = "align-self: flex-start; background: white; padding: 10px 15px; border-radius: 0 15px 15px 15px; font-size: 13px; color: #64748b; font-style: italic; margin-top: 10px;";
    botTyping.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang phân tích...';
    body.appendChild(botTyping);
    body.scrollTop = body.scrollHeight;

    try {
        const response = await fetch('/api/chatbot/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken')},
            body: JSON.stringify({ message: message })
        });
        const data = await response.json();
        body.removeChild(botTyping);

        const botMsg = document.createElement('div');
        botMsg.style.cssText = "align-self: flex-start; background: white; padding: 10px 15px; border-radius: 0 15px 15px 15px; font-size: 13px; max-width: 80%; box-shadow: 0 2px 5px rgba(0,0,0,0.05); line-height: 1.5; margin-top: 10px; color: #334155;";
        botMsg.innerHTML = data.reply; 
        body.appendChild(botMsg);
        body.scrollTop = body.scrollHeight;
    } catch (error) { if(botTyping.parentNode) body.removeChild(botTyping); }
};

// 3. Hàm Lấy Token Bảo Mật
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

// 4. Các hàm bổ trợ khác cho trang Tiến độ
window.openModal = function(id) { 
    const m = document.getElementById(id);
    if(m) { m.style.display = 'flex'; m.classList.add('active'); }
};
window.closeModal = function(id) { 
    const m = document.getElementById(id);
    if(m) { m.style.display = 'none'; m.classList.remove('active'); }
};

window.openNopHoModal = function(id, name, mssv) {
    const idInput = document.getElementById('nopHoId');
    const nameInput = document.getElementById('nopHoName');
    const label = document.getElementById('nopHoLabel');
    if(idInput) idInput.value = id;
    if(nameInput) nameInput.value = name;
    if(label) label.innerText = `${name} (${mssv})`;
    openModal('nopHoModal');
};