<template>
  <div class="relative w-full rounded-lg overflow-hidden border border-white/10 bg-[#1a1f2e]" style="aspect-ratio: 16/9;">
    <!-- Blueprint background -->
    <div
      ref="mapRef"
      class="relative w-full h-full cursor-crosshair select-none"
      @click="handleClick"
    >
      <!-- Blueprint image or placeholder grid -->
      <img
        v-if="blueprintUrl"
        :src="blueprintUrl"
        alt="Floor blueprint"
        class="absolute inset-0 w-full h-full object-cover opacity-30 pointer-events-none"
      />
      <!-- Fallback grid when no blueprint -->
      <svg
        v-else
        class="absolute inset-0 w-full h-full opacity-10 pointer-events-none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#60a5fa" stroke-width="0.5"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      <!-- Placed pin -->
      <Transition name="pin">
        <div
          v-if="pinPosition"
          class="absolute -translate-x-1/2 -translate-y-full pointer-events-none"
          :style="{ left: `${pinPosition.xPercent}%`, top: `${pinPosition.yPercent}%` }"
        >
          <!-- Pin icon -->
          <div class="flex flex-col items-center">
            <div class="w-6 h-6 rounded-full bg-blue-500 border-2 border-white shadow-lg shadow-blue-500/50 flex items-center justify-center">
              <div class="w-2 h-2 rounded-full bg-white"></div>
            </div>
            <div class="w-0.5 h-3 bg-blue-400"></div>
            <div class="w-1.5 h-1.5 rounded-full bg-blue-400 opacity-50"></div>
          </div>
          <!-- Pulse ring -->
          <div class="absolute top-0 left-1/2 -translate-x-1/2 w-6 h-6 rounded-full border border-blue-400 animate-ping opacity-40"></div>
        </div>
      </Transition>

      <!-- Crosshair hint when no pin -->
      <div
        v-if="!pinPosition"
        class="absolute inset-0 flex items-center justify-center pointer-events-none"
      >
        <div class="text-center">
          <div class="text-white/20 text-sm font-mono tracking-widest uppercase">Click to place router</div>
        </div>
      </div>
    </div>

    <!-- Coordinates badge -->
    <Transition name="fade">
      <div
        v-if="pinPosition"
        class="absolute bottom-3 right-3 bg-black/60 backdrop-blur-sm border border-white/10 rounded-md px-3 py-1.5 font-mono text-xs text-blue-300"
      >
        X: {{ modelValue?.x.toFixed(3) }} · Y: {{ modelValue?.y.toFixed(3) }}
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

export interface Location {
  x: number
  y: number
}

interface PinPosition {
  xPercent: number
  yPercent: number
}

const props = defineProps<{
  modelValue: Location | null
  blueprintUrl?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: Location): void
}>()

const mapRef = ref<HTMLDivElement | null>(null)
const pinPosition = ref<PinPosition | null>(null)

function handleClick(event: MouseEvent) {
  const el = mapRef.value
  if (!el) return

  const rect = el.getBoundingClientRect()
  const xPercent = ((event.clientX - rect.left) / rect.width) * 100
  const yPercent = ((event.clientY - rect.top) / rect.height) * 100

  pinPosition.value = { xPercent, yPercent }

  // Normalize to 0–1 range for the API
  emit('update:modelValue', {
    x: parseFloat((xPercent / 100).toFixed(6)),
    y: parseFloat((yPercent / 100).toFixed(6)),
  })
}

// Sync pin if value is set externally
watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      pinPosition.value = { xPercent: val.x * 100, yPercent: val.y * 100 }
    } else {
      pinPosition.value = null
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.pin-enter-active {
  animation: pin-drop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
@keyframes pin-drop {
  from { transform: translateX(-50%) translateY(-200%) scale(0.5); opacity: 0; }
  to { transform: translateX(-50%) translateY(-100%) scale(1); opacity: 1; }
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
