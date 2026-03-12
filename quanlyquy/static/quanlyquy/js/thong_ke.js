document.addEventListener('DOMContentLoaded', function() {
    // Cấu hình chung cho toàn bộ biểu đồ giao diện sáng
    Chart.defaults.color = '#64748b';
    Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
    Chart.defaults.plugins.tooltip.backgroundColor = '#111827';
    Chart.defaults.plugins.tooltip.titleColor = '#fff';
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;

    const gridOptions = { color: '#f3f4f6', drawBorder: false };

    // --- ĐỌC DỮ LIỆU TỪ HTML (DO DJANGO TRUYỀN XUỐNG) ---
    // Chart 1: Line
    const c1_labels = JSON.parse(document.getElementById('c1-labels').textContent);
    const c1_thu = JSON.parse(document.getElementById('c1-thu').textContent);
    const c1_chi = JSON.parse(document.getElementById('c1-chi').textContent);

    // Chart 2: Doughnut (Chi tiêu)
    const c2_labels = JSON.parse(document.getElementById('c2-labels').textContent);
    const c2_data = JSON.parse(document.getElementById('c2-data').textContent);

    // Chart 3: Horizontal Bar (Thành viên đóng góp)
    const c3_labels = JSON.parse(document.getElementById('c3-labels').textContent);
    const c3_data = JSON.parse(document.getElementById('c3-data').textContent);

    // Chart 4: Stacked Bar (Tiến độ thu)
    const c4_labels = JSON.parse(document.getElementById('c4-labels').textContent);
    const c4_dathu = JSON.parse(document.getElementById('c4-dathu').textContent);
    const c4_no = JSON.parse(document.getElementById('c4-no').textContent);

    // Chart 5: Pie (Ngân sách quỹ)
    const c5_labels = JSON.parse(document.getElementById('c5-labels').textContent);
    const c5_data = JSON.parse(document.getElementById('c5-data').textContent);


    // =================================================================
    // THUẬT TOÁN AI: DỰ BÁO HỒI QUY TUYẾN TÍNH (LINEAR REGRESSION)
    // =================================================================
    function predictNextMonth(dataArray) {
        if (dataArray.length < 2) return 0;
        let n = dataArray.length;
        let sumX = 0, sumY = 0, sumXY = 0, sumXX = 0;
        
        for (let i = 0; i < n; i++) {
            sumX += i;
            sumY += dataArray[i];
            sumXY += i * dataArray[i];
            sumXX += i * i;
        }
        // Tính độ dốc (m) và điểm cắt (b) của đường xu hướng
        let m = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
        let b = (sumY - m * sumX) / n;
        
        // Dự báo tháng tiếp theo (vị trí n)
        let prediction = m * n + b;
        return prediction > 0 ? Math.round(prediction) : 0; // Không cho phép số âm
    }

    // Nếu có dữ liệu quá khứ, tiến hành dự báo tương lai
    if (c1_labels.length > 0) {
        const nextThu = predictNextMonth(c1_thu);
        const nextChi = predictNextMonth(c1_chi);

        // Đẩy dữ liệu tương lai vào mảng
        c1_labels.push('Tháng tới (AI)');
        c1_thu.push(nextThu);
        c1_chi.push(nextChi);
    }


    // --- VẼ BIỂU ĐỒ BẰNG DỮ LIỆU THẬT VÀ DỮ LIỆU DỰ BÁO ---
    
    // 1. Biểu đồ Đường (Tổng Thu/Chi 6 tháng + 1 tháng AI Dự báo)
    const ctxTrend = document.getElementById('trendChart').getContext('2d');
    let gradTrend = ctxTrend.createLinearGradient(0, 0, 0, 250);
    gradTrend.addColorStop(0, 'rgba(16, 185, 129, 0.4)'); 
    gradTrend.addColorStop(1, 'rgba(16, 185, 129, 0)');
    
    new Chart(ctxTrend, {
        type: 'line',
        data: {
            labels: c1_labels,
            datasets: [
                { 
                    label: 'Thu vào (VNĐ)', 
                    data: c1_thu, 
                    borderColor: '#10b981', 
                    backgroundColor: gradTrend, 
                    borderWidth: 3, 
                    fill: true, 
                    tension: 0.4,
                    // Dùng segment để làm nét đứt mờ đoạn dự báo tương lai
                    segment: {
                        borderDash: ctx => ctx.p0DataIndex >= (c1_thu.length - 2) ? [6, 6] : undefined,
                        borderColor: ctx => ctx.p0DataIndex >= (c1_thu.length - 2) ? 'rgba(16, 185, 129, 0.5)' : '#10b981'
                    }
                },
                { 
                    label: 'Chi ra (VNĐ)', 
                    data: c1_chi, 
                    borderColor: '#ef4444', 
                    borderWidth: 2, 
                    fill: false, 
                    tension: 0.4,
                    // Dùng segment để làm nét đứt mờ đoạn dự báo tương lai
                    segment: {
                        borderDash: ctx => ctx.p0DataIndex >= (c1_chi.length - 2) ? [6, 6] : undefined,
                        borderColor: ctx => ctx.p0DataIndex >= (c1_chi.length - 2) ? 'rgba(239, 68, 68, 0.4)' : '#ef4444'
                    }
                }
            ]
        },
        options: { 
            responsive: true, 
            maintainAspectRatio: false, 
            plugins: { 
                legend: { position: 'top', align: 'end' },
                tooltip: {
                    callbacks: {
                        // Thêm icon Robot vào Tooltip cho tháng dự báo
                        title: function(context) {
                            let title = context[0].label;
                            if (context[0].dataIndex === c1_labels.length - 1) return title + " 🤖 (Dự báo)";
                            return title;
                        }
                    }
                }
            }, 
            scales: { x: { grid: { display: false } }, y: { grid: gridOptions } } 
        }
    });

    // 2. Biểu đồ Doughnut (Cơ cấu chi tiêu)
    new Chart(document.getElementById('expensePieChart').getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: c2_labels.length > 0 ? c2_labels : ['Chưa có dữ liệu'],
            datasets: [{ 
                data: c2_data.length > 0 ? c2_data : [1], 
                backgroundColor: ['#a855f7', '#3b82f6', '#f43f5e', '#f59e0b', '#10b981'], 
                borderWidth: 0, hoverOffset: 4 
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, cutout: '70%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } } }
    });

    // 3. Biểu đồ Bar Ngang (Top Đóng Góp)
    new Chart(document.getElementById('topMemberChart').getContext('2d'), {
        type: 'bar',
        data: {
            labels: c3_labels,
            datasets: [{ label: 'Tổng tiền đã đóng (VNĐ)', data: c3_data, backgroundColor: '#a855f7', borderRadius: 6 }]
        },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: gridOptions }, y: { grid: { display: false } } } }
    });

    // 4. Biểu đồ Stacked Bar (Tiến độ đợt thu)
    new Chart(document.getElementById('progressChart').getContext('2d'), {
        type: 'bar',
        data: {
            labels: c4_labels,
            datasets: [
                { label: 'Đã hoàn thành (VNĐ)', data: c4_dathu, backgroundColor: '#3b82f6', borderRadius: 4 },
                { label: 'Chưa đóng / Nợ (VNĐ)', data: c4_no, backgroundColor: '#e2e8f0', borderRadius: 4 }
            ]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top', align: 'end' } }, scales: { x: { stacked: true, grid: { display: false } }, y: { stacked: true, grid: gridOptions } } }
    });

    // 5. Biểu đồ Pie (Phân bổ ngân sách theo quỹ)
    new Chart(document.getElementById('fundDistributionChart').getContext('2d'), {
        type: 'pie',
        data: {
            labels: c5_labels.length > 0 ? c5_labels : ['Trống'],
            datasets: [{ 
                data: c5_data.length > 0 ? c5_data : [1], 
                backgroundColor: ['#10b981', '#f59e0b', '#0ea5e9', '#ec4899', '#8b5cf6'], 
                borderWidth: 0, hoverOffset: 4 
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { boxWidth: 12 } } } }
    });
});