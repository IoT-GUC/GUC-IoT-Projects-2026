<script setup lang="ts">
import Nav from '../nav/Nav.vue';

</script>

<template>
    <div class="flex">
        <Nav />
        <div class="grow">
            <slot />
        </div>
    </div>
</template>