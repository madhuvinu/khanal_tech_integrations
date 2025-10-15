<template>
    <LayoutHeader>
        <template #left-header>
            <Breadcrumbs :items="breadcrumbs" />
        </template>
        <template #right-header>
            <CustomActions />
            <component :is="lead.data._assignedTo?.length == 1 ? 'Button' : 'div'">
                <MultipleAvatar :avatars="lead.data._assignedTo" @click="showAssignmentModal = true" />
            </component>
            <Dropdown :options="statusOptions('lead', updateField)">
                <template #default="{ open }">
                    <Button :label="lead.data.status" :class="getLeadStatus(lead.data.status).colorClass">
                        <!-- <template #prefix>
                            <IndicatorIcon />
                        </template>
                        <template #suffix>
                            <FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="h-4" />
                        </template> -->
                    </Button>
                </template>
            </Dropdown>
            <Button :label="__('Convert to Deal')" variant="solid" @click="showConvertToDealModal = true" />
        </template>
    </LayoutHeader>
    <div v-if="lead.data" class="flex h-full overflow-hidden">
        <Tabs v-model="tabIndex" :tabs="tabs">
            <template #tab="{ tab, selected }">
                <button
                    class="group flex items-center gap-2 border-b border-transparent py-2.5 text-base text-gray-600 duration-300 ease-in-out hover:border-gray-400 hover:text-gray-900"
                    :class="{ 'text-gray-900': selected }">
                    <component v-if="tab.icon" :is="tab.icon" class="h-5" />
                    {{ __(tab.label) }}
                    <!-- <Badge class="group-hover:bg-gray-900" :class="[selected ? 'bg-gray-900' : 'bg-gray-600']"
                        variant="solid" theme="gray" size="sm">
                        {{ tab.count }}
                    </Badge> -->
                </button>
            </template>
            <!-- Tab Content -->
            <template #default="{ tab }">
                <template v-if="tab.label === 'All'">
                    <div class="grid md:grid-cols-3 grid-cols-2 gap-4 p-4">
                        <Card title="TESTING" class="p-4">
                            TEST CARD
                        </Card>
                        <Card class="p-4">
                            TEST CARD
                        </Card>
                        <Card class="p-4">
                            TEST CARD
                        </Card>
                        <Card class="p-4">
                            TEST CARD
                        </Card>
                        <Card class="p-4">
                            TEST CARD
                        </Card>
                    </div>
                </template>
                <template v-if="tab.label === 'Sales'">
                    <div class="grid md:grid-cols-3 grid-cols-1 gap-4 p-4">
                        <Card class="p-4">
                            TEST CARD
                        </Card>
                        <Card class="p-4">
                            TEST CARD
                        </Card>
                        <Card class="p-4">
                            TEST CARD
                        </Card>
                        <Card class="p-4">
                            TEST CARD
                        </Card>
                        <Card class="p-4">
                            TEST CARD
                        </Card>
                    </div>
                </template>
                <template v-if="tab.label === 'Finance'">
                    <div class="grid md:grid-cols-3 grid-cols-1 gap-4 p-4">
                        <Card  class="p-4">
                            FINANCE CARD
                        </Card>
                        <Card class="p-4">
                            TEST CARD
                        </Card>
                        <Card class="p-4">
                            TEST CARD
                        </Card>
                        <Card class="p-4">
                            TEST CARD
                        </Card>
                        <Card class="p-4">
                            TEST CARD
                        </Card>
                    </div>
                </template>

            </template>
        </Tabs>
        <Resizer class="flex flex-col justify-between border-l" side="right">
            <div class="flex h-10.5 cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium">

            </div>
        </Resizer>
    </div>
</template>

<script setup>
import Resizer from '@/components/Resizer.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import CustomActions from '@/components/CustomActions.vue'
import { statusesStore } from '@/stores/statuses'


// import Dropdown from 'frappe-ui/Dropdown'
import {
    createResource,
    FileUploader,
    Dropdown,
    Tooltip,
    Avatar,
    Tabs,
    Switch,
    Breadcrumbs,
    call,
    Card,
} from 'frappe-ui'
import { ref, computed } from 'vue'

const { statusOptions, getLeadStatus } = statusesStore()

const showConvertToDealModal = ref(false)

const lead = {
    data: {
        name: 'CRM-LEAD-2024-00002',
        lead_name: 'Static Lead',
    }
}

const breadcrumbs = computed(() => {
    return [
        { label: 'Leads', route: { name: 'Leads' } },
        { label: lead.data.lead_name, route: { name: 'Lead', params: { leadId: lead.data.name } } }
    ]
})

const tabIndex = ref(0)

const tabs = [
    { name: 'All', label: 'All', icon: ActivityIcon },
    { name: 'Sales', label: 'Sales', icon: EmailIcon },
    { name: 'Finance', label: 'Finance', icon: CommentIcon },
    { name: 'Inventory', label: 'Inventory', icon: PhoneIcon },
    { name: 'Hr', label: 'Hr', icon: TaskIcon },
    { name: 'Procurement', label: 'Procurement', icon: NoteIcon },
    { name: 'Production', label: 'Production', icon: WhatsAppIcon },
]

// TODO: Replace with actual data & make it dynamic
const shortCuts = [
    { name: 'Shortcut1', label: 'Shortcut1', link:'http://', category:'Sales' },
    { name: 'Sales', label: 'Sales', icon: EmailIcon },
    { name: 'Finance', label: 'Finance', icon: CommentIcon },
    { name: 'Inventory', label: 'Inventory', icon: PhoneIcon },
    { name: 'Hr', label: 'Hr', icon: TaskIcon },
    { name: 'Procurement', label: 'Procurement', icon: NoteIcon },
    { name: 'Production', label: 'Production', icon: WhatsAppIcon },
]
</script>
