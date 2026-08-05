<script setup>
import { ref, onMounted, computed } from 'vue'

const episodes = ref([])
const characters = ref([])
const viewMode = ref('bilibili')
const loading = ref(true)
const watchedSet = ref(new Set())
const filterMainStory = ref(false)
const characterFilter = ref('')
const characterFilterList = ref([])
const characterSearch = ref('')
const showDetailModal = ref(false)
const detailEpisode = ref(null)
const charPage = ref(0)
const perPage = ref(100)
const perPageOptions = [50, 100, 200, 500]
const jumpPage = ref('')

const filteredEpisodes = computed(() => {
  let list = episodes.value
  if (filterMainStory.value) {
    list = list.filter(ep => ep.is_main_story)
  }
  if (characterFilterList.value.length > 0) {
    list = list.filter(ep =>
      characterFilterList.value.every(charName =>
        ep.characters.some(c => c.name === charName)
      )
    )
  }
  if (characterFilter.value) {
    const kw = characterFilter.value.toLowerCase()
    list = list.filter(ep =>
      ep.characters.some(c => c.name.toLowerCase().includes(kw))
    )
  }
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredEpisodes.value.length / perPage.value)))

const currentPage = computed(() => Math.min(charPage.value, totalPages.value - 1))

const pagedEpisodes = computed(() => {
  const start = currentPage.value * perPage.value
  return filteredEpisodes.value.slice(start, start + perPage.value)
})

const pageNumbers = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  const result = []
  const windowSize = 5
  let start = Math.max(0, current - Math.floor(windowSize / 2))
  let end = Math.min(total - 1, start + windowSize - 1)
  if (end - start < windowSize - 1) {
    start = Math.max(0, end - windowSize + 1)
  }
  for (let i = start; i <= end; i++) {
    result.push(i)
  }
  return result
})

const watchProgress = computed(() => {
  const total = episodes.value.length
  const watched = [...watchedSet.value].filter(k => k.startsWith(viewMode.value)).length
  return total > 0 ? Math.round((watched / total) * 100) : 0
})

const watchedCount = computed(() => {
  return [...watchedSet.value].filter(k => k.startsWith(viewMode.value)).length
})

const displayedCharacters = computed(() => {
  if (!characterSearch.value) return []
  const kw = characterSearch.value.toLowerCase()
  return characters.value.filter(c => c.name.toLowerCase().includes(kw)).slice(0, 10)
})

function toggleWatched(episodeNum) {
  const key = `${viewMode.value}-${episodeNum}`
  const newSet = new Set(watchedSet.value)
  if (newSet.has(key)) {
    newSet.delete(key)
  } else {
    newSet.add(key)
  }
  watchedSet.value = newSet
  saveWatched()
}

function isWatched(episodeNum) {
  return watchedSet.value.has(`${viewMode.value}-${episodeNum}`)
}

function saveWatched() {
  localStorage.setItem('conan-watched', JSON.stringify([...watchedSet.value]))
}

function loadWatched() {
  try {
    const saved = localStorage.getItem('conan-watched')
    if (saved) {
      watchedSet.value = new Set(JSON.parse(saved))
    }
  } catch (e) {}
}

function showDetail(ep) {
  detailEpisode.value = ep
  showDetailModal.value = true
}

function closeDetail() {
  showDetailModal.value = false
  detailEpisode.value = null
}

function onSearchEnter() {
  if (characterSearch.value) {
    addCharacterFilter(characterSearch.value)
  }
}

function addCharacterFilter(name) {
  if (!characterFilterList.value.includes(name)) {
    characterFilterList.value.push(name)
  }
  characterSearch.value = ''
}

function removeCharacterFilter(name) {
  characterFilterList.value = characterFilterList.value.filter(n => n !== name)
}

function clearAllFilters() {
  filterMainStory.value = false
  characterFilterList.value = []
  characterSearch.value = ''
}

async function loadData() {
  loading.value = true
  try {
    const [epRes, charRes] = await Promise.all([
      fetch(`${import.meta.env.BASE_URL}data/${viewMode.value}.json`),
      fetch(`${import.meta.env.BASE_URL}data/characters.json`)
    ])
    if (epRes.ok) episodes.value = await epRes.json()
    if (charRes.ok) characters.value = await charRes.json()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function switchView(mode) {
  if (viewMode.value === mode) return
  viewMode.value = mode
  charPage.value = 0
  loadData()
}

function statusLabel(status) {
  const map = {
    '登场': '登场',
    '登场（初）': '初登场',
    '提及': '提及',
    '回忆': '回忆'
  }
  return map[status] || status || '登场'
}

function goToPage(p) {
  charPage.value = Math.max(0, Math.min(p, totalPages.value - 1))
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function changePerPage(val) {
  perPage.value = val
  charPage.value = 0
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function jumpToPage() {
  const p = parseInt(jumpPage.value, 10)
  if (isNaN(p)) return
  goToPage(p - 1)
  jumpPage.value = ''
}

onMounted(() => {
  loadWatched()
  loadData()
})
</script>

<template>
  <div class="app">
    <header class="header">
      <h1 class="title">柯南追番工具</h1>
      <div class="progress">
        已看 {{ watchProgress }}%
        <span class="count">({{ watchedCount }}/{{ episodes.length }})</span>
      </div>
    </header>

    <div class="toolbar">
      <div class="view-switch">
        <button
          :class="{ active: viewMode === 'bilibili' }"
          @click="switchView('bilibili')"
        >B站版 (拆分版)</button>
        <button
          :class="{ active: viewMode === 'original' }"
          @click="switchView('original')"
        >日本原版</button>
      </div>

      <div class="filters">
        <button
          :class="{ active: filterMainStory }"
          @click="filterMainStory = !filterMainStory"
          class="btn-main"
        >
          主线剧情
        </button>

        <div class="search-box">
          <input
            v-model="characterSearch"
            type="text"
            placeholder="搜索人物筛选..."
              @keydown.enter="onSearchEnter"
          />
          <div v-if="displayedCharacters.length && characterSearch" class="suggestions">
            <div
              v-for="c in displayedCharacters"
              :key="c.name"
              class="suggestion-item"
              @click="addCharacterFilter(c.name)"
            >
              {{ c.name }}
              <span class="count">{{ c.episode_count }}集</span>
            </div>
          </div>
        </div>

        <div v-if="characterFilterList.length || filterMainStory" class="active-tags">
          <span v-if="filterMainStory" class="tag tag-main">
            主线 <button @click="filterMainStory = false">&times;</button>
          </span>
          <span v-for="c in characterFilterList" :key="c" class="tag">
            {{ c }}
            <button @click="removeCharacterFilter(c)">&times;</button>
          </span>
          <button class="clear-btn" @click="clearAllFilters">清除筛选</button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else>
      <div class="stats">
        当前显示 {{ filteredEpisodes.length }} 集
        <span v-if="filterMainStory" class="hint">(主线剧情)</span>
        <span v-if="characterFilterList.length" class="hint">(含 {{ characterFilterList.join(', ') }})</span>
      </div>

      <div class="grid">
        <div
          v-for="ep in pagedEpisodes"
          :key="viewMode + '-' + ep.episode"
          class="episode-cell"
          :class="{
            watched: isWatched(ep.episode),
            'main-story': ep.is_main_story
          }"
        >
          <div class="ep-num">{{ viewMode === 'original' ? 'TV' : 'B' }}{{ ep.episode }}</div>
          <div class="ep-name" :title="ep.name">{{ ep.name }}</div>
          <div class="ep-actions">
            <button
              class="btn-eye"
              :class="{ checked: isWatched(ep.episode) }"
              @click="toggleWatched(ep.episode)"
              :title="isWatched(ep.episode) ? '取消已看' : '标记已看'"
            >
              {{ isWatched(ep.episode) ? 'Done' : 'Mark' }}
            </button>
            <button class="btn-detail" @click="showDetail(ep)" title="详情">i</button>
            <a
              v-if="ep.link"
              :href="ep.link"
              target="_blank"
              class="btn-link"
              title="B站观看"
            >B</a>
          </div>
        </div>
      </div>

      <div v-if="totalPages > 1" class="pagination">
        <button
          class="page-btn"
          :disabled="currentPage <= 0"
          @click="goToPage(currentPage - 1)"
        >上一页</button>

        <span v-if="pageNumbers[0] > 0" class="page-ellipsis">…</span>
        <button
          v-for="p in pageNumbers"
          :key="p"
          class="page-btn"
          :class="{ active: p === currentPage }"
          @click="goToPage(p)"
        >{{ p + 1 }}</button>
        <span v-if="pageNumbers[pageNumbers.length - 1] < totalPages - 1" class="page-ellipsis">…</span>

        <button
          class="page-btn"
          :disabled="currentPage >= totalPages - 1"
          @click="goToPage(currentPage + 1)"
        >下一页</button>

        <span class="page-info">共 {{ filteredEpisodes.length }} 集 / {{ totalPages }} 页</span>

        <div class="page-jump">
          <input
            v-model="jumpPage"
            type="number"
            min="1"
            :max="totalPages"
            placeholder="页码"
            @keydown.enter="jumpToPage"
          />
          <button class="page-btn" @click="jumpToPage">跳转</button>
        </div>

        <label class="per-page">
          每页
          <select v-model="perPage" @change="changePerPage(perPage)">
            <option v-for="n in perPageOptions" :key="n" :value="n">{{ n }}</option>
          </select>
          集
        </label>
      </div>
    </template>

    <div v-if="showDetailModal" class="modal-overlay" @click.self="closeDetail">
      <div class="modal">
        <button class="modal-close" @click="closeDetail">&times;</button>
        <h2>{{ detailEpisode?.name }}</h2>
        <div class="modal-meta">
          <div class="meta-item">
            <span class="meta-label">编号</span>
            <span>{{ viewMode === 'original' ? 'TV' + detailEpisode?.episode : 'episode' + detailEpisode?.episode }}</span>
          </div>
          <div v-if="detailEpisode?.tv_range && detailEpisode?.tv_range !== detailEpisode?.episode" class="meta-item">
            <span class="meta-label">原版编号</span>
            <span>{{ detailEpisode?.tv_range }}</span>
          </div>
          <div v-if="detailEpisode?.pub_date" class="meta-item">
            <span class="meta-label">发布时间</span>
            <span>{{ detailEpisode?.pub_date }}</span>
          </div>
          <div v-if="detailEpisode?.link" class="meta-item">
            <span class="meta-label">观看链接</span>
            <a :href="detailEpisode?.link" target="_blank" class="bilibili-link">前往B站观看</a>
          </div>
        </div>
        <div v-if="detailEpisode?.characters?.length" class="char-list">
          <h3>登场人物 ({{ detailEpisode.characters.length }})</h3>
          <table class="char-table">
            <thead>
              <tr>
                <th>角色</th>
                <th>类型</th>
                <th>状态</th>
                <th>声优</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in detailEpisode.characters" :key="c.name">
                <td class="char-name">{{ c.name }}</td>
                <td>{{ c.category || '-' }}</td>
                <td>{{ statusLabel(c.status) }}</td>
                <td>{{ c.voice_actor || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="no-chars">
          暂无人物数据
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  background: #0d1117;
  color: #c9d1d9;
}

.header {
  padding: 16px 24px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
  display: flex;
  align-items: baseline;
  gap: 16px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header h1 {
  font-size: 20px;
  font-weight: 600;
  color: #ff8c00;
}

.header .progress {
  font-size: 13px;
  color: #8b949e;
}

.header .count {
  color: #484f58;
}

.toolbar {
  padding: 12px 24px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.view-switch {
  display: flex;
  gap: 0;
  border: 1px solid #30363d;
  border-radius: 6px;
  overflow: hidden;
}

.view-switch button {
  padding: 6px 16px;
  border: none;
  background: #21262d;
  color: #c9d1d9;
  cursor: pointer;
  font-size: 13px;
}

.view-switch button.active {
  background: #388bfd;
  color: #fff;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  flex: 1;
  margin-left: 12px;
}

.btn-main {
  padding: 6px 12px;
  border: 1px solid #f85149;
  border-radius: 6px;
  background: transparent;
  color: #f85149;
  cursor: pointer;
  font-size: 13px;
}

.btn-main.active {
  background: #f85149;
  color: #fff;
}

.search-box {
  position: relative;
  flex: 1;
  max-width: 300px;
}

.search-box input {
  width: 100%;
  padding: 6px 12px;
  border: 1px solid #30363d;
  border-radius: 6px;
  background: #0d1117;
  color: #c9d1d9;
  font-size: 13px;
  outline: none;
}

.search-box input:focus {
  border-color: #58a6ff;
}

.suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 0 0 6px 6px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 20;
}

.suggestion-item {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.suggestion-item:hover {
  background: #21262d;
}

.suggestion-item .count {
  color: #8b949e;
  font-size: 12px;
}

.active-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  background: #21262d;
  border: 1px solid #30363d;
  border-radius: 12px;
  font-size: 12px;
  color: #8b949e;
}

.tag button {
  border: none;
  background: none;
  color: #8b949e;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
}

.tag button:hover {
  color: #f85149;
}

.tag-main {
  border-color: #f85149;
  color: #f85149;
}

.clear-btn {
  border: none;
  background: none;
  color: #8b949e;
  cursor: pointer;
  font-size: 12px;
  text-decoration: underline;
}

.stats {
  padding: 10px 24px;
  font-size: 13px;
  color: #8b949e;
}

.stats .main-title {
  color: #f85149;
}

.stats .hint {
  color: #58a6ff;
}

.loading {
  padding: 60px;
  text-align: center;
  color: #8b949e;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 10px;
  padding: 12px 24px;
}

.episode-cell {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.episode-cell.watched {
  opacity: 0.45;
}

.episode-cell.main-story {
  border-left: 3px solid #f85149;
}

.ep-num {
  font-size: 14px;
  font-weight: 600;
  color: #58a6ff;
  min-width: 52px;
  font-family: 'Courier New', monospace;
}

.ep-name {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ep-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.ep-actions button {
  width: 32px;
  height: 28px;
  border: 1px solid #30363d;
  border-radius: 4px;
  background: #21262d;
  color: #c9d1d9;
  cursor: pointer;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ep-actions button:hover {
  background: #30363d;
}

.btn-eye.checked {
  background: #238636;
  border-color: #238636;
  color: #fff;
}

.btn-link {
  width: 28px;
  height: 28px;
  border: 1px solid #58a6ff;
  border-radius: 4px;
  background: transparent;
  color: #58a6ff;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
}

.btn-link:hover {
  background: #58a6ff;
  color: #fff;
}

.pagination {
  padding: 16px 24px 32px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
  align-items: center;
}

.page-btn {
  padding: 6px 12px;
  min-width: 34px;
  border: 1px solid #30363d;
  border-radius: 6px;
  background: #21262d;
  color: #c9d1d9;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s;
}

.page-btn:hover:not(:disabled):not(.active) {
  background: #30363d;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

.page-btn.active {
  background: #388bfd;
  border-color: #388bfd;
  color: #fff;
  font-weight: 600;
}

.page-ellipsis {
  color: #8b949e;
  padding: 0 2px;
  font-size: 13px;
}

.page-info {
  font-size: 13px;
  color: #8b949e;
  padding: 0 8px;
}

.page-jump {
  display: flex;
  align-items: center;
  gap: 4px;
}

.page-jump input {
  width: 56px;
  padding: 6px 8px;
  border: 1px solid #30363d;
  border-radius: 6px;
  background: #0d1117;
  color: #c9d1d9;
  font-size: 13px;
  outline: none;
}

.page-jump input:focus {
  border-color: #58a6ff;
}

.per-page {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #8b949e;
}

.per-page select {
  padding: 6px 8px;
  border: 1px solid #30363d;
  border-radius: 6px;
  background: #21262d;
  color: #c9d1d9;
  font-size: 13px;
  outline: none;
  cursor: pointer;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 20px;
}

.modal {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  padding: 24px;
  max-width: 750px;
  width: 100%;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
}

.modal-close {
  position: absolute;
  top: 12px;
  right: 12px;
  border: none;
  background: none;
  color: #8b949e;
  font-size: 20px;
  cursor: pointer;
}

.modal h2 {
  font-size: 18px;
  margin-bottom: 16px;
  color: #ff8c00;
  padding-right: 24px;
}

.modal-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #30363d;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-label {
  font-size: 12px;
  color: #8b949e;
  text-transform: uppercase;
}

.meta-item span:last-child {
  font-size: 13px;
}

.bilibili-link {
  color: #58a6ff;
  text-decoration: none;
  font-size: 13px;
}

.bilibili-link:hover {
  text-decoration: underline;
}

.char-list h3 {
  font-size: 15px;
  margin-bottom: 12px;
  color: #c9d1d9;
}

.char-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.char-table th {
  text-align: left;
  padding: 8px 12px;
  border-bottom: 1px solid #30363d;
  color: #8b949e;
  font-weight: 500;
}

.char-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #21262d;
}

.char-name {
  color: #58a6ff;
  font-weight: 500;
}

.no-char {
  padding: 20px;
  text-align: center;
  color: #8b949e;
}
</style>