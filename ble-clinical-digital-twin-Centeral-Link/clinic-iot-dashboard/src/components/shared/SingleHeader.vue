<template>
  <div
    class="w-full rounded-2xl border border-slate-800/80 bg-linear-to-r from-[#0c1727] via-[#0f1c2f] to-[#101b2b] px-6 py-5 shadow-[0_0_0_1px_rgba(59,130,246,0.05),0_20px_40px_rgba(0,0,0,0.35)]">
    <div class="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
      <!-- Left -->
      <div class="flex items-center gap-4">
        <!-- Router Icon -->
        <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-500/10 ring-1 ring-blue-400/10">
          <div class="h-7 w-7 text-sky-400">
            <component :is="icon"></component>
          </div>
        </div>

        <!-- Title -->
        <div>
          <div class="flex flex-wrap items-center gap-3">
            <h1 class="text-2xl font-semibold tracking-tight text-white">
              {{ title }}
            </h1>

            <span
              class="rounded-lg border border-emerald-400/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-400"
              :style="{ color: statusColor }">
              {{ status }}
            </span>
          </div>
        </div>
      </div>

      <!-- Right -->
      <div class="py-2 px-4 rounded-2xl bg-[#1E293B80] border border-[#1E293B]">
        <p class="text-xs text-gray-500 font-bold">{{ feature?.name.toUpperCase() }}</p>
        <p class="text-xl font-bold text-[#259DF4]">{{ feature?.value }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue';

defineProps<{
  title: string,
  status: string,
  statusColor: string,
  icon: Component,
  feature: { name: string, value: any }
}>()

</script>