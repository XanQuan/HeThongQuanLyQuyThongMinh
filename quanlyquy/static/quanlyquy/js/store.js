/* ======================================================
   XỬ LÝ NGHIỆP VỤ CỬA HÀNG (store.js)
   ====================================================== */

// Quản lý Modals
function openModal(id) { 
    const el = document.getElementById(id);
    if(el) { 
        el.style.display = 'flex'; 
        el.classList.add('active'); 
    }
}

function closeModal(id) { 
    const el = document.getElementById(id);
    if(el) { 
        el.style.display = 'none'; 
        el.classList.remove('active'); 
    }
}

// Logic kiểm tra điểm trước khi đổi quà
function confirmExchange(itemName, itemPrice, userBalance) {
    if (userBalance < itemPrice) {
        alert(`❌ Không đủ Xu! Bạn cần thêm ${itemPrice - userBalance} Xu nữa để đổi "${itemName}".\nHãy làm nhiệm vụ hoặc nộp quỹ để tích thêm Xu nhé!`);
        return;
    }
    
    if (confirm(`🎁 Bạn có chắc chắn muốn dùng ${itemPrice} Xu để đổi "${itemName}" không?`)) {
        alert("✅ Yêu cầu đổi quà thành công! Hệ thống đã báo cho Lớp trưởng duyệt.");
        // Gợi ý cho Tech Lead: Chỗ này sau gọi API AJAX nộp request trừ tiền
    }
}