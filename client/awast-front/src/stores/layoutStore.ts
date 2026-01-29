import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useLayoutStore = defineStore('layout', () => {
    const rail = ref(false);
    const drawer = ref(true);

    const toggleRail = () => {
        rail.value = !rail.value;
    };

    const toggleDrawer = () => {
        drawer.value = !drawer.value;
    }

    return { rail, drawer, toggleRail, toggleDrawer };
});
