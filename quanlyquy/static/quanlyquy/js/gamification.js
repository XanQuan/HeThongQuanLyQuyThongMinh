/* ======================================================
   JAVASCRIPT CHO GAMIFICATION (gamification.js)
   ====================================================== */

// --- BỘ CÔNG CỤ DÙNG CHUNG ---
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

window.showToast = function(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
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
    setTimeout(() => toast.style.transform = 'translateX(0)', 10);
    setTimeout(() => { toast.style.transform = 'translateX(120%)'; setTimeout(() => toast.remove(), 300); }, 4000);
};

window.openModal = function(id) { 
    const el = document.getElementById(id);
    if(el) { el.style.display = 'flex'; el.classList.add('active'); }
};
window.closeModal = function(id) { 
    const el = document.getElementById(id);
    if(el) { el.style.display = 'none'; el.classList.remove('active'); }
};

// --- CHATBOT AI ---
window.toggleChatbot = function() {
    const bot = document.getElementById('chatbot-window');
    if(!bot) return;
    if(bot.style.transform === 'scale(1)') {
        bot.style.transform = 'scale(0)'; bot.style.opacity = '0';
    } else {
        bot.style.transform = 'scale(1)'; bot.style.opacity = '1';
        document.getElementById('chat-input').focus();
    }
};

window.sendChatMessage = async function() {
    const input = document.getElementById('chat-input');
    const body = document.getElementById('chat-body');
    if(!input || !body) return;
    const message = input.value.trim();
    if (!message) return;

    const userMsg = document.createElement('div');
    userMsg.style.cssText = "align-self: flex-end; background: var(--theme-primary); color: white; padding: 10px 15px; border-radius: 15px 0 15px 15px; font-size: 13px; max-width: 80%; margin-top: 10px;";
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
        botMsg.style.cssText = "align-self: flex-start; background: white; padding: 10px 15px; border-radius: 0 15px 15px 15px; font-size: 13px; max-width: 80%; box-shadow: 0 2px 5px rgba(0,0,0,0.05); line-height: 1.5; margin-top: 10px;";
        botMsg.innerHTML = data.reply; 
        body.appendChild(botMsg);
        body.scrollTop = body.scrollHeight;
    } catch (error) { if(botTyping.parentNode) body.removeChild(botTyping); }
};

// --- NGHIỆP VỤ GAME ---
let currentRotation = 0;
window.playGacha = function() {
    const btn = document.getElementById('spinBtn');
    const wheel = document.getElementById('gachaWheel');
    if (!wheel) return;

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> ĐANG XỬ LÝ...';
    }

    fetch('/api/gacha/spin/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'error') {
            showToast(data.message, 'error');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = 'QUAY NGAY <span style="background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 6px; font-size: 10px;">-20 XU</span>';
            }
            return;
        }

        wheel.style.animation = 'none'; 
        currentRotation += data.angle; 
        wheel.style.transition = 'transform 4s cubic-bezier(0.1, 0.7, 0.1, 1)';
        wheel.style.transform = `rotate(${currentRotation}deg)`;

        setTimeout(() => {
            showToast(data.message, data.prize > 0 ? 'success' : 'error');
            setTimeout(() => { location.reload(); }, 2000);
        }, 4000);
    })
    .catch(err => {
        showToast('Lỗi kết nối mạng!', 'error');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = 'QUAY NGAY <span style="background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 6px; font-size: 10px;">-20 XU</span>';
        }
    });
};

window.submitVote = function(pollId) {
    fetch('/api/gacha/vote/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ poll_id: pollId })
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            showToast(data.message, 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(err => showToast('Lỗi kết nối mạng!', 'error'));
};

window.toggleQuests = function() {
    const extraQuests = document.querySelectorAll('.extra-quest');
    const btn = document.getElementById('toggleQuestBtn');
    if (!extraQuests.length) return;

    const isHidden = extraQuests[0].style.display === 'none';
    if (isHidden) {
        extraQuests.forEach(q => q.style.display = 'flex');
        btn.innerHTML = 'Thu gọn danh sách <i class="fa-solid fa-chevron-up ms-2"></i>';
        btn.style.background = 'rgba(239, 68, 68, 0.05)';
        btn.style.color = '#f87171';
        btn.style.borderColor = 'rgba(239, 68, 68, 0.3)';
    } else {
        extraQuests.forEach(q => q.style.display = 'none');
        btn.innerHTML = `Xem thêm ${extraQuests.length} nhiệm vụ <i class="fa-solid fa-chevron-down ms-2"></i>`;
        btn.style.background = 'rgba(56, 189, 248, 0.05)';
        btn.style.color = '#38bdf8';
        btn.style.borderColor = 'rgba(56, 189, 248, 0.3)';
        document.getElementById('quest-container').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
};