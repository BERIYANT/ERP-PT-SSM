// ==================== DATA STORE ====================
let kasbonList = [];
let projectList = [];
let currentPage = 1;
const itemsPerPage = 5;
let filteredKasbon = [];
let currentCancelId = null; let currentUser = null;

// ==================== API FUNCTIONS ====================

async function loadKasbonData() {
    try {
        const response = await fetch('/api/kasbon');
        const result = await response.json();

        if (result.success) {
            kasbonList = result.data;
            filteredKasbon = [...kasbonList];
            renderKasbonTable();
            renderPagination();
        } else {
            console.error('Failed to load kasbon data:', result.message);
        }
    } catch (error) {
        console.error('Error loading kasbon data:', error);
        showWarningModal('Gagal memuat data kasbon');
    }
}

async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        const result = await response.json();

        if (result.success) {
            projectList = result.data.filter(p => p.status === 'active');
            populateProjectSelect();
        }
    } catch (error) {
        console.error('Error loading projects:', error);
    }
}

async function loadSummary() {
    try {
        const response = await fetch('/api/kasbon/summary');
        const result = await response.json();

        if (result.success) {
            document.getElementById('totalPending').textContent = result.data.counts.pending;
            document.getElementById('totalApproved').textContent = result.data.counts.approved;
            document.getElementById('totalRejected').textContent = result.data.counts.rejected;
        }
    } catch (error) {
        console.error('Error loading summary:', error);
    }
}

function populateProjectSelect() {
    const select = document.getElementById('projectSelect');
    select.innerHTML = '<option value="">-- Pilih Project --</option>';

    projectList.forEach(project => {
        const option = document.createElement('option');
        option.value = project.id;
        option.textContent = `${project.project_name}${project.customer_name ? ' - ' + project.customer_name : ''}`;
        select.appendChild(option);
    });
}

// ==================== UTILITY FUNCTIONS ====================

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    sidebar.classList.toggle('collapsed');
    mainContent.classList.toggle('expanded');
}

function toggleMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

function confirmLogout(event) {
    if (!confirm('Apakah Anda yakin ingin logout?')) {
        event.preventDefault();
        return false;
    }
    window.location.href = '/api/auth/logout';
    return false;
}

// Format Rupiah
function formatRupiah(amount) {
    return 'Rp ' + parseFloat(amount).toLocaleString('id-ID');
}

// Format Date
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Format Date Long
function formatDateLong(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });
}

// Get Status Badge Class
function getStatusBadgeClass(status) {
    switch (status) {
        case 'pending': return 'status-badge pending';
        case 'approved': return 'status-badge approved';
        case 'rejected': return 'status-badge rejected';
        default: return 'status-badge';
    }
}

// Get Status Text
function getStatusText(status) {
    switch (status) {
        case 'pending': return 'Pending';
        case 'approved': return 'Disetujui';
        case 'rejected': return 'Ditolak';
        default: return status;
    }
}

// ==================== MODAL FUNCTIONS ====================

function showWarningModal(message) {
    document.getElementById('warningMessage').textContent = message;
    document.getElementById('warningModal').classList.add('active');
}

function closeWarningModal() {
    document.getElementById('warningModal').classList.remove('active');
}

function closeSuccessModal() {
    document.getElementById('successModal').classList.remove('active');
}

function closeDetailModal() {
    document.getElementById('detailModal').classList.remove('active');
}

function closeCancelModal() {
    document.getElementById('cancelModal').classList.remove('active');
    currentCancelId = null;
}

// ==================== TAB FUNCTIONS ====================

function switchTab(tab) {
    const tabs = document.querySelectorAll('.tab');
    const requestTab = document.getElementById('requestTab');
    const historyTab = document.getElementById('historyTab');

    tabs.forEach(t => t.classList.remove('active'));

    if (tab === 'request') {
        tabs[0].classList.add('active');
        requestTab.style.display = 'block';
        historyTab.style.display = 'none';
    } else {
        tabs[1].classList.add('active');
        requestTab.style.display = 'none';
        historyTab.style.display = 'block';
        loadKasbonData();
        loadSummary();
    }
}

// ==================== KASBON FUNCTIONS ====================

// Submit Kasbon
async function submitKasbon() {
    const project = document.getElementById('projectSelect').value;
    const jumlah = document.getElementById('jumlahKasbon').value;
    const tanggal = document.getElementById('tanggalDibutuhkan').value;
    const keperluan = document.getElementById('keperluan').value;

    if (!project) {
        showWarningModal('Pilih project terlebih dahulu!');
        return;
    }

    if (!jumlah || jumlah < 10000) {
        showWarningModal('Jumlah kasbon minimal Rp 10.000!');
        return;
    }

    if (!tanggal) {
        showWarningModal('Pilih tanggal dibutuhkan!');
        return;
    }

    if (!keperluan || keperluan.trim() === '') {
        showWarningModal('Isi keperluan kasbon!');
        return;
    }

    try {
        const response = await fetch('/api/kasbon', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_id: parseInt(project),
                jumlah: parseFloat(jumlah),
                tanggal_pengajuan: tanggal,
                keperluan: keperluan.trim()
            })
        });

        const result = await response.json();

        if (result.success) {
            // Reset form
            resetForm();

            // Reload data
            await loadKasbonData();
            await loadSummary();

            // Update success message
            document.getElementById('successMessage').textContent = 'Kasbon berhasil diajukan!';
            document.getElementById('successKasbonNumber').textContent = `K-${result.data.id.toString().padStart(4, '0')}`;
            document.getElementById('successModal').classList.add('active');
        } else {
            showWarningModal(result.message || 'Gagal mengajukan kasbon');
        }
    } catch (error) {
        console.error('Error submitting kasbon:', error);
        showWarningModal('Terjadi kesalahan saat mengajukan kasbon');
    }
}

// Reset Form
function resetForm() {
    document.getElementById('projectSelect').value = '';
    document.getElementById('jumlahKasbon').value = '';
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('tanggalDibutuhkan').value = today;
    document.getElementById('keperluan').value = '';
}

// Lihat Detail Kasbon
function viewDetail(id) {
    const kasbon = kasbonList.find(k => k.id === id);
    if (!kasbon) return;

    const statusClass = getStatusBadgeClass(kasbon.status);
    const statusText = getStatusText(kasbon.status);
    const kasbonNumber = `K-${kasbon.id.toString().padStart(4, '0')}`;

    const modalBody = document.getElementById('detailModalBody');

    let html = `
        <div style="background: #f8f9fa; border-radius: 12px; padding: 20px;">
            <div style="display: flex; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e8e8e8;">
                <div style="width: 120px; font-size: 14px; color: #666;">No. Kasbon</div>
                <div style="flex: 1; font-size: 18px; font-weight: 700; color: var(--primary-color);">${kasbonNumber}</div>
            </div>
            <div style="display: flex; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e8e8e8;">
                <div style="width: 120px; font-size: 14px; color: #666;">Tanggal</div>
                <div style="flex: 1; font-size: 15px; font-weight: 600; color: #333;">${formatDateLong(kasbon.tanggal_pengajuan)}</div>
            </div>
            <div style="display: flex; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e8e8e8;">
                <div style="width: 120px; font-size: 14px; color: #666;">Project</div>
                <div style="flex: 1; font-size: 15px; font-weight: 600; color: #333;">${kasbon.project_name || '-'}</div>
            </div>
            <div style="display: flex; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e8e8e8;">
                <div style="width: 120px; font-size: 14px; color: #666;">Keperluan</div>
                <div style="flex: 1; font-size: 15px; font-weight: 600; color: #333;">${kasbon.keperluan}</div>
            </div>
            <div style="display: flex; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e8e8e8;">
                <div style="width: 120px; font-size: 14px; color: #666;">Jumlah</div>
                <div style="flex: 1; font-size: 18px; font-weight: 700; color: var(--primary-color);">${formatRupiah(kasbon.jumlah)}</div>
            </div>
            <div style="display: flex;">
                <div style="width: 120px; font-size: 14px; color: #666;">Status</div>
                <div style="flex: 1;"><span class="${statusClass}">${statusText}</span></div>
            </div>
    `;

    if (kasbon.rejection_reason) {
        html += `
            <div style="margin-top: 20px; padding: 15px; background: #fff1f0; border-radius: 8px;">
                <div style="color: #e74c3c; margin-bottom: 5px; font-weight: 600;">Alasan Ditolak:</div>
                <div style="color: #666;">${kasbon.rejection_reason}</div>
            </div>
        `;
    }

    if (kasbon.tanggal_verifikasi) {
        html += `
            <div style="margin-top: 15px; padding: 12px; background: #f0f9fb; border-radius: 8px;">
                <span style="color: #666;">Tanggal Verifikasi:</span>
                <span style="font-weight: 600; color: #333; margin-left: 5px;">${formatDate(kasbon.tanggal_verifikasi)}</span>
            </div>
        `;
    }

    html += '</div>';
    modalBody.innerHTML = html;

    document.getElementById('detailModal').classList.add('active');
}

// Batalkan Kasbon (hanya yang status pending)
function cancelKasbon(id) {
    const kasbon = kasbonList.find(k => k.id === id);
    if (!kasbon) return;

    if (kasbon.status !== 'pending') {
        showWarningModal('Hanya kasbon dengan status Pending yang dapat dibatalkan!');
        return;
    }

    currentCancelId = id;
    document.getElementById('cancelProject').textContent = kasbon.project_name || '-';
    document.getElementById('cancelAmount').textContent = formatRupiah(kasbon.jumlah);
    document.getElementById('cancelModal').classList.add('active');
}

async function confirmCancelKasbon() {
    if (!currentCancelId) return;

    try {
        const response = await fetch(`/api/kasbon/${currentCancelId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            closeCancelModal();

            // Reload data
            await loadKasbonData();
            await loadSummary();

            // Tampilkan modal sukses untuk pembatalan
            document.getElementById('successMessage').textContent = 'Kasbon berhasil dibatalkan!';
            document.getElementById('successKasbonNumber').textContent = '-';
            document.getElementById('successModal').classList.add('active');
        } else {
            showWarningModal(result.message || 'Gagal membatalkan kasbon');
        }
    } catch (error) {
        console.error('Error canceling kasbon:', error);
        showWarningModal('Terjadi kesalahan saat membatalkan kasbon');
    }
}

// ==================== TABLE RENDERING ====================

function renderKasbonTable() {
    const tbody = document.getElementById('kasbonTableBody');
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const paginatedKasbon = filteredKasbon.slice(start, end);

    if (paginatedKasbon.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 50px; color: #999;">
                    <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M12 6v6l4 2"></path>
                    </svg>
                    <p>Belum ada riwayat kasbon</p>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    paginatedKasbon.forEach((kasbon, index) => {
        const statusClass = getStatusBadgeClass(kasbon.status);
        const statusText = getStatusText(kasbon.status);
        const rowNumber = start + index + 1;

        html += `
            <tr>
                <td>${rowNumber}</td>
                <td>${formatDate(kasbon.tanggal_pengajuan)}</td>
                <td>${kasbon.project_name || '-'}</td>
                <td>${kasbon.keperluan.substring(0, 30)}${kasbon.keperluan.length > 30 ? '...' : ''}</td>
                <td class="amount">${formatRupiah(kasbon.jumlah)}</td>
                <td><span class="${statusClass}">${statusText}</span></td>
                <td>
                    <button class="action-btn view" onclick="viewDetail(${kasbon.id})">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="2"></circle>
                            <path d="M22 12c-2.667 4.667-6 7-10 7s-7.333-2.333-10-7c2.667-4.667 6-7 10-7s7.333 2.333 10 7z"></path>
                        </svg>
                        Detail
                    </button>
                    ${kasbon.status === 'pending' ? `
                    <button class="action-btn cancel" onclick="cancelKasbon(${kasbon.id})">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                        Batalkan
                    </button>
                    ` : ''}
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;

    // Update pagination info
    const startItem = filteredKasbon.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0;
    const endItem = Math.min(currentPage * itemsPerPage, filteredKasbon.length);
    document.getElementById('paginationInfo').textContent =
        filteredKasbon.length > 0
            ? `Menampilkan ${startItem} - ${endItem} dari ${filteredKasbon.length} data`
            : 'Menampilkan 0 data';
}

// ==================== PAGINATION ====================

function renderPagination() {
    const totalPages = Math.ceil(filteredKasbon.length / itemsPerPage);
    const paginationControls = document.getElementById('paginationControls');

    // Clear existing page buttons (keep prev and next)
    while (paginationControls.children.length > 2) {
        paginationControls.removeChild(paginationControls.children[1]);
    }

    // Add page buttons
    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement('button');
        btn.className = `pagination-btn ${currentPage === i ? 'active' : ''}`;
        btn.id = `page${i}`;
        btn.textContent = i;
        btn.onclick = () => goToPage(i);

        // Insert before next button
        paginationControls.insertBefore(btn, document.getElementById('nextPage'));
    }

    // Update prev/next buttons
    document.getElementById('prevPage').disabled = currentPage === 1 || filteredKasbon.length === 0;
    document.getElementById('nextPage').disabled = currentPage === totalPages || filteredKasbon.length === 0;
}

function changePage(direction) {
    const totalPages = Math.ceil(filteredKasbon.length / itemsPerPage);
    if (direction === 'prev' && currentPage > 1) {
        currentPage--;
    } else if (direction === 'next' && currentPage < totalPages) {
        currentPage++;
    }
    renderKasbonTable();
    renderPagination();
}

function goToPage(page) {
    currentPage = page;
    renderKasbonTable();
    renderPagination();
}

// Initialize
window.onload = async function () {
    await loadProjects();
    await loadKasbonData();
    await loadSummary();

    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('tanggalDibutuhkan').value = today;
};
