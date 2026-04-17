// ==================== DATA STORE ====================
let projectList = [];
let galleryData = [];
let selectedFiles = [];
let currentPage = 1;
const itemsPerPage = 12;

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
    // Populate upload project select
    const uploadSelect = document.getElementById('projectSelect');
    if (uploadSelect) {
        uploadSelect.innerHTML = '<option value="">-- Pilih Project --</option>';
        projectList.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = `${project.project_name}${project.customer_name ? ' - ' + project.customer_name : ''}`;
            uploadSelect.appendChild(option);
        });
    }

    // Populate filter project select
    const filterSelect = document.getElementById('filterProject');
    if (filterSelect) {
        filterSelect.innerHTML = '<option value="">Semua Project</option>';
        projectList.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = `${project.project_name}`;
            filterSelect.appendChild(option);
        });
    }
}

async function loadGallery() {
    try {
        const params = new URLSearchParams();

        const projectId = document.getElementById('filterProject')?.value;
        const tanggal = document.getElementById('filterTanggal')?.value;

        if (projectId) params.append('project_id', projectId);
        if (tanggal) params.append('tanggal', tanggal);

        const response = await fetch(`/api/supervisi/evidence?${params}`);
        const result = await response.json();

        if (result.success) {
            galleryData = result.data;
            renderGallery();
        }
    } catch (error) {
        console.error('Error loading gallery:', error);
        showWarningModal('Gagal memuat galeri foto');
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

function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('id-ID', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
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

function closePreviewModal() {
    const modal = document.getElementById('previewModal');
    if (modal) modal.classList.remove('active');
}

function showPreviewModal(imageUrl, caption, projectName, tanggal) {
    const modal = document.getElementById('previewModal');
    if (!modal) return;

    const img = document.getElementById('previewImage');
    const captionEl = document.getElementById('previewCaption');
    const projectEl = document.getElementById('previewProject');
    const dateEl = document.getElementById('previewDate');

    if (img) img.src = imageUrl;
    if (captionEl) captionEl.textContent = caption || 'Tidak ada caption';
    if (projectEl) projectEl.textContent = projectName || '-';
    if (dateEl) dateEl.textContent = formatDate(tanggal);

    modal.classList.add('active');
}

// ==================== TAB FUNCTIONS ====================

function switchTab(tab) {
    const tabs = document.querySelectorAll('.tab');
    const uploadTab = document.getElementById('uploadTab');
    const galleryTab = document.getElementById('galleryTab');

    tabs.forEach(t => t.classList.remove('active'));

    if (tab === 'upload') {
        tabs[0].classList.add('active');
        uploadTab.style.display = 'block';
        galleryTab.style.display = 'none';
    } else {
        tabs[1].classList.add('active');
        uploadTab.style.display = 'none';
        galleryTab.style.display = 'block';
        loadGallery();
    }
}

// ==================== FILE UPLOAD FUNCTIONS ====================

function triggerFileInput() {
    document.getElementById('fileInput').click();
}

function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    addFiles(files);
}

function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) uploadArea.classList.add('drag-over');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) uploadArea.classList.remove('drag-over');
}

function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();

    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) uploadArea.classList.remove('drag-over');

    const files = Array.from(event.dataTransfer.files);
    const imageFiles = files.filter(f => f.type.startsWith('image/'));

    if (imageFiles.length < files.length) {
        showWarningModal('Hanya file gambar yang diperbolehkan!');
    }

    addFiles(imageFiles);
}

function addFiles(files) {
    const validFiles = files.filter(f => {
        const isImage = f.type.startsWith('image/');
        const isValidSize = f.size <= 5 * 1024 * 1024; // 5MB

        if (!isImage) {
            showWarningModal(`${f.name} bukan file gambar!`);
            return false;
        }

        if (!isValidSize) {
            showWarningModal(`${f.name} terlalu besar! Maksimal 5MB`);
            return false;
        }

        return true;
    });

    selectedFiles.push(...validFiles);
    displaySelectedFiles();

    // Hide upload area, show preview area
    const uploadArea = document.getElementById('uploadArea');
    const previewArea = document.getElementById('previewArea');

    if (selectedFiles.length > 0) {
        if (uploadArea) uploadArea.style.display = 'none';
        if (previewArea) previewArea.style.display = 'block';
    }
}

function displaySelectedFiles() {
    const container = document.getElementById('selectedFilesContainer');
    if (!container) return;

    container.innerHTML = '';

    selectedFiles.forEach((file, index) => {
        const reader = new FileReader();

        reader.onload = function (e) {
            const fileCard = document.createElement('div');
            fileCard.className = 'file-preview-card';
            fileCard.innerHTML = `
                <img src="${e.target.result}" alt="${file.name}">
                <button class="remove-file-btn" onclick="removeFile(${index})" type="button">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${(file.size / 1024).toFixed(1)} KB</div>
                </div>
            `;
            container.appendChild(fileCard);
        };

        reader.readAsDataURL(file);
    });

    // Update counter
    const counter = document.getElementById('fileCounter');
    if (counter) {
        counter.textContent = `${selectedFiles.length} foto dipilih`;
    }
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    displaySelectedFiles();

    // If no files left, show upload area again
    if (selectedFiles.length === 0) {
        const uploadArea = document.getElementById('uploadArea');
        const previewArea = document.getElementById('previewArea');

        if (uploadArea) uploadArea.style.display = 'flex';
        if (previewArea) previewArea.style.display = 'none';
    }
}

function clearAllFiles() {
    selectedFiles = [];
    displaySelectedFiles();

    const uploadArea = document.getElementById('uploadArea');
    const previewArea = document.getElementById('previewArea');

    if (uploadArea) uploadArea.style.display = 'flex';
    if (previewArea) previewArea.style.display = 'none';

    // Reset file input
    const fileInput = document.getElementById('fileInput');
    if (fileInput) fileInput.value = '';
}

// ==================== UPLOAD FUNCTION ====================

async function uploadPhotos() {
    if (selectedFiles.length === 0) {
        showWarningModal('Pilih foto terlebih dahulu!');
        return;
    }

    const projectSelect = document.getElementById('projectSelect');
    const tanggal = document.getElementById('tanggalFoto')?.value;
    const caption = document.getElementById('caption')?.value;

    if (!projectSelect.value) {
        showWarningModal('Pilih project terlebih dahulu!');
        return;
    }

    if (!tanggal) {
        showWarningModal('Pilih tanggal terlebih dahulu!');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('project_id', projectSelect.value);
        formData.append('project_name', projectSelect.selectedOptions[0].text);
        formData.append('tanggal', tanggal);
        formData.append('jenis', 'absen');  // bisa diganti sesuai kebutuhan

        if (caption) {
            formData.append('caption', caption);
        }

        // Append all files
        selectedFiles.forEach(file => {
            formData.append('foto', file);
        });

        const response = await fetch('/api/supervisi/evidence', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            showSuccessModal(`${selectedFiles.length} foto berhasil diupload!`);
            clearAllFiles();

            // Clear form
            if (projectSelect) projectSelect.value = '';
            if (document.getElementById('caption')) document.getElementById('caption').value = '';

            // Reload gallery if in gallery tab
            if (document.getElementById('galleryTab')?.style.display === 'block') {
                await loadGallery();
            }
        } else {
            showWarningModal(result.message || 'Gagal upload foto');
        }
    } catch (error) {
        console.error('Error uploading photos:', error);
        showWarningModal('Terjadi kesalahan saat upload foto');
    }
}

// ==================== GALLERY FUNCTIONS ====================

function renderGallery() {
    const container = document.getElementById('galleryContainer');
    if (!container) return;

    if (galleryData.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: #999;">
                <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <circle cx="8.5" cy="8.5" r="1.5"></circle>
                    <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
                <p style="margin-top: 20px; font-size: 16px;">Belum ada foto</p>
            </div>
        `;
        return;
    }

    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const paginatedData = galleryData.slice(start, end);

    container.innerHTML = '';

    paginatedData.forEach(item => {
        const card = document.createElement('div');
        card.className = 'gallery-item';
        card.innerHTML = `
            <div class="gallery-image" onclick="showPreviewModal('${item.url}', '${item.caption || ''}', '${item.project_name || ''}', '${item.tanggal || ''}')">
                <img src="${item.url}" alt="${item.caption || 'Evidence'}" loading="lazy">
            </div>
            <div class="gallery-info">
                <div class="gallery-project">${item.project_name || '-'}</div>
                <div class="gallery-date">${formatDate(item.tanggal)}</div>
                ${item.caption ? `<div class="gallery-caption">${item.caption}</div>` : ''}
            </div>
        `;
        container.appendChild(card);
    });

    updatePaginationInfo();
}

function updatePaginationInfo() {
    const info = document.getElementById('galleryPaginationInfo');
    if (!info) return;

    const totalItems = galleryData.length;
    const start = totalItems > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0;
    const end = Math.min(currentPage * itemsPerPage, totalItems);

    info.textContent = `Menampilkan ${start} - ${end} dari ${totalItems} foto`;

    // Update pagination buttons
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    if (prevBtn) prevBtn.disabled = currentPage === 1;
    if (nextBtn) nextBtn.disabled = currentPage === totalPages || totalItems === 0;
}

function changePage(direction) {
    const totalPages = Math.ceil(galleryData.length / itemsPerPage);

    if (direction === 'prev' && currentPage > 1) {
        currentPage--;
    } else if (direction === 'next' && currentPage < totalPages) {
        currentPage++;
    }

    renderGallery();
}

function applyFilter() {
    currentPage = 1;
    loadGallery();
}

async function downloadAllPhotos() {
    if (galleryData.length === 0) {
        showWarningModal('Tidak ada foto untuk didownload!');
        return;
    }

    showWarningModal('Fitur download masih dalam pengembangan. Silakan download foto satu per satu dengan klik kanan pada gambar.');
}

// ==================== INITIALIZE ====================

window.onload = async function () {
    await loadProjects();

    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    const tanggalFoto = document.getElementById('tanggalFoto');
    if (tanggalFoto) tanggalFoto.value = today;

    // Setup file input
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }

    // Load gallery if in gallery tab
    if (document.getElementById('galleryTab')?.style.display === 'block') {
        await loadGallery();
    }
};
