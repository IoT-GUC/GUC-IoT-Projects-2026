<script setup lang="ts">
import { ref } from 'vue'
import SignIn from './SignIn.vue'
import SignUp from './SignUp.vue'

type Tab = 'signin' | 'signup'

const activeTab = ref<Tab>('signin')

const switchTab = (tab: Tab) => {
  activeTab.value = tab
}
</script>

<template>
  <div class="flex items-center justify-center py-10">
    <div class="w-full">

      <!-- Tab Switcher -->
      <div class="relative flex bg-[#161b27] border border-[#ffffff0f] rounded-xl p-1 mb-6 shadow-inner">
        <!-- Sliding indicator -->
        <div
          class="absolute top-1 bottom-1 w-[calc(50%-4px)] rounded-lg bg-[#1e2638] border border-[#ffffff14] shadow-md transition-all duration-300 ease-in-out"
          :class="activeTab === 'signin' ? 'left-1' : 'left-[calc(50%+3px)]'"
        />

        <button
          @click="switchTab('signin')"
          class="relative z-10 flex-1 py-2.5 text-sm font-semibold tracking-wide rounded-lg transition-colors duration-300"
          :class="activeTab === 'signin' ? 'text-white' : 'text-[#6b7a99] hover:text-[#a0aec0]'"
        >
          Sign In
        </button>

        <button
          @click="switchTab('signup')"
          class="relative z-10 flex-1 py-2.5 text-sm font-semibold tracking-wide rounded-lg transition-colors duration-300"
          :class="activeTab === 'signup' ? 'text-white' : 'text-[#6b7a99] hover:text-[#a0aec0]'"
        >
          Register
        </button>
      </div>

      <!-- Panel -->
      <div class="relative overflow-hidden">

        <!-- Sign In Panel -->
        <Transition
          enter-active-class="transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]"
          enter-from-class="opacity-0 translate-x-[-20px]"
          enter-to-class="opacity-100 translate-x-0"
          leave-active-class="transition-all duration-200 ease-in"
          leave-from-class="opacity-100 translate-x-0"
          leave-to-class="opacity-0 translate-x-[-20px]"
        >
          <SignIn v-if="activeTab === 'signin'" />
        </Transition>

        <!-- Sign Up Panel -->
        <Transition
          enter-active-class="transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]"
          enter-from-class="opacity-0 translate-x-[20px]"
          enter-to-class="opacity-100 translate-x-0"
          leave-active-class="transition-all duration-200 ease-in"
          leave-from-class="opacity-100 translate-x-0"
          leave-to-class="opacity-0 translate-x-[20px]"
        >
          <SignUp v-if="activeTab === 'signup'" />
        </Transition>

      </div>
    </div>
  </div>
</template>