/* ======================================================
   XỬ LÝ NGHIỆP VỤ TRANG GIAO DỊCH (giao_dich.js)
   ====================================================== */

// 1. Hàm cốt lõi: Kết hợp cả 2 bộ lọc (Tìm kiếm + Phân loại)
function applyFilters() {
    const typeFilter = document.getElementById('typeFilter');
    const searchInput = document.getElementById('searchInput');
    const rows = document.querySelectorAll('.tx-row');

    if (!rows.length) return;

    const filterType = typeFilter ? typeFilter.value : 'ALL';
    const searchText = searchInput ? searchInput.value.toLowerCase().trim() : '';

    rows.forEach(row => {
        const rowType = row.getAttribute('data-type');
        const textContent = row.textContent.toLowerCase();

        // 1.1 Kiểm tra điều kiện Loại (THU/CHI)
        let isMatch_Type = false;
        if (filterType === 'ALL') {
            isMatch_Type = true;
        } else if (filterType === 'THU' && (rowType === 'THU' || rowType === 'LAI')) {
            isMatch_Type = true;
        } else if (filterType === 'CHI' && (rowType === 'CHI' || rowType === 'TU')) {
            isMatch_Type = true;
        }

        // 1.2 Kiểm tra điều kiện Tìm kiếm (Text)
        let isMatch_Search = textContent.includes(searchText);

        // 1.3 Nếu thỏa mãn CẢ 2 điều kiện thì hiện, ngược lại thì ẩn
        if (isMatch_Type && isMatch_Search) {
            row.style.display = 'flex'; // Dùng 'flex' để giữ nguyên Layout xịn của bảng
        } else {
            row.style.display = 'none';
        }
    });
}

// 2. Hàm thiết lập các sự kiện lắng nghe (Event Listeners)
function setupEventListeners() {
    const typeFilter = document.getElementById('typeFilter');
    const searchInput = document.getElementById('searchInput');

    if (typeFilter) {
        typeFilter.addEventListener('change', applyFilters);
    }

    if (searchInput) {
        searchInput.addEventListener('keyup', applyFilters);
    }
}

// 3. Hàm kiểm tra URL (Khi click từ Dashboard sang hoặc share link)
function checkUrlSearchParam() {
    const urlParams = new URLSearchParams(window.location.search);
    const searchKey = urlParams.get('search');
    
    if (searchKey) {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = searchKey;
            applyFilters(); // Gọi hàm lọc luôn
            
            // Hiện Toast thông báo (Nếu ông có thư viện Toast)
            if (typeof showToast === 'function') {
                showToast(`Đang lọc lịch sử của: ${searchKey}`, 'info');
            }
        }
    }
}

// ================= KÍCH HOẠT KHI TRANG LOAD XONG =================
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners(); // Gắn sự kiện
    checkUrlSearchParam(); // Kiểm tra URL
});