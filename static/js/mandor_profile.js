let activityPage = 1;
const activityPerPage = 10;
let profileInitial = null;

function $(id) { return document.getElementById(id); }

function toggleSidebar() {
    $('sidebar').classList.toggle('collapsed');
    $('mainContent').classList.toggle('expanded');
}

function toggleMobileMenu() {
    $('sidebar').classList.toggle('open');
}

function setActiveMenuItem(element, menuId) {
    document.querySelectorAll('.menu-item').forEach((item) => item.classList.remove('active'));
    element.classList.add('active');
    sessionStorage.setItem('activeMenu', menuId);
}

async function confirmLogout(event) {
    if (event) event.preventDefault();
    const ok = confirm('Apakah Anda yakin ingin logout?');
    if (!ok) return false;
    try {
        await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
    } catch (_) {
        // Ignore and still redirect to login.
    }
    window.location.href = '/login';
    return false;
}

function switchTab(tab) {
    const tabs = document.querySelectorAll('.tab');
    const map = { personal: 'personalTab', security: 'securityTab', activity: 'activityTab' };
    tabs.forEach((t) => t.classList.remove('active'));
    Object.values(map).forEach((id) => { $(id).style.display = 'none'; });

    const idx = tab === 'personal' ? 0 : tab === 'security' ? 1 : 2;
    tabs[idx].classList.add('active');
    $(map[tab]).style.display = 'block';
}

function closeSuccessProfileModal() { $('successProfileModal').classList.remove('active'); }
function closeSuccessPasswordModal() { $('successPasswordModal').classList.remove('active'); }
function closeCancelModal() { $('cancelModal').classList.remove('active'); }
function closeLoadingModal() { $('loadingModal').classList.remove('active'); }
function closeWarningRequiredModal() { $('warningRequiredModal').classList.remove('active'); }
function closeWarningPasswordLengthModal() { $('warningPasswordLengthModal').classList.remove('active'); }
function closeWarningPasswordMatchModal() { $('warningPasswordMatchModal').classList.remove('active'); }

function openModal(id) { $(id).classList.add('active'); }

async function loadProfile() {
    const res = await fetch('/api/settings/profile', { credentials: 'same-origin' });
    const data = await res.json();
    if (!data.success) return;

    const u = data.data;
    profileInitial = {
        nama: u.nama || '',
        email: u.email || '',
        phone: u.phone || '',
        address: '',
    };

    $('fullName').value = profileInitial.nama;
    $('email').value = profileInitial.email;
    $('phone').value = profileInitial.phone;

    const initials = (u.nama || u.username || 'U').split(' ').map((x) => x[0]).join('').slice(0, 2).toUpperCase();
    document.querySelectorAll('.user-avatar, .profile-avatar-large').forEach((el) => { el.textContent = initials; });
    document.querySelectorAll('.user-name').forEach((el) => { el.textContent = u.nama || u.username || '-'; });
    const pName = document.querySelector('.profile-name');
    if (pName) pName.textContent = u.nama || u.username || '-';
    const pRole = document.querySelector('.profile-role');
    if (pRole) pRole.textContent = 'Mandor';

    const detailValues = document.querySelectorAll('.detail-group .detail-value');
    if (detailValues.length >= 6) {
        detailValues[0].textContent = u.nama || '-';
        detailValues[1].textContent = 'Mandor';
        detailValues[3].textContent = u.email || '-';
        detailValues[4].textContent = u.phone || '-';
    }
}

async function saveProfile() {
    const nama = $('fullName').value.trim();
    const email = $('email').value.trim();
    const phone = $('phone').value.trim();
    const address = $('address').value.trim();

    if (!nama || !email || !phone || !address) {
        openModal('warningRequiredModal');
        return;
    }

    const res = await fetch('/api/settings/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ nama, email, phone }),
    });
    const data = await res.json();
    if (!data.success) {
        alert(data.message || 'Gagal menyimpan profil.');
        return;
    }

    profileInitial = { nama, email, phone, address };
    openModal('successProfileModal');
}

function cancelEdit() { openModal('cancelModal'); }

function confirmCancel() {
    closeCancelModal();
    if (!profileInitial) return;
    $('fullName').value = profileInitial.nama;
    $('email').value = profileInitial.email;
    $('phone').value = profileInitial.phone;
    $('address').value = profileInitial.address;
}

async function changePassword() {
    const old_password = $('currentPassword').value;
    const new_password = $('newPassword').value;
    const confirm_password = $('confirmPassword').value;

    if (!old_password || !new_password || !confirm_password) {
        openModal('warningRequiredModal');
        return;
    }
    if (new_password.length < 8) {
        openModal('warningPasswordLengthModal');
        return;
    }
    if (new_password !== confirm_password) {
        openModal('warningPasswordMatchModal');
        return;
    }

    const res = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ old_password, new_password, confirm_password }),
    });
    const data = await res.json();
    if (!data.success) {
        alert(data.message || 'Gagal mengganti password.');
        return;
    }

    $('currentPassword').value = '';
    $('newPassword').value = '';
    $('confirmPassword').value = '';
    openModal('successPasswordModal');
}

function renderActivity(items, append = false) {
    const timeline = document.querySelector('.timeline');
    if (!timeline) return;

    const html = items.map((x) => `
    <div class="timeline-item">
      <div class="timeline-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <path d="M12 6v6l4 2"></path>
        </svg>
      </div>
      <div class="timeline-content">
        <div class="timeline-title">${x.aksi || '-'} - ${x.modul || '-'}</div>
        <div class="timeline-time">${new Date(x.created_at).toLocaleString('id-ID')}</div>
      </div>
    </div>
  `).join('');

    if (append) {
        timeline.insertAdjacentHTML('beforeend', html);
    } else {
        timeline.innerHTML = html || '<div class="timeline-item"><div class="timeline-content"><div class="timeline-title">Belum ada aktivitas.</div></div></div>';
    }
}

async function loadActivity(page = 1, append = false) {
    const res = await fetch(`/api/log/?page=${page}&per_page=${activityPerPage}`, { credentials: 'same-origin' });
    const data = await res.json();
    if (!data.success) return;
    renderActivity(data.data || [], append);
}

async function loadMoreActivity() {
    openModal('loadingModal');
    activityPage += 1;
    await loadActivity(activityPage, true);
    closeLoadingModal();
}

window.addEventListener('load', async () => {
    await loadProfile();
    await loadActivity(1, false);
});
