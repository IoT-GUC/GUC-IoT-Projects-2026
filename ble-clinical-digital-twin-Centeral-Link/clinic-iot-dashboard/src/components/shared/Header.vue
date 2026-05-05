<script setup lang="ts">
import IconPlus from './icons/IconPlus.vue';
import IconSearch from './icons/IconSearch.vue';

defineProps({
    searchPlaceholder: {
        type: String,
        default: 'Search ...'
    },
    addNewText: {
        type: String,
        default: 'Add New'
    }
})

const searchQuery = defineModel<string>();

const emit = defineEmits(['add-new'])

const addNew = () => {
    emit('add-new')
}
</script>

<template>
    <div class="p-4 flex items-center gap-4 border-b border-[#1E293B]">
        <div class="grow h-9! relative">
            <div class="w-5 text-[#94A3B8] absolute top-1/2 -translate-y-1/2 left-4">
                <IconSearch />
            </div>
            <input v-model="searchQuery" :placeholder="searchPlaceholder" class="pl-11! h-full!" />
        </div>
        <div>
            <button @click="addNew"
                class="text-white font-medium text-sm h-full flex items-center gap-2 justify-center bg-[#259DF4] px-4 py-2 rounded-lg">
                <span class="w-3 text-white">
                    <IconPlus />
                </span>
                {{ addNewText }}
            </button>
        </div>
    </div>
</template>