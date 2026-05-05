<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useBlueprint } from '../../utils/hooks/settings'

const { blueprintUrl, loading, error, fetchBlueprint, uploadBlueprint } = useBlueprint()

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFileName = ref<string | undefined>(undefined)

onMounted(() => {
  fetchBlueprint()
})

function triggerFileInput() {
  fileInput.value?.click()
}

async function onFileChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  selectedFileName.value = file.name
  await uploadBlueprint(file)
}

function viewFullMap() {
  if (blueprintUrl.value) window.open(blueprintUrl.value, '_blank')
}
</script>

<template>
  <section>
    <h2 class="text-white font-bold text-lg mb-1">Clinic Blueprint Management</h2>
    <p class="text-gray-400 text-sm mb-4">Upload or update floor plans to map IoT sensor locations accurately.</p>

    <div class="bg-[#1a1f2e] border border-gray-700 rounded-xl p-6">
      <div class="flex items-center gap-5">
        <!-- Blueprint Preview Thumbnail -->
        <div class="w-24 h-24 shrink-0 bg-[#111827] border-2 border-dashed border-gray-600 rounded-xl flex items-center justify-center overflow-hidden">
          <img
            v-if="blueprintUrl"
            :src="blueprintUrl"
            alt="Floor plan preview"
            class="w-full h-full object-cover rounded-xl"
          />
          <svg v-else class="w-8 h-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
        </div>

        <!-- Info & Actions -->
        <div class="flex-1 min-w-0">
          <p class="text-white text-sm font-medium">
            Current Floor Plan:
            <a
              v-if="blueprintUrl"
              :href="blueprintUrl"
              target="_blank"
              class="text-blue-400 hover:underline truncate"
            >{{ selectedFileName ?? 'View Blueprint' }}</a>
            <span v-else class="text-gray-500">No blueprint uploaded</span>
          </p>
          <p class="text-gray-400 text-xs mt-1">Format: SVG, PNG or PDF (Max 10MB).</p>

          <p v-if="error" class="text-red-400 text-xs mt-2">{{ error  }}</p>

          <div class="flex items-center gap-3 mt-3">
            <!-- Hidden file input -->
            <input
              ref="fileInput"
              type="file"
              accept=".svg,.png,.pdf"
              class="hidden"
              @change="onFileChange"
            />
            <button
              @click="triggerFileInput"
              :disabled="loading"
              class="flex items-center gap-1.5 text-blue-400 text-sm hover:text-blue-300 transition-colors disabled:opacity-50"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              {{ loading ? 'Uploading...' : 'Update Blueprint' }}
            </button>

            <button
              v-if="blueprintUrl"
              @click="viewFullMap"
              class="bg-white text-gray-900 text-sm px-4 py-1.5 rounded-lg hover:bg-gray-100 transition-colors font-medium"
            >
              View Full Map
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
