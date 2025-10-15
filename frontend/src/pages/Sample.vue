<template>
    <ion-page>
        <ion-content :fullscreen="true">
            <FormView v-if="formFields.data" doctype="Employee" v-model="employeeAdvance" :isSubmittable="true"
                :fields="formFields.data" :id="props.id" :showAttachmentView="true" @validateForm="validateForm" />
        </ion-content>
    </ion-page>
</template>

<!-- <script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { createResource } from "frappe-ui"
import { ref, watch, inject, computed } from "vue"

import FormView from "@/components/Form/FormView.vue"

import { getCompanyCurrency } from "@/data/currencies"

const employee = inject("$employee")

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

// object to store form data
 const employeeAdvance = ref({
	employee: employee.data.name,
	employee_name: employee.data.employee_name,
	company: employee.data.company,
	department: employee.data.department,
}) 

const companyCurrency = computed(() =>
	getCompanyCurrency(employeeAdvance.value.company)
)

// get form fields


// const employeeCurrency = createResource({
// 	url: "hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment.get_employee_currency",
// 	params: { employee: employee.data.name },
// 	onSuccess(data) {
// 		employeeAdvance.value.currency = data
// 		setExchangeRate()
// 	},
// })

const exchangeRate = createResource({
	url: "erpnext.setup.utils.get_exchange_rate",
	onSuccess(data) {
		employeeAdvance.value.exchange_rate = data
	},
})

const advanceAccount = createResource({
	url: "hrms.api.get_advance_account",
	params: { company: employeeAdvance.value.company },
	onSuccess(data) {
		employeeAdvance.value.advance_account = data
	},
})

// form scripts
watch(
	() => employeeAdvance.value.currency,
	() => setExchangeRate()
)

// helper functions
function getFilteredFields(fields) {
	// reduce noise from the form view by excluding unnecessary fields
	// eg: employee and other details can be fetched from the session user
	const excludeFields = ["naming_series"]
	const extraFields = [
		"employee",
		"employee_name",
		"department",
		"company",
		"more_info_section",
		"pending_amount",
	]

	if (!props.id) excludeFields.push(...extraFields)

	return fields.filter((field) => !excludeFields.includes(field.fieldname))
}

function applyFilters(fields) {
	return fields.map((field) => {
		if (field.fieldname === "advance_account") {
			let currencies = [employeeAdvance.value.currency]
			if (employeeAdvance.value.currency != companyCurrency.value)
				currencies.push(companyCurrency.value)

			field.linkFilters = {
				company: employeeAdvance.value.company,
				is_group: 0,
				root_type: "Asset",
				account_currency: ("in", currencies),
			}
		}

		return field
	})
}

function setExchangeRate() {
	if (!employeeAdvance.value.currency) return
	const exchange_rate_field = formFields.data?.find(
		(field) => field.fieldname === "exchange_rate"
	)

	if (employeeAdvance.value.currency === companyCurrency.value) {
		employeeAdvance.value.exchange_rate = 1
		exchange_rate_field.hidden = 1
	} else {
		exchangeRate.fetch({
			from_currency: employeeAdvance.value.currency,
			to_currency: companyCurrency.value,
		})
		exchange_rate_field.hidden = 0
	}
}

function validateForm() {}

</script> -->



<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { createResource } from "frappe-ui"
import { ref, watch, inject, computed } from "vue"

import FormView from "@/components/Form/FormView.vue"
const employee = inject("$employee")


const props = defineProps({
    id: {
        type: String,
        required: false,
    },
})


console.log(employee.data,'employee')
const employeeAdvance = ref({

    
    employee: employee.data.name,
    employee_name: employee.data.employee_name,
    company: employee.data.company,
    department: employee.data.department,
})


const formFields = createResource({
    url: "khanal_tech_integrations.api.employee.get_doctype_fields",
    params: { doctype: "Employee" },
    transform(data) {
        const fields = getFilteredFields(data)
        return applyFilters(fields)

        // console.log(fields, '\n\n\n', 'fields')
        // return fields
    },
    onSuccess(_) {
        // employeeCurrency.reload()
        // advanceAccount.reload()
    },
})

formFields.reload()

function applyFilters(fields) {
    return fields.map((field) => {
        field.linkFilters = {
                company: employeeAdvance.value.company,
                is_group: 0,
                root_type: "Asset",
                account_currency: ("in", currencies),
            }

        return field
    })
}

function getFilteredFields(fields) {
    console.log(fields, '\n\n\n', 'fields')
    // reduce noise from the form view by excluding unnecessary fields
    // eg: employee and other details can be fetched from the session user
    const excludeFields = ["naming_series"]
    const extraFields = [
        "employee",
        "employee_name",
        "department",
        "company",
        "more_info_section",
        "pending_amount",
    ]

    if (!props.id) excludeFields.push(...extraFields)

    return fields.filter((field) => !excludeFields.includes(field.fieldname))
}



function validateForm() { }
</script>



<!-- <template>
    <LayoutHeader>
        <template #left-header>
            <Breadcrumbs :items="breadcrumbs" />
        </template>
        <template #right-header>
            <CustomActions />
            <component>
                <MultipleAvatar />
            </component>
            <Dropdown>
                <template #default="{ open }">
                    <Button>
                        <template #prefix>
                            <IndicatorIcon />
                        </template>
                        <template #suffix>
                            <FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="h-4" />
                        </template>
                    </Button>
                </template>
            </Dropdown>
            <Button :label="__('Convert to Deal')" variant="solid" @click="showConvertToDealModal = true" />
        </template>
    </LayoutHeader>
    <div v-if="lead?.data" class="flex h-full overflow-hidden">
        <Tabs v-model="tabIndex" v-slot="{ tab }" :tabs="tabs">
     
        </Tabs>
        <Resizer class="flex flex-col justify-between border-l" side="right">
            <div class="flex h-10.5 cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium">
                {{ __(shahil) }}
            </div>


        </Resizer>
    </div>
   
   
</template>
<script setup>
import Resizer from '@/components/Resizer.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignmentModal from '@/components/Modals/AssignmentModal.vue'
import SidePanelModal from '@/components/Settings/SidePanelModal.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import Section from '@/components/Section.vue'
import SectionFields from '@/components/SectionFields.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import {
    openWebsite,
    createToast,
    setupAssignees,
    setupCustomActions,
    errorMessage,
    copyToClipboard,
} from '@/utils'
import { globalStore } from '@/stores/global'
import { contactsStore } from '@/stores/contacts'
import { organizationsStore } from '@/stores/organizations'
import { statusesStore } from '@/stores/statuses'
import { usersStore } from '@/stores/users'
import { whatsappEnabled, callEnabled } from '@/composables/settings'
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
} from 'frappe-ui'
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const { $dialog, makeCall } = globalStore()
const { getContactByName, contacts } = contactsStore()
const { organizations } = organizationsStore()
const { statusOptions, getLeadStatus } = statusesStore()
const { isManager } = usersStore()
const route = useRoute()
const router = useRouter()

const props = defineProps({
    leadId: {
        type: String,
        required: true,
    },
})
console.log('CRM-LEAD-2024-00002')
//   alert('CRM-LEAD-2024-00002')
const lead = createResource({
    url: 'khanal_tech_integrations.api.fcrm.get_lead',

    params: { name: 'CRM-LEAD-2024-00002' },
    cache: ['lead', 'CRM-LEAD-2024-00002'],
    onSuccess: (data) => {
        setupAssignees(data)
        setupCustomActions(data, {
            doc: data,
            $dialog,
            router,
            updateField,
            createToast,
            deleteDoc: deleteLead,
            call,
        })
    },
})

onMounted(() => {
    if (lead.data) return
    lead.fetch()
})

const reload = ref(false)
const showAssignmentModal = ref(false)
const showSidePanelModal = ref(false)

function updateLead(fieldname, value, callback) {
    value = Array.isArray(fieldname) ? '' : value

    if (!Array.isArray(fieldname) && validateRequired(fieldname, value)) return

    createResource({
        url: 'frappe.client.set_value',
        params: {
            doctype: 'CRM Lead',
            name: 'CRM-LEAD-2024-00002',
            fieldname,
            value,
        },
        auto: true,
        onSuccess: () => {
            lead.reload()
            reload.value = true
            createToast({
                title: __('Lead updated'),
                icon: 'check',
                iconClasses: 'text-green-600',
            })
            callback?.()
        },
        onError: (err) => {
            createToast({
                title: __('Error updating lead'),
                text: __(err.messages?.[0]),
                icon: 'x',
                iconClasses: 'text-red-600',
            })
        },
    })
}

function validateRequired(fieldname, value) {
    let meta = lead.data.fields_meta || {}
    if (meta[fieldname]?.reqd && !value) {
        createToast({
            title: __('Error Updating Lead'),
            text: __('{0} is a required field', [meta[fieldname].label]),
            icon: 'x',
            iconClasses: 'text-red-600',
        })
        return true
    }
    return false
}

const breadcrumbs = computed(() => {
    let items = [{ label: __('Leads'), route: { name: 'Leads' } }]
    items.push({
        label: lead.data.lead_name || __('Untitled'),
        route: { name: 'Lead', params: { leadId: lead.data.name } },
    })
    return items
})

const tabIndex = ref(0)

const tabs = computed(() => {
    let tabOptions = [
        {
            name: 'Activity',
            label: __('Activity'),
            icon: ActivityIcon,
        },
        {
            name: 'Emails',
            label: __('Emails'),
            icon: EmailIcon,
        },
        {
            name: 'Comments',
            label: __('Comments'),
            icon: CommentIcon,
        },
        {
            name: 'Calls',
            label: __('Calls'),
            icon: PhoneIcon,
            condition: () => callEnabled.value,
        },
        {
            name: 'Tasks',
            label: __('Tasks'),
            icon: TaskIcon,
        },
        {
            name: 'Notes',
            label: __('Notes'),
            icon: NoteIcon,
        },
        {
            name: 'WhatsApp',
            label: __('WhatsApp'),
            icon: WhatsAppIcon,
            condition: () => whatsappEnabled.value,
        },
    ]
    return tabOptions.filter((tab) => (tab.condition ? tab.condition() : true))
})

watch(tabs, (value) => {
    if (value && route.params.tabName) {
        let index = value.findIndex(
            (tab) => tab.name.toLowerCase() === route.params.tabName.toLowerCase(),
        )
        if (index !== -1) {
            tabIndex.value = index
        }
    }
})

function validateFile(file) {
    let extn = file.name.split('.').pop().toLowerCase()
    if (!['png', 'jpg', 'jpeg'].includes(extn)) {
        return __('Only PNG and JPG images are allowed')
    }
}

const fieldsLayout = createResource({
    url: 'khanal_tech_integrations.api.doc.get_sidebar_fields',
    cache: ['fieldsLayout', 'CRM-LEAD-2024-00002'],
    params: { doctype: 'CRM Lead', name: 'CRM-LEAD-2024-00002' },
    auto: true,
})

function updateField(name, value, callback) {
    updateLead(name, value, () => {
        lead.data[name] = value
        callback?.()
    })
}

async function deleteLead(name) {
    await call('frappe.client.delete', {
        doctype: 'CRM Lead',
        name,
    })
    router.push({ name: 'Leads' })
}

// Convert to Deal
const showConvertToDealModal = ref(false)
const existingContactChecked = ref(false)
const existingOrganizationChecked = ref(false)

const existingContact = ref('')
const existingOrganization = ref('')

async function convertToDeal(updated) {
    let valueUpdated = false

    if (existingContactChecked.value && !existingContact.value) {
        createToast({
            title: __('Error'),
            text: __('Please select an existing contact'),
            icon: 'x',
            iconClasses: 'text-red-600',
        })
        return
    }

    if (existingOrganizationChecked.value && !existingOrganization.value) {
        createToast({
            title: __('Error'),
            text: __('Please select an existing organization'),
            icon: 'x',
            iconClasses: 'text-red-600',
        })
        return
    }

    if (existingContactChecked.value && existingContact.value) {
        lead.data.salutation = getContactByName(existingContact.value).salutation
        lead.data.first_name = getContactByName(existingContact.value).first_name
        lead.data.last_name = getContactByName(existingContact.value).last_name
        lead.data.email_id = getContactByName(existingContact.value).email_id
        lead.data.mobile_no = getContactByName(existingContact.value).mobile_no
        existingContactChecked.value = false
        valueUpdated = true
    }

    if (existingOrganizationChecked.value && existingOrganization.value) {
        lead.data.organization = existingOrganization.value
        existingOrganizationChecked.value = false
        valueUpdated = true
    }

    if (valueUpdated) {
        updateLead(
            {
                salutation: lead.data.salutation,
                first_name: lead.data.first_name,
                last_name: lead.data.last_name,
                email_id: lead.data.email_id,
                mobile_no: lead.data.mobile_no,
                organization: lead.data.organization,
            },
            '',
            () => convertToDeal(true),
        )
        showConvertToDealModal.value = false
    } else {
        let deal = await call(
            'crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal',
            {
                lead: lead.data.name,
            },
        )
        if (deal) {
            if (updated) {
                await organizations.reload()
                await contacts.reload()
            }
            router.push({ name: 'Deal', params: { dealId: deal } })
        }
    }
}

const activities = ref(null)

function openEmailBox() {
    activities.value.emailBox.show = true
}
</script> -->