import { ref, watch } from 'vue'

const STORAGE_KEY = 'sidebar_collapsed'

const isCollapsed = ref(localStorage.getItem(STORAGE_KEY) === 'true')

watch(isCollapsed, (value) => {
  localStorage.setItem(STORAGE_KEY, String(value))
})

export function useSidebar() {
  function toggle() {
    isCollapsed.value = !isCollapsed.value
  }

  return { isCollapsed, toggle }
}
