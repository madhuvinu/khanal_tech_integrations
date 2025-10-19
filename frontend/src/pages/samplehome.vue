<template>
    <LayoutHeader>
        <template #left-header>
            <Breadcrumbs :items="breadcrumbs" />
        </template>

        <template #right-header>

        </template>

    </LayoutHeader>
    <HomeViewContols v-model="notes" v-model:loadMore="loadMore" v-model:updatedPageCount="updatedPageCount"
        doctype="Inside Doc" :options="{
            hideColumnsButton: true,
            defaultViewName: __('Dashboard View'),
        }" />
    <div class="flex-1 overflow-y-auto">
        <div class="grid  grid-rows-3 px-5 pb-3">
        <div v-if="notes.data?.data?.length"
            class="grid grid-cols-1 gap-2 px-3 pb-2 sm:grid-cols-3 sm:gap-4 sm:px-5 sm:pb-3">
            <div v-for="note in notes.data.data"
                class="group col-span-1 flex h-56 cursor-pointer flex-col justify-between gap-2 rounded-lg border px-5 py-4 shadow-sm hover:bg-gray-50">
                <div class="flex items-center justify-between">
                    <div class="truncate text-lg font-medium">
                        {{ note.title }}

                    </div>
                    <div>
                        {{ note.sub_title }}
                    </div>

                </div>
                <TextEditor v-if="note.content" :content="note.content" :editable="false"
                    editor-class="!prose-sm max-w-none !text-sm text-gray-600 focus:outline-none"
                    class="flex-1 overflow-hidden" />
                <div class="mt-2 flex items-center justify-between gap-2">
                    <div class="flex items-center gap-2">
                        <UserAvatar :user="note.owner" size="xs" />
                        <div class="text-sm text-gray-800">
                            {{ getUser(note.owner).full_name }}
                        </div>
                    </div>
                    <Tooltip :text="dateFormat(note.modified, dateTooltipFormat)">
                        <div class="text-sm text-gray-700">
                            {{ __(timeAgo(note.modified)) }}
                        </div>
                    </Tooltip>
                </div>
            </div>
        </div>
        <div v-if="notes.data?.data?.length"
            class="grid grid-cols-1 gap-2 sm:grid-cols-1 sm:gap- sm:px-5 sm:pb-3">
           <div class="col-span-1">Hi</div>
        </div>
    </div>
    
    </div>

    <ListFooter v-if="notes.data?.data?.length" class="border-t px-3 py-2 sm:px-5" v-model="notes.data.page_length_count"
        :options="{
            rowCount: notes.data.row_count,
            totalCount: notes.data.total_count,
        }" @loadMore="() => loadMore++" />
    <div v-else class="flex h-full items-center justify-center">
        <div class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500">
            <NoteIcon class="h-10 w-10" />
            <span>{{ __('No {0} Found', [__('Dashboard')]) }}</span>
            <Button :label="__('Create')" @click="createNote">
                <template #prefix>
                    <FeatherIcon name="plus" class="h-4" />
                </template>
            </Button>
        </div>
    </div>
    <HomeModal v-model="showHomeModal" v-model:reloadNotes="notes" :note="currentNote" />
</template>


<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import HomeViewContols from '@/components/HomeViewContols.vue'
import { usersStore } from '@/stores/users'
import { timeAgo, dateFormat, dateTooltipFormat } from '@/utils'
import {
    TextEditor,
    call,
    Dropdown,
    Tooltip,
    Breadcrumbs,
    ListFooter,
} from 'frappe-ui'
import { ref, watch } from 'vue'

const { getUser } = usersStore()

const breadcrumbs = [{ label: __('Dashboard'), route: { name: 'Dashboard' } }]

//   const showHomeModal = ref(false)
const currentNote = ref(null)

const notes = ref({})
const loadMore = ref(1)
const updatedPageCount = ref(20)

watch(
    () => notes.value?.data?.page_length_count,
    (val, old_value) => {
        if (!val || val === old_value) return
        updatedPageCount.value = val
    }
)

function createNote() {
    currentNote.value = {
        title: '',
        content: '',
    }
    showHomeModal.value = true
}

function editNote(note) {
    currentNote.value = note
    showHomeModal.value = true
}

async function deleteNote(name) {
    await call('frappe.client.delete', {
        doctype: 'Inside Doc',
        name,
    })
    notes.value.reload()
}
</script>
