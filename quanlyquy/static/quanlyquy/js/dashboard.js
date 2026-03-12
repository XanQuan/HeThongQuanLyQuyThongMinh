// ==========================================
// 1. CÁC HÀM TIỆN ÍCH CƠ BẢN (UTILITIES)
// ==========================================
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
    } return cookieValue;
}

function openModal(id) { document.getElementById(id).classList.add('active'); }

// Hàm đóng Modal kết hợp Reset Dữ liệu
function closeModal(id) { 
    const modal = document.getElementById(id);
    if(modal) {
        modal.classList.remove('active'); 

        // Nếu cái Modal vừa đóng là Modal Nộp Tiền thì tự động Reset mọi thứ
        if (id === 'depositModal') {
            // Xóa trắng tiền và lý do
            document.getElementById('inp-so-tien-thu').value = '';
            document.getElementById('inp-ly-do-thu').value = '';

            // Tắt gạt Ẩn Danh và reset UI về trạng thái gốc
            const incognitoToggle = document.getElementById('inp-an-danh');
            if (incognitoToggle) {
                incognitoToggle.checked = false; // Trả nút gạt về Off
                
                // Trả màu sắc về mặc định (giống hàm toggleIncognitoUI)
                const row = document.getElementById('incognito-row');
                const icon = document.getElementById('incognito-icon');
                const title = document.getElementById('incognito-title');
                const desc = document.getElementById('incognito-desc');
                
                if(row) {
                    row.style.borderColor = 'rgba(255,255,255,0.05)';
                    row.style.boxShadow = 'none';
                    row.style.background = 'rgba(255,255,255,0.02)';
                    icon.style.color = '#64748b';
                    title.style.color = 'var(--text-dark)';
                    desc.innerText = 'Người khác chỉ thấy "Nhà hảo tâm"';
                    desc.style.color = 'var(--text-light)';
                    desc.style.fontWeight = 'normal';
                }
            }
        }
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('systemToast');
    const icon = document.getElementById('toastIcon');
    const title = document.getElementById('toastTitle');
    const desc = document.getElementById('toastDesc');

    const config = {
        success: { icon: 'fa-circle-check', color: '#10b981', title: 'Thành công!' },
        error: { icon: 'fa-circle-exclamation', color: '#ef4444', title: 'Cảnh báo!' },
        info: { icon: 'fa-circle-info', color: '#7c3aed', title: 'Hệ thống' }
    };

    const s = config[type] || config.info;

    icon.className = `fa-solid ${s.icon}`;
    icon.style.color = s.color;
    title.innerText = s.title;
    desc.innerText = message;
    toast.style.borderLeft = `6px solid ${s.color}`;

    toast.classList.add('show');
    setTimeout(() => { toast.classList.remove('show'); }, 3000);
}

// ==========================================
// 2. XỬ LÝ GỌI API BACKEND (CÁC NÚT CHỨC NĂNG)
// ==========================================

// 2.1. CẬP NHẬT HÀM NỘP QUỸ (ĐẦY ĐỦ LOGIC PHÁO HOA & THÔNG BÁO)
function handleDeposit(e) {
    e.preventDefault(); 
    
    const payload = { 
        so_tien: getRawValue('inp-so-tien-thu'), 
        ly_do: document.getElementById('inp-ly-do-thu').value 
    };

    fetch('/api/nop-quy/', {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            closeModal('depositModal'); 
            showToast(data.message, 'success');
            // Hiệu ứng pháo hoa thành công
            confetti({ particleCount: 150, spread: 70, origin: { y: 0.6 } });
            setTimeout(() => window.location.reload(), 1500);
        } else { 
            showToast(data.message, 'error'); 
        }
    })
    .catch(err => {
        console.error(err);
        showToast('Lỗi kết nối máy chủ!', 'error');
    });
}

// 2.2. CẬP NHẬT HÀM TẠO PHIẾU CHI (ĐẦY ĐỦ LOGIC THÔNG BÁO)
function handleAdvance(e) {
    e.preventDefault(); 
    
    const payload = { 
        so_tien: getRawValue('inp-so-tien-chi'), 
        ly_do: document.getElementById('inp-ly-do-chi').value 
    };

    fetch('/api/tam-ung/', {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') { 
            closeModal('advanceModal');
            showToast(data.message, 'info'); 
            setTimeout(() => window.location.reload(), 1500); 
        } else { 
            showToast(data.message, 'error'); 
        }
    })
    .catch(err => {
        console.error(err);
        showToast('Lỗi kết nối máy chủ!', 'error');
    });
}

// Điều Chuyển Nội Bộ
function handleInternalTransfer(e) {
    e.preventDefault();
    const payload = {
        so_tien: document.getElementById('inp-so-tien-transfer').value,
        id_quy_di: document.getElementById('sel-quy-di').value,
        id_quy_den: document.getElementById('sel-quy-den').value,
        ly_do: "Điều chuyển quỹ nội bộ"
    };

    fetch('/api/chuyen-noi-bo/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify(payload)
    }).then(res => res.json()).then(data => {
        if(data.status === 'success') {
            closeModal('transferModal'); showToast(data.message, 'success');
            setTimeout(() => window.location.reload(), 1500);
        } else { showToast(data.message, 'error'); }
    });
}

// Nhắc Nợ Qua Email
function handleNhacNo(tvId) {
    showToast('Đang gửi yêu cầu nhắc nợ...', 'info');
    fetch('/api/nhac-no/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ tv_id: tvId })
    }).then(res => res.json()).then(data => {
        if(data.status === 'success') { showToast(data.message, 'success'); } 
        else { showToast(data.message, 'error'); }
    });
}

// ==========================================
// 3. LOGIC THÀNH VIÊN (AVATAR CLICK)
// ==========================================
let selectedMember = { id: null, name: "" };

function showFriendProfile(id, name, mssv, noXau) {
    selectedMember.id = id;
    selectedMember.name = name;

    document.getElementById('friend-name').innerText = name;
    document.getElementById('friend-mssv').innerText = 'MSSV: ' + mssv;
    document.getElementById('friend-avatar').src = `https://ui-avatars.com/api/?name=${name}&background=random&color=fff`;
    
    const statusBox = document.getElementById('friend-status');
    if (noXau === 'True' || noXau === true) {
        statusBox.innerHTML = '<span class="text-rose-500 font-bold"><i class="fa-solid fa-triangle-exclamation"></i> Đang nợ quỹ</span>';
        statusBox.style.background = '#fef2f2';
    } else {
        statusBox.innerHTML = '<span class="text-emerald-500 font-bold"><i class="fa-solid fa-check-circle"></i> Đóng quỹ đầy đủ</span>';
        statusBox.style.background = '#f0fdf4';
    }
    
    openModal('friendModal');
}

function goToMemberHistory() {
    if (!selectedMember.name) return;
    window.location.href = `/giao-dich/?search=${encodeURIComponent(selectedMember.name)}`;
}

function openQuickDeposit() {
    closeModal('friendModal');
    document.getElementById('quick-dep-name').innerText = selectedMember.name;
    openModal('quickDepositModal');
}

function handleMemberDeposit(e) {
    e.preventDefault();
    const payload = {
        tv_id: selectedMember.id,
        so_tien: document.getElementById('member-so-tien').value,
        ly_do: document.getElementById('member-ly-do').value
    };

    fetch('/api/nop-quy-ho/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            closeModal('quickDepositModal');
            showToast(`Đã thu ${payload.so_tien}đ từ ${selectedMember.name}`, 'success');
            confetti({ particleCount: 150, spread: 70, origin: { y: 0.6 } });
            setTimeout(() => window.location.reload(), 2000);
        } else {
            showToast(data.message, 'error');
        }
    });
}

// ==========================================
// 4. LOGIC GIAO DIỆN (MODALS, TABS, THẺ)
// ==========================================
function switchMainTab(tabId, element) {
    document.querySelectorAll('.main-tab-btn').forEach(t => {
        t.style.borderColor = 'transparent';
        t.style.color = 'var(--text-light)';
    });
    element.style.borderColor = 'var(--primary)';
    element.style.color = 'var(--primary)';

    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
}

function openBigCard(title, balance, number, bgGradient) {
    document.getElementById('bigCardTitle').innerText = title;
    document.getElementById('bigCardBackground').style.background = bgGradient;
    
    const balanceEl = document.getElementById('bigCardBalance');
    const numberEl = document.getElementById('bigCardNumber');
    
    balanceEl.setAttribute('data-value', balance);
    numberEl.setAttribute('data-value', number);

    if (!isDataVisible) {
        balanceEl.innerText = '*** đ';
        numberEl.innerText = '**** **** **** ' + number.slice(-4);
    } else {
        balanceEl.innerText = balance;
        numberEl.innerText = number;
    }
    openModal('bigCardModal');
}

// ==========================================
// 5. LOGIC XÁC THỰC BẢO MẬT (PIN CODE)
// ==========================================
let isDataVisible = false;

function handleEyeClick() {
    if (!isDataVisible) {
        openModal('pinModal');
        setTimeout(() => document.getElementById('pin1').focus(), 300);
    } else {
        lockSensitiveData();
    }
}

function verifyPin(event) {
    event.preventDefault();
    const fullPin = document.getElementById('pin1').value + 
                    document.getElementById('pin2').value + 
                    document.getElementById('pin3').value + 
                    document.getElementById('pin4').value;

    if (fullPin === '1234') { 
        unlockSensitiveData();
        closeModal('pinModal');
        showToast('Xác minh thành công. Dữ liệu đã mở!', 'success');
    } else {
        showToast('Mã PIN không chính xác!', 'error');
        const content = document.querySelector('#pinModal .modal-content');
        content.style.animation = 'shake 0.4s ease';
        setTimeout(() => content.style.animation = '', 400);
        document.getElementById('pinForm').reset();
        document.getElementById('pin1').focus();
    }
}

function unlockSensitiveData() {
    isDataVisible = true;
    const elements = document.querySelectorAll('.sensitive-data');
    const eyeIcon = document.getElementById('eye-icon');
    const statusBadge = document.getElementById('security-status');

    elements.forEach(el => {
        el.classList.add('revealed');
        if (el.hasAttribute('data-value')) {
            el.innerText = el.getAttribute('data-value');
        }
    });

    if (eyeIcon) eyeIcon.className = 'fa-regular fa-eye text-primary cursor-pointer text-xl';
    if (statusBadge) {
        statusBadge.innerHTML = '<i class="fa-solid fa-unlock"></i> ĐÃ XÁC MINH';
        statusBadge.className = 'text-[10px] font-bold px-2 py-1 rounded-lg bg-emerald-100 text-emerald-600';
    }
}

function lockSensitiveData() {
    isDataVisible = false;
    const elements = document.querySelectorAll('.sensitive-data');
    const eyeIcon = document.getElementById('eye-icon');
    const statusBadge = document.getElementById('security-status');

    elements.forEach(el => {
        el.classList.remove('revealed');
        if (el.hasAttribute('data-value')) {
            const val = el.getAttribute('data-value');
            if(val.length > 10 && val.includes(' ')) {
                el.innerText = '**** **** **** ' + val.slice(-4);
            } else {
                el.innerText = '***' + (val.includes('đ') ? ' đ' : '');
            }
        }
    });

    if (eyeIcon) eyeIcon.className = 'fa-regular fa-eye-slash text-light cursor-pointer text-xl';
    if (statusBadge) {
        statusBadge.innerHTML = '<i class="fa-solid fa-lock"></i> ĐÃ KHÓA';
        statusBadge.className = 'text-[10px] font-bold px-2 py-1 rounded-lg bg-slate-100 text-slate-500';
    }
}

// ==========================================
// 6. KHỞI TẠO BIỂU ĐỒ (CHART.JS) VÀ SỰ KIỆN DOM
// ==========================================
let mainChart;
let currentChartType = 'thu';
let ctx;

document.addEventListener('DOMContentLoaded', function() {
    // A. Xử lý ô nhập PIN (Tự nhảy ô)
    const inputs = document.querySelectorAll('.pin-inputs input');
    inputs.forEach((input, index) => {
        input.addEventListener('input', () => {
            if (input.value.length === 1 && index < inputs.length - 1) inputs[index + 1].focus();
        });
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && input.value.length === 0 && index > 0) inputs[index - 1].focus();
        });
    });

    // B. Khởi tạo Biểu đồ
    const canvas = document.getElementById('statChart');
    if (canvas) {
        ctx = canvas.getContext('2d');
        mainChart = new Chart(ctx, {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'VNĐ', data: [], borderWidth: 4, tension: 0.4, fill: true, pointRadius: 4, pointHoverRadius: 8 }] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { backgroundColor: '#111827', titleColor: '#fff', bodyColor: '#fff', padding: 12 } },
                scales: { x: { grid: { display: false }, border: {display: false}, ticks: {color: '#9ca3af', font: {size: 11}} }, y: { border: {display: false}, grid: { color: '#f3f4f6' }, ticks: { display: false } } }
            }
        });
    }

    // Hàm áp dụng màu cho Chart
    function applyChartStyle() {
        if (!window.CHART_DATA_THU || !window.CHART_DATA_CHI || !mainChart) return;
        let dataToUse = currentChartType === 'thu' ? window.CHART_DATA_THU : window.CHART_DATA_CHI;
        mainChart.data.datasets[0].data = dataToUse;

        if (currentChartType === 'thu') {
            mainChart.data.datasets[0].borderColor = '#10b981'; 
            let grad = ctx.createLinearGradient(0, 0, 0, 250);
            grad.addColorStop(0, 'rgba(16, 185, 129, 0.4)'); grad.addColorStop(1, 'rgba(16, 185, 129, 0)');
            mainChart.data.datasets[0].backgroundColor = grad;
        } else {
            mainChart.data.datasets[0].borderColor = '#ef4444'; 
            let grad = ctx.createLinearGradient(0, 0, 0, 250);
            grad.addColorStop(0, 'rgba(239, 68, 68, 0.4)'); grad.addColorStop(1, 'rgba(239, 68, 68, 0)');
            mainChart.data.datasets[0].backgroundColor = grad;
        }
        mainChart.update();
    }

    // Hàm gọi API biểu đồ
    function updateChartData(filterType) {
        fetch(`/api/chart-data/?filter=${filterType}`)
            .then(res => {
                if (!res.ok) throw new Error("Lỗi Server");
                return res.json();
            })
            .then(data => {
                if(data.status === 'error') throw new Error(data.message);
                
                if (data.labels.length === 0) {
                    mainChart.data.labels = ['Trống'];
                    window.CHART_DATA_THU = [0];
                    window.CHART_DATA_CHI = [0];
                    showToast('Không có giao dịch nào!', 'info');
                } else {
                    mainChart.data.labels = data.labels;
                    window.CHART_DATA_THU = data.data_thu;
                    window.CHART_DATA_CHI = data.data_chi;
                }
                applyChartStyle(); 
            })
            .catch(err => {
                console.warn("Dùng dữ liệu dự phòng do API chưa sẵn sàng.");
                // DATA GIẢ LẬP KHI BACKEND CHƯA CHẠY
                mainChart.data.labels = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'CN'];
                window.CHART_DATA_THU = [150000, 200000, 50000, 300000, 450000, 250000, 600000];
                window.CHART_DATA_CHI = [50000, 80000, 20000, 100000, 90000, 200000, 150000];
                applyChartStyle();
            });
    }

    // Chạy mặc định 7 ngày qua
    updateChartData('7days');

    // Lắng nghe Dropdown Filter
    const timeFilter = document.getElementById('timeFilter');
    if (timeFilter) {
        timeFilter.addEventListener('change', (e) => updateChartData(e.target.value));
    }

    // Lắng nghe Tab Thu/Chi
    const pillTabs = document.querySelectorAll('#thuChiTabs .pill-tab');
    pillTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            pillTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            currentChartType = this.getAttribute('data-type');
            applyChartStyle(); 
        });
    });

    // C. Animation cho thanh Progress
    setTimeout(() => {
        document.querySelectorAll('.progress-bar').forEach(bar => {
            bar.style.width = bar.getAttribute('data-width');
        });
    }, 800);
});
// ==========================================
// BỘ GÕ TIỀN TỰ ĐỘNG THÊM DẤU CHẤM (.)
// ==========================================
function formatCurrency(input) {
    // 1. Lấy giá trị thô (chỉ giữ lại số)
    let value = input.value.replace(/\D/g, "");
    
    // 2. Thêm dấu chấm phân cách hàng nghìn
    value = value.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    
    // 3. Hiển thị lại vào ô input
    input.value = value;
}

document.addEventListener('DOMContentLoaded', function() {
    // Tìm tất cả các ô nhập tiền và gắn sự kiện gõ phím
    const currencyInputs = document.querySelectorAll('.currency-input');
    currencyInputs.forEach(input => {
        input.addEventListener('input', function() {
            formatCurrency(this);
        });
    });
});
///////////////HÀM XỬ LÝ TIỀN TỆ///////////
// 1. Hàm định dạng tiền tệ khi đang gõ (Thêm dấu chấm sau mỗi 3 chữ số)
function formatMoneyInput(el) {
    // Chỉ giữ lại các chữ số
    let value = el.value.replace(/\D/g, "");
    
    if (value === "") {
        el.value = "";
        return;
    }

    // Định dạng theo kiểu Việt Nam (dấu chấm phân cách phần nghìn)
    el.value = new Intl.NumberFormat('de-DE').format(value);
}

// 2. Hàm loại bỏ dấu chấm để lấy số nguyên thuần túy khi gửi API
function getRawValue(id) {
    let val = document.getElementById(id).value;
    return val.replace(/\./g, ""); // Xóa toàn bộ dấu chấm
}

// 3. Cập nhật hàm nộp tiền hộ thành viên (Fix nút bấm ở Ảnh 2)
function handleMemberDeposit(e) {
    e.preventDefault();
    
    // Lấy số tiền và XÓA BỎ dấu chấm (.) để Backend nhận được số thuần túy
    const rawAmount = document.getElementById('member-so-tien').value.replace(/\./g, "");
    
    const payload = {
        tv_id: selectedMember.id,
        so_tien: rawAmount,
        ly_do: document.getElementById('member-ly-do').value
    };

    showToast('Đang xử lý giao dịch...', 'info');

    fetch('/api/nop-quy-ho/', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json', 
            'X-CSRFToken': getCookie('csrftoken') 
        },
        body: JSON.stringify(payload)
    })
    .then(res => {
        if (!res.ok) throw new Error("Lỗi kết nối API");
        return res.json();
    })
    .then(data => {
        if(data.status === 'success') {
            closeModal('quickDepositModal');
            showToast(`Giao dịch thành công! Đã thu ${document.getElementById('member-so-tien').value}đ`, 'success');
            confetti({ particleCount: 150, spread: 70, origin: { y: 0.6 } });
            setTimeout(() => window.location.reload(), 2000);
        } else {
            showToast(data.message || 'Lỗi từ phía Server', 'error');
        }
    })
    .catch(err => {
        console.error(err);
        // THÔNG BÁO LỖI KẾT NỐI (Thường do URL /api/nop-quy-ho/ chưa khai báo trong urls.py)
        showToast('Cảnh báo! Không thể kết nối đến máy chủ. Hãy kiểm tra lại Backend!', 'error');
    });
}



// ==========================================
// TÍNH NĂNG AI: NHẬN DIỆN GIỌNG NÓI (VOICE TO TEXT)
// ==========================================
function startVoiceRecognition(inputId, btnElement) {
    // Kiểm tra trình duyệt có hỗ trợ Web Speech API không
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.lang = 'vi-VN'; // Set ngôn ngữ tiếng Việt
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        // Bật hiệu ứng đang thu âm
        btnElement.classList.add('recording-pulse');
        showToast('Đang lắng nghe... Hãy nói lý do giao dịch', 'info');

        recognition.start();

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            // Tự động điền text vào ô input và viết hoa chữ cái đầu
            document.getElementById(inputId).value = transcript.charAt(0).toUpperCase() + transcript.slice(1);
            showToast('Đã nhận diện thành công!', 'success');
        };

        recognition.onerror = function(event) {
            console.error(event.error);
            showToast('Không nghe rõ, vui lòng thử lại!', 'error');
        };

        recognition.onend = function() {
            // Tắt hiệu ứng khi kết thúc
            btnElement.classList.remove('recording-pulse');
        };
    } else {
        showToast('Trình duyệt của bạn chưa hỗ trợ nhận diện giọng nói!', 'error');
    }
}

// ==========================================
// 7. TRỢ LÝ ẢO CHATBOT AI
// ==========================================
let isChatOpen = false;

function toggleChatbot() {
    const chatWindow = document.getElementById('chatbot-window');
    isChatOpen = !isChatOpen;
    if (isChatOpen) {
        chatWindow.style.transform = 'scale(1)';
        chatWindow.style.opacity = '1';
        document.getElementById('chat-input').focus();
    } else {
        chatWindow.style.transform = 'scale(0)';
        chatWindow.style.opacity = '0';
    }
}

function appendMessage(text, sender) {
    const chatBody = document.getElementById('chat-body');
    const msgDiv = document.createElement('div');
    
    // 1. XỬ LÝ ĐỊNH DẠNG VĂN BẢN (MARKDOWN CỦA GEMINI)
    // - In đậm: **nội dung** -> <b>nội dung</b>
    let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
    
    // - Gạch đầu dòng: Chuyển dấu "*" ở đầu dòng thành dấu chấm tròn đẹp mắt
    // (Xử lý trước khi chuyển đổi dấu xuống dòng để không bị lẫn)
    formattedText = formattedText.replace(/^\* (.*$)/gim, 
        '<div style="margin-left: 10px; margin-bottom: 4px; display: flex; gap: 8px;"><span>•</span><span>$1</span></div>');

    // - Xuống dòng: Chuyển \n thành <br> để văn bản không bị dính chùm
    formattedText = formattedText.replace(/\n/g, '<br>');

    // 2. THIẾT LẬP STYLE CHUNG CHO KHUNG TIN NHẮN
    msgDiv.style.padding = '12px 18px';
    msgDiv.style.fontSize = '13px';
    msgDiv.style.maxWidth = '85%';
    msgDiv.style.lineHeight = '1.6';
    msgDiv.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.03)';
    msgDiv.style.marginBottom = '5px';
    msgDiv.innerHTML = formattedText;

    // 3. PHÂN LOẠI GIAO DIỆN THEO NGƯỜI GỬI
    if (sender === 'user') {
        // STYLE NGƯỜI DÙNG: Màu Tím Indigo Gradient đồng bộ Sidebar/Nút bấm
        msgDiv.style.alignSelf = 'flex-end';
        msgDiv.style.background = 'linear-gradient(135deg, var(--primary) 0%, #a855f7 100%)';
        msgDiv.style.color = 'white';
        msgDiv.style.borderRadius = '18px 18px 0 18px';
    } else {
        // STYLE BOT: Màu trắng tinh khôi, chữ xám đen chuyên nghiệp (Slate 800)
        msgDiv.style.alignSelf = 'flex-start';
        msgDiv.style.background = '#ffffff';
        msgDiv.style.color = '#1e293b'; 
        msgDiv.style.borderRadius = '0 18px 18px 18px';
        msgDiv.style.border = '1px solid #f1f5f9'; // Viền rất nhạt để tạo khối
    }

    // 4. HIỆU ỨNG XUẤT HIỆN (ANIMATION)
    chatBody.appendChild(msgDiv);
    msgDiv.animate([
        { opacity: 0, transform: 'translateY(10px) scale(0.95)' },
        { opacity: 1, transform: 'translateY(0) scale(1)' }
    ], { duration: 300, easing: 'ease-out' });

    // Luôn cuộn xuống tin nhắn mới nhất
    chatBody.scrollTop = chatBody.scrollHeight;
}

function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    // 1. Hiện tin nhắn của người dùng
    appendMessage(message, 'user');
    input.value = '';

    // 2. Hiện hiệu ứng "Bot đang gõ..."
    const chatBody = document.getElementById('chat-body');
    const typingIndicator = document.createElement('div');
    typingIndicator.id = 'typing-indicator';
    typingIndicator.style.alignSelf = 'flex-start';
    typingIndicator.style.color = '#94a3b8';
    typingIndicator.style.fontSize = '12px';
    typingIndicator.style.fontStyle = 'italic';
    typingIndicator.innerText = 'Bot đang suy nghĩ...';
    chatBody.appendChild(typingIndicator);
    chatBody.scrollTop = chatBody.scrollHeight;

    // 3. Gửi API lên Server
    fetch('/api/chatbot/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ message: message })
    })
    .then(res => res.json())
    .then(data => {
        // Tắt hiệu ứng gõ chữ
        document.getElementById('typing-indicator').remove();
        
        // Hiện tin nhắn phản hồi của Bot
        appendMessage(data.reply, 'bot');
    })
    .catch(err => {
        document.getElementById('typing-indicator').remove();
        appendMessage('Lỗi kết nối mạng, vui lòng thử lại!', 'bot');
    });
}
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

// Xử lý Custom Dropdown Thời gian
    function toggleDropdown() {
        const container = document.getElementById('customTimeFilter');
        const icon = document.getElementById('dropdown-icon');
        container.classList.toggle('active');
        icon.style.transform = container.classList.contains('active') ? 'rotate(180deg)' : 'rotate(0deg)';
    }

    function selectOption(element) {
        // Lấy giá trị và text
        const value = element.getAttribute('data-value');
        const text = element.innerText;

        // Đổi chữ hiển thị
        document.getElementById('selected-text').innerText = text;

        // Xóa active cũ, thêm active mới
        document.querySelectorAll('.dropdown-option').forEach(el => el.classList.remove('active-opt'));
        element.classList.add('active-opt');

        // Đóng menu
        toggleDropdown();

        // Đồng bộ với thẻ <select> ẩn và kích hoạt event 'change' cho dashboard.js nhận diện
        const hiddenSelect = document.getElementById('timeFilter');
        hiddenSelect.value = value;
        hiddenSelect.dispatchEvent(new Event('change'));
    }

    // Click ra ngoài để đóng menu
    document.addEventListener('click', function(event) {
        const container = document.getElementById('customTimeFilter');
        if (!container.contains(event.target)) {
            container.classList.remove('active');
            document.getElementById('dropdown-icon').style.transform = 'rotate(0deg)';
        }
    });

/* ======================================================
   GLOBAL SYSTEM & DEV TOOLS (HOTKEYS, PROFILER, BUG)
   ====================================================== */

// 1. CHỨC NĂNG BUG BOUNTY
function openBugBounty() {
    const modal = document.getElementById('bugBountyModal');
    if (modal) modal.style.display = 'flex';
}
// Gửi Bug thật vào DB của ông
function submitBugBounty() {
    const noiDung = document.getElementById('bugContent').value;
    if (!noiDung) { alert("Vui lòng nhập mô tả lỗi!"); return; }

    // Gọi API của hệ thống (Nhớ thiết lập URL /api/bug-report/ trong urls.py)
    fetch('/api/bug-report/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') // Hàm lấy token bảo mật của Django
        },
        body: JSON.stringify({ mo_ta: noiDung })
    })
    .then(response => response.json())
    .then(data => {
        if(data.success) {
            alert('Đã ghi nhận vào Database! Tester (Admin) sẽ kiểm tra và cộng Xu!');
            document.getElementById('bugBountyModal').style.display='none';
            document.getElementById('bugContent').value = '';
        }
    });
}

// 2. CHỨC NĂNG HOTKEYS (PHÍM TẮT)
document.addEventListener('keydown', function(event) {
    // Nhấn Ctrl + F để focus vào thanh tìm kiếm
    if (event.ctrlKey && event.key === 'f') {
        event.preventDefault(); // Chặn hành động tìm kiếm mặc định
        const searchBox = document.querySelector('input[name="search"]');
        if (searchBox) {
            searchBox.focus();
            searchBox.placeholder = "Đang tìm kiếm... (Nhấn Esc để thoát)";
        } else {
            alert('Trang này không có chức năng tìm kiếm!');
        }
    }
    
    // Nhấn Ctrl + N để tạo giao dịch mới (Kiểm tra bằng biến IS_ADMIN truyền từ HTML)
    if (event.ctrlKey && event.key === 'n') {
        event.preventDefault();
        // Biến IS_ADMIN đã được định nghĩa ở thẻ <script> trong file HTML
        if (typeof IS_ADMIN !== 'undefined' && IS_ADMIN === true) {
            window.location.href = '/admin/quanlyquy/giaodich/add/';
        } else {
            alert('Tính năng này chỉ dành cho Thủ quỹ/Admin.');
        }
    }
});

// 3. GIẢ LẬP ĐO HIỆU SUẤT API (Performance Profiler)
// Chỉ chạy bộ đếm nếu là Admin
if (typeof IS_ADMIN !== 'undefined' && IS_ADMIN === true) {
    setInterval(() => {
        const pingEl = document.getElementById('ping-time');
        const apiEl = document.getElementById('api-time');
        
        if (pingEl && apiEl) {
            pingEl.innerText = Math.floor(Math.random() * 20) + 10; // Random 10-30ms
            apiEl.innerText = Math.floor(Math.random() * 50) + 30; // Random 30-80ms
        }
    }, 3000);
}

// Hàm tạo hiệu ứng thị giác khi gạt nút Ẩn danh
function toggleIncognitoUI(checkbox) {
    const row = document.getElementById('incognito-row');
    const icon = document.getElementById('incognito-icon');
    const title = document.getElementById('incognito-title');
    const desc = document.getElementById('incognito-desc');

    if (checkbox.checked) {
        // TRẠNG THÁI BẬT: Sáng rực rỡ, đổi chữ báo hiệu
        row.style.borderColor = 'var(--theme-primary)';
        row.style.boxShadow = '0 0 15px var(--theme-glow)';
        row.style.background = 'rgba(255,255,255,0.05)'; // Sáng nền lên xíu
        
        icon.style.color = 'var(--theme-primary)';
        title.style.color = 'var(--theme-primary)';
        
        desc.innerText = 'Đang bật: Tên của bạn sẽ được giấu kín!';
        desc.style.color = '#10b981'; // Chữ xanh lá báo thành công
        desc.style.fontWeight = 'bold';
    } else {
        // TRẠNG THÁI TẮT: Trở về màu xám trầm mặc định
        row.style.borderColor = 'rgba(255,255,255,0.05)';
        row.style.boxShadow = 'none';
        row.style.background = 'rgba(255,255,255,0.02)';
        
        icon.style.color = '#64748b';
        title.style.color = 'var(--text-dark)';
        
        desc.innerText = 'Người khác chỉ thấy "Nhà hảo tâm"';
        desc.style.color = 'var(--text-light)';
        desc.style.fontWeight = 'normal';
    }
}