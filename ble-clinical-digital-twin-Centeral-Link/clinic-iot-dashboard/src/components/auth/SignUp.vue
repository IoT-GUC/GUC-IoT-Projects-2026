<script setup lang="ts">
import { ref } from 'vue';
import router from '../../router';
import { useSignup } from '../../utils/hooks/auth';
import IconEye from '../shared/icons/IconEye.vue';

const { loading, error, signup } = useSignup()

const user = ref({
    hospitalID: '',
    hospitalName: '',
    address: '',
    adminName: '',
    adminEmail: '',
    adminPassword: ''
})

const passwordVisible = ref(false)

const togglePasswordVisibility = () => {
    passwordVisible.value = !passwordVisible.value
}


const sumbitForm = () => {
    if (!user.value.hospitalID ||
        !user.value.hospitalName ||
        !user.value.adminName ||
        !user.value.adminEmail ||
        !user.value.adminPassword
    ) return

    signup({
        hospital_id: user.value.hospitalID,
        name: user.value.hospitalName,
        address: user.value.address,
        admin_name: user.value.adminName,
        admin_email: user.value.adminEmail,
        password: user.value.adminPassword
    })
        .then(res => router.push({ name: 'dashboard' }))
}


</script>

<template>
    <div
        class=" w-122 flex flex-col justify-stretch gap-8 p-10 rounded-lg border border-[#259DF430] shadow-2xl shadow-[#00000040]">
        <div class="flex flex-col gap-2">
            <p class="text-white text-3xl font-bold">
                Facility Onboarding
            </p>
            <p class="text-[14px] text-[#94A3B8]">
                Register your hospital for the AI monitoring suite
            </p>
        </div>
        <div class="flex flex-col gap-5">
            <div class="flex flex-col gap-2.5">
                <p class="text-[14px] text-[#CBD5E1] font-medium">Hospital ID</p>
                <div class="relative">
                    <input v-model="user.hospitalID" name="username" placeholder="HOSP-4829-X" />
                </div>
            </div>
            <div class="flex flex-col gap-2.5">
                <p class="text-[14px] text-[#CBD5E1] font-medium">Hospital Name</p>
                <div class="relative">
                    <input v-model="user.hospitalName" placeholder="St. Margaret's Medical Centre" />
                </div>
            </div>
            <div class="flex flex-col gap-2.5">
                <p class="text-[14px] text-[#CBD5E1] font-medium">Address</p>
                <div class="relative">
                    <input v-model="user.address" placeholder="St. Margaret's Medical Centre" />
                </div>
            </div>
            <div class="flex flex-col gap-2.5">
                <p class="text-[14px] text-[#CBD5E1] font-medium">Admin Name</p>
                <div class="relative">
                    <input v-model="user.adminName" placeholder="Dr. John Doe" />
                </div>
            </div>
            <div class="flex flex-col gap-2.5">
                <p class="text-[14px] text-[#CBD5E1] font-medium">Admin Email</p>
                <div class="relative">
                    <input v-model="user.adminEmail" type="email" placeholder="johndoe@gmail.com" />
                </div>
            </div>
            <div class="flex flex-col gap-2.5">
                <p class="text-[14px] text-[#CBD5E1] font-medium">Admin Password</p>
                <div class="relative">
                    <input v-model="user.adminPassword" name="password" :type="passwordVisible ? 'text' : 'password'"
                        placeholder="••••••••" />
                    <button @click="togglePasswordVisibility"
                        class="w-5 text-[#94A3B8] absolute top-1/2 -translate-y-1/2 right-4"
                        :style="{ color: passwordVisible ? '#259DF4' : '#94A3B8' }">
                        <IconEye />
                    </button>
                </div>
            </div>
            <div>
                <button @click="sumbitForm" :disabled="loading"
                    class="text-white flex items-center gap-2 justify-center w-full bg-[#334155] p-4 rounded-lg shadow">
                    Register Facility Access
                </button>
            </div>
        </div>
        <div class="text-red-500 text-sm" v-if="error">
            <p>{{ error }}</p>
        </div>
    </div>
</template>