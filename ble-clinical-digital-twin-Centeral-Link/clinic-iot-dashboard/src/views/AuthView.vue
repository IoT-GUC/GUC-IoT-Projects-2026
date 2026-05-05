<script setup lang="ts">
import IconAction from '../components/shared/icons/IconAction.vue';
import Feature from '../components/auth/Feature.vue';
import IconCompliant from '../components/shared/icons/IconCompliant.vue';
import IconLogo from '../components/shared/icons/IconLogo.vue';
import IconAI from '../components/shared/icons/IconAI.vue';
import AuthTabs from '../components/auth/AuthTabs.vue';

</script>

<template>
    <div class="flex flex-col items-center h-full w-full py-13.5 bg-[#101A22]">
        <div class="grid grid-cols-2 item justify-stretch gap-2 w-5xl items-stretch">
            <div class="flex flex-col items-center pt-14">
                <div class="flex flex-col justify-stretch gap-6">
                    <div class="flex gap-2 text-[#259DF4]">
                        <div class="w-8">
                            <IconLogo />
                        </div>
                        <p class="font-bold text-[24px]">
                            Central Link
                        </p>
                    </div>
                    <div>
                        <p class="text-white text-[48px] font-bold">
                            Next-Gen <span class="text-[#259DF4]">IoT & AI</span> Monitoring Dashboard
                        </p>
                    </div>
                    <div>
                        <p class="text-[18px] text-[#94A3B8]">
                            Seamlessly integrate medical devices, monitor patient vitals in real-time, and leverage
                            predictive AI analytics for your healthcare facility.
                        </p>
                    </div>
                    <div class="flex flex-col gap-4">
                        <Feature text="HIPAA Compliant Infrastructure">
                            <IconCompliant />
                        </Feature>
                        <Feature text="Millisecond Data Latency">
                            <IconAction />
                        </Feature>
                        <Feature text="AI-Driven Predictive Alerts">
                            <IconAI />
                        </Feature>
                    </div>
                </div>
            </div>
            <div class="flex flex-col justify-center items-center gap-8">
                <AuthTabs />
            </div>
        </div>
        <div class="text-center mt-14!">
            <p class="text-[#64748B] text-xs">© 2024 Nexus AI Solutions. All rights reserved.</p>
        </div>
    </div>
</template>