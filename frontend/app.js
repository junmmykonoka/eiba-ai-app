// KeibaAI Frontend Application Logic
let currentRaceId = null;
let currentRaceData = null;
let currentSortMode = 'horse_number';

// Schedule modal state
let currentScheduleData = null;
let currentVenueIndex = 0;

const API_BASE = '/api';

// DOM Elements
const raceListEl = document.getElementById('raceList');
const refreshRacesBtn = document.getElementById('refreshRacesBtn');
const scrapeInput = document.getElementById('scrapeInput');
const scrapeBtn = document.getElementById('scrapeBtn');
const reseedBtn = document.getElementById('reseedBtn');
const deleteRaceBtn = document.getElementById('deleteRaceBtn');
const runAiPredictBtn = document.getElementById('runAiPredictBtn');
const entriesBody = document.getElementById('entriesBody');
const tabBtns = document.querySelectorAll('.tab-btn');
const toastEl = document.getElementById('toast');

// Header Elements
const raceNameEl = document.getElementById('raceName');
const raceNumBadge = document.getElementById('raceNumBadge');
const raceDateEl = document.getElementById('raceDate');
const raceCourseEl = document.getElementById('raceCourse');
const raceClassEl = document.getElementById('raceClass');
const raceStartTimeEl = document.getElementById('raceStartTime');
const raceTrackDistEl = document.getElementById('raceTrackDist');
const raceConditionEl = document.getElementById('raceCondition');
const raceEntryCountEl = document.getElementById('raceEntryCount');

// AI Summary Banner Elements
const aiSummaryBanner = document.getElementById('aiSummaryBanner');
const pickHonmeiHorse = document.getElementById('pickHonmeiHorse');
const pickHonmeiMeta = document.getElementById('pickHonmeiMeta');
const pickTaikouHorse = document.getElementById('pickTaikouHorse');
const pickTaikouMeta = document.getElementById('pickTaikouMeta');
const pickAnaHorse = document.getElementById('pickAnaHorse');
const pickAnaMeta = document.getElementById('pickAnaMeta');

// Modal Elements
const scheduleModal = document.getElementById('scheduleModal');
const openScheduleModalBtn = document.getElementById('openScheduleModalBtn');
const closeScheduleModalBtn = document.getElementById('closeScheduleModalBtn');
const scheduleDateInput = document.getElementById('scheduleDateInput');
const fetchScheduleBtn = document.getElementById('fetchScheduleBtn');
const quickDateChips = document.querySelectorAll('.chip-btn');
const scheduleLoading = document.getElementById('scheduleLoading');
const scheduleEmpty = document.getElementById('scheduleEmpty');
const venueTabsContainer = document.getElementById('venueTabsContainer');
const venueTabs = document.getElementById('venueTabs');
const scheduleRaceGrid = document.getElementById('scheduleRaceGrid');
const scrapeAllVenueBtn = document.getElementById('scrapeAllVenueBtn');

// Toast Notification
function showToast(message, isError = false) {
    toastEl.textContent = message;
    toastEl.style.borderColor = isError ? '#ef4444' : '#10b981';
    toastEl.classList.add('show');
    setTimeout(() => {
        toastEl.classList.remove('show');
    }, 3000);
}

// Fetch and render saved races
async function loadRaces(selectFirst = true) {
    try {
        const res = await fetch(`${API_BASE}/races`);
        if (!res.ok) throw new Error('レース一覧の取得に失敗しました');
        const races = await res.json();

        raceListEl.innerHTML = '';
        if (races.length === 0) {
            raceListEl.innerHTML = '<div class="section-desc" style="padding: 10px;">登録されたレースがありません。「開催日程から探す」ボタンまたはURL入力から取得してください。</div>';
            clearRaceDetail();
            return;
        }

        races.forEach((race) => {
            const item = document.createElement('div');
            item.className = `race-item ${race.id === currentRaceId ? 'active' : ''}`;
            item.innerHTML = `
                <div class="race-item-header">
                    <span class="race-item-place">${race.course} ${race.race_number}R</span>
                    <span class="race-item-num">${race.race_class}</span>
                </div>
                <div class="race-item-name">${race.race_name}</div>
                <div class="race-item-sub">${race.race_date} | ${race.track_type}${race.distance}m | ${race.entry_count || 0}頭</div>
            `;
            item.addEventListener('click', () => {
                loadRaceDetail(race.id);
            });
            raceListEl.appendChild(item);
        });

        if (selectFirst && races.length > 0) {
            const targetId = currentRaceId && races.some(r => r.id === currentRaceId) ? currentRaceId : races[0].id;
            loadRaceDetail(targetId);
        }
    } catch (err) {
        showToast(err.message, true);
    }
}

// Fetch and render specific race detail
async function loadRaceDetail(raceId) {
    try {
        const res = await fetch(`${API_BASE}/races/${raceId}`);
        if (!res.ok) throw new Error('レース詳細の取得に失敗しました');
        currentRaceData = await res.json();
        currentRaceId = raceId;

        // Update active class in sidebar
        document.querySelectorAll('.race-item').forEach((el) => {
            el.classList.remove('active');
        });
        const items = Array.from(raceListEl.children);
        const currentActive = items.find(el => el.innerHTML.includes(currentRaceData.race_name));
        if (currentActive) currentActive.classList.add('active');

        renderHeader(currentRaceData);
        renderAiSummary(currentRaceData.entries);
        renderEntries(currentRaceData.entries);
    } catch (err) {
        showToast(err.message, true);
    }
}

function clearRaceDetail() {
    raceNameEl.textContent = 'レースを選択してください';
    raceNumBadge.textContent = '-';
    raceDateEl.textContent = '-';
    raceCourseEl.textContent = '-';
    raceClassEl.textContent = '-';
    raceStartTimeEl.textContent = '-';
    raceTrackDistEl.textContent = '-';
    raceConditionEl.textContent = '-';
    raceEntryCountEl.textContent = '-';
    aiSummaryBanner.style.display = 'none';
    entriesBody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 40px;">データがありません</td></tr>';
}

function renderHeader(race) {
    raceNameEl.textContent = race.race_name;
    raceNumBadge.textContent = `${race.race_number}R`;
    raceDateEl.textContent = race.race_date;
    raceCourseEl.textContent = `${race.course}競馬場`;
    raceClassEl.textContent = race.race_class;
    raceStartTimeEl.textContent = race.start_time;
    raceTrackDistEl.textContent = `${race.track_type} ${race.distance}m`;
    raceConditionEl.textContent = `${race.weather} / ${race.track_condition}`;
    raceEntryCountEl.textContent = `${race.entries.length}頭`;
}

function getAiMark(rank, expectedROI) {
    if (rank === 1) return '◎';
    if (rank === 2) return '◯';
    if (rank === 3 || (expectedROI >= 1.2 && rank <= 6)) return '▲';
    if (rank <= 5) return '△';
    return '-';
}

function renderAiSummary(entries) {
    const hasPredictions = entries.some(e => e.ai_pred_score !== null && e.ai_pred_score > 0);
    if (!hasPredictions) {
        aiSummaryBanner.style.display = 'none';
        return;
    }

    const sortedByRank = [...entries].sort((a, b) => (a.ai_pred_rank || 99) - (b.ai_pred_rank || 99));
    const honmei = sortedByRank[0];
    const taikou = sortedByRank[1];

    // Find best expected value穴馬 (odds >= 7.0 and high expected value)
    const anaList = [...entries].filter(e => e.odds && e.odds >= 7.0 && e.ai_pred_score && (e.ai_pred_score * e.odds >= 1.0));
    anaList.sort((a, b) => ((b.ai_pred_score * b.odds) - (a.ai_pred_score * a.odds)));
    const ana = anaList.length > 0 ? anaList[0] : sortedByRank[2];

    if (honmei) {
        const prob = Math.round((honmei.ai_pred_score || 0) * 100);
        pickHonmeiHorse.textContent = `${honmei.horse_number}番 ${honmei.horse_name}`;
        pickHonmeiMeta.textContent = `勝率: ${prob}% | 単勝: ${honmei.odds ? honmei.odds + '倍' : '-'} | 騎手: ${honmei.jockey_name}`;
    }

    if (taikou) {
        const prob = Math.round((taikou.ai_pred_score || 0) * 100);
        pickTaikouHorse.textContent = `${taikou.horse_number}番 ${taikou.horse_name}`;
        pickTaikouMeta.textContent = `勝率: ${prob}% | 単勝: ${taikou.odds ? taikou.odds + '倍' : '-'} | 騎手: ${taikou.jockey_name}`;
    }

    if (ana) {
        const prob = Math.round((ana.ai_pred_score || 0) * 100);
        const exp = ana.odds && ana.ai_pred_score ? (ana.odds * ana.ai_pred_score).toFixed(2) : '-';
        pickAnaHorse.textContent = `${ana.horse_number}番 ${ana.horse_name}`;
        pickAnaMeta.textContent = `勝率: ${prob}% | 単勝: ${ana.odds ? ana.odds + '倍' : '-'} | 期待値: ${exp}`;
    }

    aiSummaryBanner.style.display = 'flex';
}

function renderEntries(entries) {
    let sorted = [...entries];

    if (currentSortMode === 'horse_number') {
        sorted.sort((a, b) => a.horse_number - b.horse_number);
    } else if (currentSortMode === 'odds') {
        sorted.sort((a, b) => (a.odds || 999) - (b.odds || 999));
    } else if (currentSortMode === 'ai_score') {
        sorted.sort((a, b) => (b.ai_pred_score || 0) - (a.ai_pred_score || 0));
    }

    entriesBody.innerHTML = '';
    sorted.forEach(entry => {
        const tr = document.createElement('tr');
        
        let weightStr = '-';
        if (entry.horse_weight) {
            const diff = entry.weight_diff !== null && entry.weight_diff !== undefined 
                ? (entry.weight_diff > 0 ? `+${entry.weight_diff}` : `${entry.weight_diff}`)
                : '0';
            weightStr = `${entry.horse_weight}kg (${diff})`;
        }

        const oddsVal = entry.odds ? entry.odds.toFixed(1) : '-';
        const isFav = entry.odds && entry.odds <= 3.5;
        const popVal = entry.popularity ? `${entry.popularity}番人気` : '-';
        const isTopPop = entry.popularity === 1;

        // AI Score Bar & Expected ROI
        const aiScore = entry.ai_pred_score ? (entry.ai_pred_score * 100).toFixed(1) : 0;
        const aiRank = entry.ai_pred_rank || 0;
        
        let expVal = null;
        let expClass = '';
        if (entry.odds && entry.ai_pred_score) {
            expVal = (entry.odds * entry.ai_pred_score).toFixed(2);
            if (expVal >= 1.5) expClass = 'expected-high';
            else if (expVal >= 1.0) expClass = 'expected-mid';
        }

        const aiMark = getAiMark(aiRank, expVal ? parseFloat(expVal) : 0);
        const aiBadgeClass = aiRank <= 3 && aiRank > 0 ? `ai-rank-${aiRank}` : '';

        tr.innerHTML = `
            <td>
                <div class="waku-cell waku-${entry.bracket_number}">${entry.bracket_number}</div>
            </td>
            <td>
                <div class="umaban-cell">${entry.horse_number}</div>
            </td>
            <td>
                <div class="horse-cell">
                    <span class="horse-name">${entry.horse_name}</span>
                    <span class="horse-sub">${entry.sex_age}</span>
                </div>
            </td>
            <td>
                <div class="jockey-cell">
                    <span class="jockey-name">${entry.jockey_name}</span>
                    <span class="impost-val">${entry.impost}kg</span>
                </div>
            </td>
            <td>
                <div class="trainer-cell">
                    <span class="trainer-name">${entry.trainer_name}</span>
                    <span class="weight-val">${weightStr}</span>
                </div>
            </td>
            <td>
                <span class="odds-badge ${isFav ? 'odds-fav' : ''}">${oddsVal}</span>
            </td>
            <td>
                <span class="pop-badge ${isTopPop ? 'pop-top' : ''}">${popVal}</span>
            </td>
            <td>
                <div class="ai-pred-box">
                    <span class="ai-rank-badge ${aiBadgeClass}">${aiMark}</span>
                    <div class="ai-bar-bg" title="勝率予測: ${aiScore}%">
                        <div class="ai-bar-fill" style="width: ${Math.min(aiScore * 2.5, 100)}%;"></div>
                    </div>
                    <span style="font-size: 0.8rem; font-weight: 700; color: #fff;">${aiScore > 0 ? aiScore + '%' : '-'}</span>
                    ${expVal ? `<span class="expected-badge ${expClass}" title="回収期待値: ${expVal}">期待値 ${expVal}</span>` : ''}
                </div>
            </td>
        `;
        entriesBody.appendChild(tr);
    });
}

// ----------------------------------------------------
// AI Predict Action
// ----------------------------------------------------
runAiPredictBtn.addEventListener('click', async () => {
    if (!currentRaceId) {
        showToast('予想するレースを選択してください', true);
        return;
    }

    runAiPredictBtn.disabled = true;
    runAiPredictBtn.innerHTML = '<span>⏳ AI計算中...</span>';

    try {
        const res = await fetch(`${API_BASE}/predict/${currentRaceId}`, { method: 'POST' });
        if (!res.ok) throw new Error('AI予想計算に失敗しました');
        currentRaceData = await res.json();

        showToast(`「${currentRaceData.race_name}」のAI予想が完了しました！`);
        renderAiSummary(currentRaceData.entries);
        renderEntries(currentRaceData.entries);
    } catch (err) {
        showToast(err.message, true);
    } finally {
        runAiPredictBtn.disabled = false;
        runAiPredictBtn.innerHTML = '<span class="ai-sparkle">✨</span><span>🤖 AI予想を実行 (LightGBM)</span>';
    }
});

// ----------------------------------------------------
// Schedule & Calendar Modal Logic
// ----------------------------------------------------
function openModal() {
    scheduleModal.classList.add('active');
    if (!scheduleDateInput.value) {
        scheduleDateInput.value = '2024-05-26';
    }
}

function closeModal() {
    scheduleModal.classList.remove('active');
}

openScheduleModalBtn.addEventListener('click', openModal);
closeScheduleModalBtn.addEventListener('click', closeModal);
scheduleModal.addEventListener('click', (e) => {
    if (e.target === scheduleModal) closeModal();
});

quickDateChips.forEach(chip => {
    chip.addEventListener('click', () => {
        const val = chip.dataset.date;
        if (val === 'today') {
            const today = new Date().toISOString().split('T')[0];
            scheduleDateInput.value = today;
        } else {
            scheduleDateInput.value = val;
        }
        fetchSchedule();
    });
});

fetchScheduleBtn.addEventListener('click', fetchSchedule);

async function fetchSchedule() {
    const dateVal = scheduleDateInput.value;
    if (!dateVal) {
        showToast('日付を選択してください', true);
        return;
    }

    scheduleLoading.style.display = 'flex';
    scheduleEmpty.style.display = 'none';
    venueTabsContainer.style.display = 'none';
    fetchScheduleBtn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/schedule?date=${dateVal}`);
        if (!res.ok) throw new Error('スケジュールの取得に失敗しました');
        currentScheduleData = await res.json();

        if (!currentScheduleData.venues || currentScheduleData.venues.length === 0) {
            scheduleEmpty.style.display = 'block';
            scheduleEmpty.innerHTML = `<span>${dateVal} の開催レースは見つかりませんでした。別の開催日（例: 2024-05-26 ダービー日）をお試しください。</span>`;
            return;
        }

        renderVenueTabs();
        selectVenue(0);
        venueTabsContainer.style.display = 'block';
    } catch (err) {
        showToast(err.message, true);
        scheduleEmpty.style.display = 'block';
    } finally {
        scheduleLoading.style.display = 'none';
        fetchScheduleBtn.disabled = false;
    }
}

function renderVenueTabs() {
    venueTabs.innerHTML = '';
    currentScheduleData.venues.forEach((v, idx) => {
        const btn = document.createElement('button');
        btn.className = `venue-tab-btn ${idx === currentVenueIndex ? 'active' : ''}`;
        btn.textContent = `${v.course} (${v.race_count}R)`;
        btn.addEventListener('click', () => selectVenue(idx));
        venueTabs.appendChild(btn);
    });
}

function selectVenue(idx) {
    currentVenueIndex = idx;
    const venueBtns = venueTabs.querySelectorAll('.venue-tab-btn');
    venueBtns.forEach((b, i) => {
        b.classList.toggle('active', i === idx);
    });

    const venue = currentScheduleData.venues[idx];
    scrapeAllVenueBtn.textContent = `「${venue.course}」の全${venue.races.length}レースを一括取得`;
    
    renderScheduleRaces(venue.races);
}

function renderScheduleRaces(races) {
    scheduleRaceGrid.innerHTML = '';
    races.forEach(r => {
        const card = document.createElement('div');
        card.className = 'schedule-race-card';
        card.innerHTML = `
            <div class="schedule-card-top">
                <span class="schedule-r-badge">${r.race_number}R</span>
                <span class="schedule-card-name" title="${r.race_name}">${r.race_name}</span>
            </div>
            <button class="btn btn-primary btn-sm fetch-single-race-btn" data-raceid="${r.race_id}">
                出馬表を取得
            </button>
        `;

        const btn = card.querySelector('.fetch-single-race-btn');
        btn.addEventListener('click', async () => {
            btn.disabled = true;
            btn.textContent = '取得中...';
            await scrapeSingleRace(r.race_id);
            btn.disabled = false;
            btn.textContent = '取得完了 ✓';
        });

        scheduleRaceGrid.appendChild(card);
    });
}

async function scrapeSingleRace(raceId) {
    try {
        const res = await fetch(`${API_BASE}/scrape`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url_or_date: raceId })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || '取得に失敗しました');

        showToast(`「${data.race_name}」の出馬表を取得しました！`);
        currentRaceId = data.id;
        closeModal();
        await loadRaces(true);
    } catch (err) {
        showToast(err.message, true);
    }
}

scrapeAllVenueBtn.addEventListener('click', async () => {
    const venue = currentScheduleData.venues[currentVenueIndex];
    if (!venue || !venue.races) return;

    const raceIds = venue.races.map(r => r.race_id);
    scrapeAllVenueBtn.disabled = true;
    scrapeAllVenueBtn.textContent = `全${raceIds.length}レースを取得中...`;

    try {
        const res = await fetch(`${API_BASE}/scrape-batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ race_ids: raceIds })
        });
        const result = await res.json();
        if (!res.ok) throw new Error('一括取得に失敗しました');

        showToast(`「${venue.course}」の ${result.success_count}/${result.total} レースを取得しました！`);
        closeModal();
        await loadRaces(true);
    } catch (err) {
        showToast(err.message, true);
    } finally {
        scrapeAllVenueBtn.disabled = false;
        scrapeAllVenueBtn.textContent = `「${venue.course}」の全${venue.races.length}レースを一括取得`;
    }
});

// ----------------------------------------------------
// Core Dashboard Event Listeners
// ----------------------------------------------------
refreshRacesBtn.addEventListener('click', () => {
    loadRaces(false);
    showToast('レース一覧を更新しました');
});

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentSortMode = btn.dataset.sort;
        if (currentRaceData) {
            renderEntries(currentRaceData.entries);
        }
    });
});

scrapeBtn.addEventListener('click', async () => {
    const val = scrapeInput.value.trim();
    if (!val) {
        showToast('レースIDまたはURLを入力してください', true);
        return;
    }

    scrapeBtn.disabled = true;
    scrapeBtn.textContent = '取得中...';

    try {
        const res = await fetch(`${API_BASE}/scrape`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url_or_date: val })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || '取得に失敗しました');

        showToast(`「${data.race_name}」の出馬表を取得しました！`);
        scrapeInput.value = '';
        currentRaceId = data.id;
        await loadRaces(true);
    } catch (err) {
        showToast(err.message, true);
    } finally {
        scrapeBtn.disabled = false;
        scrapeBtn.textContent = '取得';
    }
});

reseedBtn.addEventListener('click', async () => {
    if (!confirm('サンプルレースを再生成しますか？')) return;
    try {
        const res = await fetch(`${API_BASE}/seed`, { method: 'POST' });
        if (!res.ok) throw new Error('復元に失敗しました');
        showToast('サンプルレースを復元しました');
        await loadRaces(true);
    } catch (err) {
        showToast(err.message, true);
    }
});

deleteRaceBtn.addEventListener('click', async () => {
    if (!currentRaceId) return;
    if (!confirm(`レース「${currentRaceData?.race_name}」を削除しますか？`)) return;

    try {
        const res = await fetch(`${API_BASE}/races/${currentRaceId}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('削除に失敗しました');
        showToast('レースを削除しました');
        currentRaceId = null;
        await loadRaces(true);
    } catch (err) {
        showToast(err.message, true);
    }
});

// Initial load
document.addEventListener('DOMContentLoaded', () => {
    loadRaces(true);
});
