// ==================== DATA STORE ====================
let projectList = [];
let absenList = [];
let absenItems = [];
let currentPage = 1;
const itemsPerPage = 10;

// ==================== API FUNCTIONS ====================

async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        const result = await response.json();

        if (result.success) {
            projectList = result.data.filter(p => p.status === 'active');
            populateProjectSelects();
        }
    } catch (error) {
        console.error('Error loading projects:', error);
    }
}

function populateProjectSelects() {
    const selects = document.querySelectorAll('.project-select');
    selects.forEach(select => {
        select.innerHTML = '<option value="">-- Pilih Project --</option>';
        projectList.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = `${project.project_name}${project.customer_name ? ' - ' + project.customer_name : ''}`;
            select.appendChild(option);
        });
    });
}

async function loadAbsenList() {
    try {
        const params = new URLSearchParams();
        params.append('jenis', 'absen');

        // Add filters if any
        const projectId = document.getElementById('filterProject')?.value;
        const dari = document.getElementById('filterDari')?.value;
        const ke = document.getElementById('filterKe')?.value;

        if (projectId) params.append('project_id', projectId);
        if (dari) params.append('dari', dari);
        if (ke) params.append('ke', ke);

        const response = await fetch(`/api/supervisi/laporan?${params}`);
        const result = await response.json();

        if (result.success) {
            absenList = result.data;
            renderAbsenTable();
        }
    } catch (error) {
        console.error('Error loading absen:', error);
        showWarningModal('Gagal memuat data absen');
    }
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

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

function formatDateLong(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });
}

// ==================== MODAL FUNCTIONS ====================

function showWarningModal(message) {
    const modal = document.getElementById('warningModal');
    if (modal) {
        document.getElementById('warningMessage').textContent = message;
        modal.classList.add('active');
    } else {
        alert(message);
    }
}

function closeWarningModal() {
    const modal = document.getElementById('warningModal');
    if (modal) modal.classList.remove('active');
}

function showSuccessModal(message) {
    const modal = document.getElementById('successModal');
    if (modal) {
        document.getElementById('successMessage').textContent = message;
        modal.classList.add('active');
    } else {
        alert(message);
    }
}

function closeSuccessModal() {
    const modal = document.getElementById('successModal');
    if (modal) modal.classList.remove('active');
}

function closeDetailModal() {
    const modal = document.getElementById('detailModal');
    if (modal) modal.classList.remove('active');
}

// ==================== TAB FUNCTIONS ====================

function switchTab(tab) {
    const tabs = document.querySelectorAll('.tab');
    const createTab = document.getElementById('createTab');
    const historyTab = document.getElementById('historyTab');

    tabs.forEach(t => t.classList.remove('active'));

    if (tab === 'create') {
        tabs[0].classList.add('active');
        createTab.style.display = 'block';
        historyTab.style.display = 'none';
        resetForm();
    } else {
        tabs[1].classList.add('active');
        createTab.style.display = 'none';
        historyTab.style.display = 'block';
        loadAbsenList();
    }
}

// ==================== ABSEN ITEM MANAGEMENT ====================

function addAbsenItem() {
    const kategori = document.getElementById('itemKategori')?.value;
    const label = document.getElementById('itemLabel')?.value;
    const nilai = document.getElementById('itemNilai')?.value;
    const satuan = document.getElementById('itemSatuan')?.value;

    if (!kategori) {
        showWarningModal('Pilih kategori item!');
        return;
    }

    if (!label || label.trim() === '') {
        showWarningModal('Isi label/nama item!');
        return;
    }

    const item = {
        kategori: kategori,
        label: label.trim(),
        nilai: nilai || null,
        satuan: satuan || null
    };

    absenItems.push(item);
    renderItemsTable();
    clearItemForm();
}

function removeItem(index) {
    absenItems.splice(index, 1);
    renderItemsTable();
}

function clearItemForm() {
    if (document.getElementById('itemKategori')) document.getElementById('itemKategori').value = '';
    if (document.getElementById('itemLabel')) document.getElementById('itemLabel').value = '';
    if (document.getElementById('itemNilai')) document.getElementById('itemNilai').value = '';
    if (document.getElementById('itemSatuan')) document.getElementById('itemSatuan').value = '';
}

function renderItemsTable() {
    const tbody = document.getElementById('itemsTableBody');
    if (!tbody) return;

    if (absenItems.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 30px; color: #999;">
                    Belum ada item. Klik tombol "Tambah Item" untuk menambahkan.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = '';

    absenItems.forEach((item, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${item.kategori}</td>
            <td>${item.label}</td>
            <td>${item.nilai || ''} ${item.satuan || ''}</td>
            <td>
                <button class="btn-icon btn-danger" onclick="removeItem(${index})" title="Hapus">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// ==================== FORM SUBMIT ====================

async function submitAbsen() {
    const projectSelect = document.getElementById('projectSelect');
    const tanggal = document.getElementById('tanggalAbsen')?.value;
    const segmen = document.getElementById('segmen')?.value;
    const waktuLapor = document.getElementById('waktuLapor')?.value;
    const deskripsi = document.getElementById('deskripsi')?.value;

    // Validation
    if (!projectSelect || !projectSelect.value) {
        showWarningModal('Pilih project terlebih dahulu!');
        return;
    }

    if (!tanggal) {
        showWarningModal('Pilih tanggal absen!');
        return;
    }

    try {
        // Prepare items for API - convert to SupervisiLaporanItem format
        const items = absenItems.map(item => ({
            segmen: item.kategori,  // Use kategori as segmen for absen
            kategori: item.kategori,
            nama_item: item.label,
            nilai: item.nilai ? parseFloat(item.nilai) : null,
            satuan: item.satuan
        }));

        const data = {
            jenis: 'absen',
            tanggal: tanggal,
            project_id: parseInt(projectSelect.value),
            project_name: projectSelect.selectedOptions[0].text,
            lokasi: segmen || null,  // Use segmen as lokasi
            waktu_lapor: waktuLapor || null,
            judul: `ABSEN ${projectSelect.selectedOptions[0].text}`,
            catatan: deskripsi || null,
            items: items
        };

        const response = await fetch('/api/supervisi/laporan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showSuccessModal('Absen berhasil disimpan!');
            resetForm();
            absenItems = [];
            renderItemsTable();
        } else {
            showWarningModal(result.message || 'Gagal menyimpan absen');
        }
    } catch (error) {
        console.error('Error submitting absen:', error);
        showWarningModal('Terjadi kesalahan saat menyimpan absen');
    }
}

function resetForm() {
    if (document.getElementById('projectSelect')) document.getElementById('projectSelect').value = '';
    if (document.getElementById('segmen')) document.getElementById('segmen').value = '';
    if (document.getElementById('waktuLapor')) document.getElementById('waktuLapor').value = '';
    if (document.getElementById('deskripsi')) document.getElementById('deskripsi').value = '';

    absenItems = [];
    renderItemsTable();
    clearItemForm();

    // Reset tanggal to today
    const today = new Date().toISOString().split('T')[0];
    if (document.getElementById('tanggalAbsen')) document.getElementById('tanggalAbsen').value = today;
}

// ==================== ABSEN LIST ====================

function renderAbsenTable() {
    const tbody = document.getElementById('absenTableBody');
    if (!tbody) return;

    if (absenList.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 50px; color: #999;">
                    <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M12 6v6l4 2"></path>
                    </svg>
                    <p>Belum ada riwayat absen</p>
                </td>
            </tr>
        `;
        return;
    }

    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const paginatedData = absenList.slice(start, end);

    tbody.innerHTML = '';

    paginatedData.forEach((absen, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${start + index + 1}</td>
            <td>${formatDate(absen.tanggal)}</td>
            <td>${absen.project_name || '-'}</td>
            <td>${absen.lokasi || '-'}</td>
            <td>${absen.waktu_lapor || '-'}</td>
            <td>
                <button class="action-btn view" onclick="viewAbsenDetail(${absen.id})">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="2"></circle>
                        <path d="M22 12c-2.667 4.667-6 7-10 7s-7.333-2.333-10-7c2.667-4.667 6-7 10-7s7.333 2.333 10 7z"></path>
                    </svg>
                    Detail
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });

    updatePaginationInfo();
}

function updatePaginationInfo() {
    const info = document.getElementById('paginationInfo');
    if (!info) return;

    const totalItems = absenList.length;
    const start = totalItems > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0;
    const end = Math.min(currentPage * itemsPerPage, totalItems);

    info.textContent = `Menampilkan ${start} - ${end} dari ${totalItems} data`;

    // Update pagination buttons
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');

    if (prevBtn) prevBtn.disabled = currentPage === 1;
    if (nextBtn) nextBtn.disabled = currentPage === totalPages || totalItems === 0;
}

function changePage(direction) {
    const totalPages = Math.ceil(absenList.length / itemsPerPage);

    if (direction === 'prev' && currentPage > 1) {
        currentPage--;
    } else if (direction === 'next' && currentPage < totalPages) {
        currentPage++;
    }

    renderAbsenTable();
}

function applyFilter() {
    currentPage = 1;
    loadAbsenList();
}

// ==================== ABSEN DETAIL ====================

async function viewAbsenDetail(id) {
    try {
        const response = await fetch(`/api/supervisi/laporan/${id}`);
        const result = await response.json();

        if (result.success) {
            const absen = result.data;

            const modalBody = document.getElementById('detailModalBody');
            if (!modalBody) return;

            let html = `
                <div style="background: #f8f9fa; border-radius: 12px; padding: 20px;">
                    <div style="margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e8e8e8;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 12px; color: #666; margin-bottom: 4px;">Tanggal</div>
                                <div style="font-size: 16px; font-weight: 600;">${formatDateLong(absen.tanggal)}</div>
                            </div>
                            ${absen.waktu_lapor ? `
                                <div style="background: var(--primary-color); color: white; padding: 6px 12px; border-radius: 20px; font-size: 13px;">
                                    ${absen.waktu_lapor}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e8e8e8;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 4px;">Project</div>
                        <div style="font-size: 15px; font-weight: 600;">${absen.project_name || '-'}</div>
                    </div>
                    
                    ${absen.lokasi ? `
                    <div style="margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e8e8e8;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 4px;">Segmen</div>
                        <div style="font-size: 15px; font-weight: 600;">${absen.lokasi}</div>
                    </div>
                    ` : ''}
                    
                    ${absen.catatan ? `
                    <div style="margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e8e8e8;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 4px;">Keterangan</div>
                        <div style="font-size: 14px; color: #333;">${absen.catatan}</div>
                    </div>
                    ` : ''}
                    
                    ${absen.items && absen.items.length > 0 ? `
                    <div style="margin-top: 20px;">
                        <div style="font-weight: 700; margin-bottom: 12px; color: #333;">Detail Absen (${absen.items.length}):</div>
                        <div style="max-height: 300px; overflow-y: auto;">
                            ${absen.items.map((item, idx) => `
                                <div style="background: white; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid var(--primary-color);">
                                    <div style="font-weight: 600; color: #333; margin-bottom: 4px;">${idx + 1}. ${item.nama_item}</div>
                                    <div style="font-size: 12px; color: #666;">
                                        Kategori: ${item.kategori}
                                        ${item.nilai !== null ? ` | ${item.nilai} ${item.satuan || ''}` : ''}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}
                    
                    ${absen.foto && absen.foto.length > 0 ? `
                    <div style="margin-top: 20px;">
                        <div style="font-weight: 700; margin-bottom: 12px; color: #333;">Foto (${absen.foto.length}):</div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 10px;">
                            ${absen.foto.map(foto => `
                                <div style="aspect-ratio: 1; border-radius: 8px; overflow: hidden; cursor: pointer;">
                                    <img src="${foto.url}" alt="" style="width: 100%; height: 100%; object-fit: cover;">
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}
                </div>
            `;

            modalBody.innerHTML = html;
            document.getElementById('detailModal').classList.add('active');
        }
    } catch (error) {
        console.error('Error loading absen detail:', error);
        showWarningModal('Gagal memuat detail absen');
    }
}

// ==================== INITIALIZE ====================

window.onload = async function () {
    await loadProjects();

    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    if (document.getElementById('tanggalAbsen')) {
        document.getElementById('tanggalAbsen').value = today;
    }

    // Initialize items table
    renderItemsTable();

    // Load list if in history tab
    if (document.getElementById('historyTab')?.style.display === 'block') {
        await loadAbsenList();
    }
};
