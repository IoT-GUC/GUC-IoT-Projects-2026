<script setup lang="ts">
import { ref } from 'vue';
import IconEye from '../shared/icons/IconEye.vue';
import IconHospital from '../shared/icons/IconHospital.vue';
import IconLock from '../shared/icons/IconLock.vue';
import router from '../../router';
import { useLogin } from '../../utils/hooks/auth';
const { loading, error, login } = useLogin()

const user = ref({
    hospitalID: '',
    password: ''
})

const passwordVisible = ref(false)

const togglePasswordVisibility = () => {
    passwordVisible.value = !passwordVisible.value
}

const sumbitForm = () => {
    if (!user.value.hospitalID || !user.value.password) return
    login({ hospital_id: user.value.hospitalID, password: user.value.password })
    .then(res => router.push({ name: 'dashboard' }))
}

</script>

<template>
    <div
        class=" w-122 flex flex-col justify-stretch gap-8 p-10 rounded-lg border border-[#259DF430] shadow-2xl shadow-[#00000040]">
        <div class="flex flex-col gap-2">
            <p class="text-white text-3xl font-bold">
                Welcom Back
            </p>
            <p class="text-[14px] text-[#94A3B8]">
                Access your secure clinic workspace
            </p>
        </div>
        <div class="flex flex-col gap-5">
            <div class="flex flex-col gap-2.5">
                <p class="text-[14px] text-[#CBD5E1] font-medium">Hospital ID</p>
                <div class="relative">
                    <div class="w-5 text-[#94A3B8] absolute top-1/2 -translate-y-1/2 left-4">
                        <IconHospital />
                    </div>
                    <input v-model="user.hospitalID" name="username" placeholder="HOSP-4829-X" class="pl-11!" />
                </div>
            </div>
            <div class="flex flex-col gap-2.5">
                <div class="flex justify-between">
                    <p class="text-[14px] text-[#CBD5E1] font-medium">Password</p>
                </div>
                <div class="relative">
                    <div class="w-5 text-[#94A3B8] absolute top-1/2 -translate-y-1/2 left-4">
                        <IconLock />
                    </div>
                    <input v-model="user.password" name="password" :type="passwordVisible ? 'text' : 'password'" placeholder="••••••••"
                        class="pl-11! " />
                    <button @click="togglePasswordVisibility"
                        class="w-5 text-[#94A3B8] absolute top-1/2 -translate-y-1/2 right-4"
                        :style="{ color: passwordVisible ? '#259DF4' : '#94A3B8' }">
                        <IconEye />
                    </button>
                </div>
            </div>
            <div>
                <button @click="sumbitForm" :disabled="loading"
                    class="text-white flex items-center gap-2 justify-center w-full bg-[#259DF4] p-4 rounded-lg shadow">
                    Initialize Secure Session
                    <span class="w-3.5 text-white">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path
                                d="M10.1458 7.5H0V5.83333H10.1458L5.47917 1.16667L6.66667 0L13.3333 6.66667L6.66667 13.3333L5.47917 12.1667L10.1458 7.5Z"
                                fill="white" />
                        </svg>
                    </span>
                </button>
            </div>
            <div class="text-red-500 text-sm" v-if="error">
                <p>{{ error }}</p>
            </div>
        </div>
    </div>
</template>